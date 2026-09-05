package com.aaris.voiceludomasti

import android.app.ActivityManager
import android.content.Context
import android.os.Handler
import android.os.Looper
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.Executors
import java.util.zip.ZipInputStream

class MainActivity : FlutterActivity() {
    private val modelExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            MODEL_CHANNEL,
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "prepareOfflineVoskModel" -> {
                    modelExecutor.execute {
                        try {
                            // Vosk's mobile model is small on disk but expands into a much
                            // larger native-memory working set. A native std::bad_alloc is a
                            // process-level SIGABRT and cannot be caught by Dart, so reject an
                            // unsafe load before Vosk receives the model path. The game then
                            // falls back to normal random dice instead of crashing.
                            ensureVoiceMemoryHeadroom()
                            val modelPath = prepareOfflineVoskModel()
                            mainHandler.post { result.success(modelPath.absolutePath) }
                        } catch (error: Throwable) {
                            mainHandler.post {
                                result.error(
                                    "MODEL_PREPARE_FAILED",
                                    error.message ?: "Offline model preparation failed",
                                    null,
                                )
                            }
                        }
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun ensureVoiceMemoryHeadroom() {
        val activityManager =
            getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)

        val availableMb = memoryInfo.availMem / BYTES_PER_MB
        val totalMb = memoryInfo.totalMem / BYTES_PER_MB
        val unsafeReason = when {
            activityManager.isLowRamDevice ->
                "Android reports this as a low-RAM device. Offline voice was disabled to protect the game."
            memoryInfo.lowMemory ->
                "Android is currently under low-memory pressure. Offline voice was disabled to protect the game."
            totalMb < MIN_DEVICE_MEMORY_MB ->
                "This device does not have enough total RAM for the offline Hindi voice model."
            availableMb < MIN_VOSK_HEADROOM_MB ->
                "Not enough free RAM to safely load the offline Hindi voice model ($availableMb MB free)."
            else -> null
        }

        if (unsafeReason != null) {
            throw IllegalStateException(unsafeReason)
        }
    }

    private fun prepareOfflineVoskModel(): File {
        val modelsDir = File(filesDir, "vosk_models")
        val finalModelDir = File(modelsDir, MODEL_NAME)
        if (isUsableModel(finalModelDir)) return finalModelDir

        // A previous interrupted extraction may have left a directory that has
        // only final.mdl/model.conf. Vosk can abort the whole Android process on
        // structurally incomplete Kaldi data, so never reuse a partially valid
        // folder and never validate by only one or two files.
        if (finalModelDir.exists() && !finalModelDir.deleteRecursively()) {
            throw IllegalStateException("Could not remove an incomplete offline voice model")
        }

        if (!modelsDir.exists() && !modelsDir.mkdirs()) {
            throw IllegalStateException("Could not create the offline model directory")
        }
        if (modelsDir.usableSpace < MIN_MODEL_INSTALL_FREE_BYTES) {
            throw IllegalStateException("Not enough free storage to safely prepare the offline voice model")
        }

        val stagingDir = File(modelsDir, ".staging-${System.nanoTime()}")
        if (stagingDir.exists() && !stagingDir.deleteRecursively()) {
            throw IllegalStateException("Could not clear a stale offline-model staging directory")
        }
        if (!stagingDir.mkdirs()) {
            throw IllegalStateException("Could not create the offline-model staging directory")
        }

        try {
            var extractedBytes = 0L
            assets.open(MODEL_ANDROID_ASSET).use { assetStream ->
                ZipInputStream(assetStream.buffered()).use { zip ->
                    val buffer = ByteArray(64 * 1024)
                    var entry = zip.nextEntry
                    while (entry != null) {
                        val output = safeZipDestination(stagingDir, entry.name)
                        if (entry.isDirectory) {
                            if (!output.exists() && !output.mkdirs()) {
                                throw IllegalStateException("Could not create model directory: ${entry.name}")
                            }
                        } else {
                            val parent = output.parentFile
                            if (parent != null && !parent.exists() && !parent.mkdirs()) {
                                throw IllegalStateException("Could not create model parent directory")
                            }
                            FileOutputStream(output).buffered().use { fileOut ->
                                while (true) {
                                    val count = zip.read(buffer)
                                    if (count <= 0) break
                                    extractedBytes += count
                                    if (extractedBytes > MAX_EXTRACTED_MODEL_BYTES) {
                                        throw IllegalStateException("Offline model archive expanded beyond its safety limit")
                                    }
                                    fileOut.write(buffer, 0, count)
                                }
                            }
                        }
                        zip.closeEntry()
                        entry = zip.nextEntry
                    }
                }
            }

            val extractedModel = File(stagingDir, MODEL_NAME)
            if (!isUsableModel(extractedModel)) {
                throw IllegalStateException("Extracted Vosk model is incomplete or corrupt")
            }

            if (finalModelDir.exists() && !finalModelDir.deleteRecursively()) {
                throw IllegalStateException("Could not replace previous offline model")
            }

            if (!extractedModel.renameTo(finalModelDir)) {
                val copied = extractedModel.copyRecursively(finalModelDir, overwrite = true)
                if (!copied) {
                    throw IllegalStateException("Could not install extracted offline model")
                }
            }

            if (!isUsableModel(finalModelDir)) {
                finalModelDir.deleteRecursively()
                throw IllegalStateException("Offline Vosk model failed final verification")
            }
            return finalModelDir
        } finally {
            stagingDir.deleteRecursively()
        }
    }

    private fun isUsableModel(modelDir: File): Boolean {
        if (!modelDir.isDirectory) return false

        for (relativePath in REQUIRED_MODEL_FILES) {
            val file = File(modelDir, relativePath)
            if (!file.isFile || file.length() <= 0L) return false
        }

        var totalBytes = 0L
        modelDir.walkTopDown().forEach { file ->
            if (file.isFile) totalBytes += file.length()
        }
        return totalBytes >= MIN_EXTRACTED_MODEL_BYTES
    }

    private fun safeZipDestination(root: File, entryName: String): File {
        if (entryName.isBlank()) {
            throw SecurityException("Blocked empty ZIP entry")
        }
        val destination = File(root, entryName)
        val rootPath = root.canonicalPath + File.separator
        val destinationPath = destination.canonicalPath
        if (!destinationPath.startsWith(rootPath)) {
            throw SecurityException("Blocked unsafe ZIP entry: $entryName")
        }
        return destination
    }

    override fun onDestroy() {
        modelExecutor.shutdownNow()
        super.onDestroy()
    }

    companion object {
        private const val MODEL_CHANNEL = "voice_ludo/native_model"
        private const val MODEL_NAME = "vosk-model-small-hi-0.22"
        private const val MODEL_ANDROID_ASSET = "vosk-model-small-hi-0.22.zip"

        private const val BYTES_PER_MB = 1024L * 1024L
        private const val MIN_DEVICE_MEMORY_MB = 2048L
        private const val MIN_VOSK_HEADROOM_MB = 640L
        private const val MIN_MODEL_INSTALL_FREE_BYTES = 180L * BYTES_PER_MB
        private const val MIN_EXTRACTED_MODEL_BYTES = 30L * BYTES_PER_MB
        private const val MAX_EXTRACTED_MODEL_BYTES = 256L * BYTES_PER_MB

        // Exact critical structure for vosk-model-small-hi-0.22. Checking this
        // whole set prevents an interrupted/legacy partial extraction from being
        // handed to Kaldi/Vosk, where malformed model data can terminate the
        // process with SIGABRT rather than a recoverable Java/Dart exception.
        private val REQUIRED_MODEL_FILES = arrayOf(
            "am/final.mdl",
            "conf/mfcc.conf",
            "conf/model.conf",
            "graph/Gr.fst",
            "graph/HCLr.fst",
            "graph/disambig_tid.int",
            "graph/phones/word_boundary.int",
            "ivector/final.dubm",
            "ivector/final.ie",
            "ivector/final.mat",
            "ivector/global_cmvn.stats",
            "ivector/online_cmvn.conf",
            "ivector/splice.conf",
        )
    }
}
