package com.aaris.voiceludomasti

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

    private fun prepareOfflineVoskModel(): File {
        val modelsDir = File(filesDir, "vosk_models")
        val finalModelDir = File(modelsDir, MODEL_NAME)
        if (isUsableModel(finalModelDir)) return finalModelDir

        modelsDir.mkdirs()
        val stagingDir = File(modelsDir, ".staging-${System.nanoTime()}")
        if (stagingDir.exists()) stagingDir.deleteRecursively()
        stagingDir.mkdirs()

        try {
            assets.open(MODEL_ANDROID_ASSET).use { assetStream ->
                ZipInputStream(assetStream.buffered()).use { zip ->
                    val buffer = ByteArray(64 * 1024)
                    var entry = zip.nextEntry
                    while (entry != null) {
                        val output = safeZipDestination(stagingDir, entry.name)
                        if (entry.isDirectory) {
                            output.mkdirs()
                        } else {
                            output.parentFile?.mkdirs()
                            FileOutputStream(output).buffered().use { fileOut ->
                                while (true) {
                                    val count = zip.read(buffer)
                                    if (count <= 0) break
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
                throw IllegalStateException("Extracted Vosk model is incomplete")
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
                throw IllegalStateException("Offline Vosk model failed final verification")
            }
            return finalModelDir
        } finally {
            stagingDir.deleteRecursively()
        }
    }

    private fun isUsableModel(modelDir: File): Boolean =
        File(modelDir, "am/final.mdl").isFile &&
            File(modelDir, "conf/model.conf").isFile

    private fun safeZipDestination(root: File, entryName: String): File {
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
    }
}
