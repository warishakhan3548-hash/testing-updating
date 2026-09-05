package com.aaris.voiceludomasti

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel
import java.util.ArrayList
import kotlin.math.max

class MainActivity : FlutterActivity() {
    private data class VoiceBinding(
        val matchId: String,
        val playerId: String,
        val turnId: Long,
    )

    private val mainHandler = Handler(Looper.getMainLooper())

    private var recognizer: SpeechRecognizer? = null
    private var eventSink: EventChannel.EventSink? = null

    private var voiceEnabled = false
    private var pausedByFlutter = false
    private var activityResumed = false
    private var sessionActive = false

    private var pendingStartAfterPermission = false
    private var permissionRequestInFlight = false

    private var currentBinding: VoiceBinding? = null
    private var recognitionBinding: VoiceBinding? = null

    // Epoch changes whenever the recognizer object is destroyed/recreated. A
    // turn/context change always rotates the epoch so callbacks from a canceled
    // old turn cannot ever be emitted under the next turn's binding.
    private var recognizerEpoch = 0L

    // A recognizer object can safely serve several natural same-turn sessions.
    // Session ids let Dart deduplicate partial/final callbacks from one utterance
    // without applying a global time debounce that could block the next turn.
    private var sessionSerial = 0L
    private var activeSessionId = 0L

    private var restartAttempt = 0
    private var consecutiveNoMatch = 0
    private var usingOnDeviceRecognizer = false
    private var onDeviceRejectedForProcess = false

    private var readyWatchdog: Runnable? = null
    private var sessionWatchdog: Runnable? = null
    private var resultWatchdog: Runnable? = null

    private val restartRunnable = Runnable {
        if (shouldListen()) startSession()
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        EventChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            VOICE_EVENT_CHANNEL,
        ).setStreamHandler(object : EventChannel.StreamHandler {
            override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                eventSink = events
                emitAvailability()
                emitListening(sessionActive)
                emit(mapOf("type" to "lifecycle", "active" to activityResumed))
            }

            override fun onCancel(arguments: Any?) {
                eventSink = null
            }
        })

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            VOICE_METHOD_CHANNEL,
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "isAvailable" -> {
                    val available = isAnyRecognitionAvailable()
                    result.success(available)
                    if (available && hasMicrophonePermission() && activityResumed) {
                        // Pre-create the recognizer object so the first playable
                        // turn does not pay avoidable object-creation latency.
                        mainHandler.post { ensureRecognizer() }
                    }
                }

                "startListening" -> {
                    val binding = bindingFrom(call.arguments)
                    if (binding == null) {
                        result.error("invalid_context", "A match/turn voice context is required.", null)
                        return@setMethodCallHandler
                    }

                    val changed = currentBinding != null && currentBinding != binding
                    currentBinding = binding
                    voiceEnabled = true
                    pausedByFlutter = false

                    if (changed) {
                        restartForContextChange()
                    } else {
                        ensurePermissionAndStart()
                    }
                    result.success(null)
                }

                "updateContext" -> {
                    val binding = bindingFrom(call.arguments)
                    if (binding == null) {
                        result.error("invalid_context", "A match/turn voice context is required.", null)
                        return@setMethodCallHandler
                    }

                    val changed = currentBinding != binding
                    currentBinding = binding
                    if (changed && voiceEnabled && !pausedByFlutter) {
                        restartForContextChange()
                    }
                    result.success(null)
                }

                "pauseListening" -> {
                    pausedByFlutter = true
                    pauseCurrentSession()
                    result.success(null)
                }

                "stopListening" -> {
                    voiceEnabled = false
                    pausedByFlutter = false
                    pendingStartAfterPermission = false
                    currentBinding = null
                    pauseCurrentSession()
                    result.success(null)
                }

                else -> result.notImplemented()
            }
        }
    }

    private fun bindingFrom(arguments: Any?): VoiceBinding? {
        val map = arguments as? Map<*, *> ?: return null
        val matchId = map["matchId"] as? String ?: return null
        val playerId = map["playerId"] as? String ?: return null
        val turnId = (map["turnId"] as? Number)?.toLong() ?: return null
        if (matchId.isBlank() || playerId.isBlank() || turnId <= 0L) return null
        return VoiceBinding(matchId, playerId, turnId)
    }

    private fun shouldListen(): Boolean =
        voiceEnabled && !pausedByFlutter && activityResumed && currentBinding != null

    private fun isOnDeviceRecognitionUsable(): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            !onDeviceRejectedForProcess &&
            SpeechRecognizer.isOnDeviceRecognitionAvailable(this)

    private fun isAnyRecognitionAvailable(): Boolean =
        SpeechRecognizer.isRecognitionAvailable(this) || isOnDeviceRecognitionUsable()

    private fun hasMicrophonePermission(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.M ||
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED

    private fun ensurePermissionAndStart() {
        if (!shouldListen()) return

        if (!isAnyRecognitionAvailable()) {
            voiceEnabled = false
            emit(
                mapOf(
                    "type" to "unavailable",
                    "message" to "Android speech recognition is unavailable on this device.",
                ),
            )
            return
        }

        if (hasMicrophonePermission()) {
            pendingStartAfterPermission = false
            startSession()
            return
        }

        pendingStartAfterPermission = true
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !permissionRequestInFlight) {
            permissionRequestInFlight = true
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_AUDIO_PERMISSION)
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != REQUEST_AUDIO_PERMISSION) return

        permissionRequestInFlight = false
        val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
        emit(mapOf("type" to "permission", "granted" to granted))

        if (!granted) {
            voiceEnabled = false
            pendingStartAfterPermission = false
            destroyRecognizer()
            return
        }

        if (pendingStartAfterPermission && shouldListen()) {
            pendingStartAfterPermission = false
            startSession()
        }
    }

    /**
     * Accuracy-first backend selection. The regular system recognizer is used
     * first because Google/OEM speech services commonly have the strongest
     * short Hindi/Hinglish acoustic model. The on-device recognizer is a safe
     * fallback when the system recognizer cannot be created.
     */
    private fun ensureRecognizer(): SpeechRecognizer? {
        recognizer?.let { return it }

        val created =
            if (SpeechRecognizer.isRecognitionAvailable(this)) {
                try {
                    usingOnDeviceRecognizer = false
                    SpeechRecognizer.createSpeechRecognizer(this)
                } catch (systemError: Throwable) {
                    createOnDeviceFallback(systemError)
                }
            } else {
                createOnDeviceFallback(null)
            } ?: return null

        recognizer = created
        recognizerEpoch += 1L
        created.setRecognitionListener(createRecognitionListener(recognizerEpoch))
        return created
    }

    private fun createOnDeviceFallback(systemError: Throwable?): SpeechRecognizer? {
        if (!isOnDeviceRecognitionUsable()) {
            emitRecognizerCreationFailure(systemError ?: IllegalStateException("No speech recognizer available."))
            return null
        }

        return try {
            usingOnDeviceRecognizer = true
            SpeechRecognizer.createOnDeviceSpeechRecognizer(this)
        } catch (error: Throwable) {
            onDeviceRejectedForProcess = true
            usingOnDeviceRecognizer = false
            emitRecognizerCreationFailure(error)
            null
        }
    }

    private fun emitRecognizerCreationFailure(error: Throwable) {
        sessionActive = false
        voiceEnabled = false
        recognitionBinding = null
        activeSessionId = 0L
        cancelVoiceWatchdogs()
        emitListening(false)
        emit(
            mapOf(
                "type" to "unavailable",
                "message" to (error.message ?: "Could not create Android speech recognizer."),
            ),
        )
    }

    private fun createRecognitionListener(epoch: Long): RecognitionListener =
        object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                if (!isCurrentEpoch(epoch) || !sessionActive) return
                cancelReadyWatchdog()
                restartAttempt = 0
                armSessionWatchdog(epoch, SESSION_IDLE_WATCHDOG_MS)
                emitListening(true)
            }

            override fun onBeginningOfSpeech() {
                if (!isCurrentEpoch(epoch) || !sessionActive) return
                cancelReadyWatchdog()
                armSessionWatchdog(epoch, SPEECH_WATCHDOG_MS)
            }

            // RMS updates are intentionally ignored. They are high-frequency UI
            // thread callbacks and the Flutter UI does not render an audio meter.
            // Avoiding channel traffic here keeps board/animation frames isolated.
            override fun onRmsChanged(rmsdB: Float) = Unit

            override fun onBufferReceived(buffer: ByteArray?) = Unit

            override fun onEndOfSpeech() {
                if (!isCurrentEpoch(epoch) || !sessionActive) return
                cancelSessionWatchdog()
                armResultWatchdog(epoch)
                emitListening(false)
            }

            override fun onError(error: Int) {
                if (!isCurrentEpoch(epoch)) return
                cancelVoiceWatchdogs()
                sessionActive = false
                recognitionBinding = null
                activeSessionId = 0L
                emitListening(false)

                if (error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS) {
                    voiceEnabled = false
                    emit(mapOf("type" to "permission", "granted" to false))
                    destroyRecognizer()
                    return
                }

                if (isLanguageAvailabilityError(error) && usingOnDeviceRecognizer) {
                    fallBackFromOnDeviceRecognizer()
                    return
                }

                if (isLanguageAvailabilityError(error)) {
                    voiceEnabled = false
                    emit(
                        mapOf(
                            "type" to "error",
                            "code" to error,
                            "recoverable" to false,
                            "message" to recognitionErrorMessage(error),
                        ),
                    )
                    destroyRecognizer()
                    return
                }

                if (!shouldListen()) return

                if (error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) {
                    consecutiveNoMatch += 1
                    if (
                        usingOnDeviceRecognizer &&
                        consecutiveNoMatch >= ON_DEVICE_NO_MATCH_FALLBACK_THRESHOLD &&
                        SpeechRecognizer.isRecognitionAvailable(this@MainActivity)
                    ) {
                        onDeviceRejectedForProcess = true
                        destroyRecognizer()
                        emit(
                            mapOf(
                                "type" to "error",
                                "recoverable" to true,
                                "message" to "Switching to system speech recognition.",
                            ),
                        )
                        scheduleRestart(SYSTEM_FALLBACK_RESTART_MS)
                        return
                    }
                }

                if (error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY || error == SpeechRecognizer.ERROR_CLIENT) {
                    destroyRecognizer()
                }

                emit(
                    mapOf(
                        "type" to "error",
                        "code" to error,
                        "recoverable" to true,
                        "message" to recognitionErrorMessage(error),
                    ),
                )
                scheduleRestart(restartDelayFor(error))
            }

            override fun onResults(results: Bundle?) {
                if (!isCurrentEpoch(epoch) || !sessionActive) return
                cancelVoiceWatchdogs()
                consecutiveNoMatch = 0

                emitSpeech(results, isFinal = true, epoch = epoch)

                restartAttempt = 0
                sessionActive = false
                recognitionBinding = null
                activeSessionId = 0L
                emitListening(false)
                scheduleRestart(resultRestartDelay())
            }

            override fun onPartialResults(partialResults: Bundle?) {
                if (!isCurrentEpoch(epoch) || !sessionActive) return
                consecutiveNoMatch = 0
                armSessionWatchdog(epoch, SPEECH_WATCHDOG_MS)
                emitSpeech(partialResults, isFinal = false, epoch = epoch)
            }

            override fun onEvent(eventType: Int, params: Bundle?) = Unit
        }

    private fun isCurrentEpoch(epoch: Long): Boolean = epoch == recognizerEpoch && recognizer != null

    private fun isLanguageAvailabilityError(error: Int): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            (error == SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED ||
                error == SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE)

    private fun fallBackFromOnDeviceRecognizer() {
        mainHandler.removeCallbacks(restartRunnable)
        onDeviceRejectedForProcess = true
        consecutiveNoMatch = 0
        destroyRecognizer()

        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            voiceEnabled = false
            emit(
                mapOf(
                    "type" to "unavailable",
                    "message" to "Hindi speech recognition is unavailable on this device.",
                ),
            )
            return
        }

        emit(
            mapOf(
                "type" to "error",
                "recoverable" to true,
                "message" to "Switching to system speech recognition.",
            ),
        )
        scheduleRestart(SYSTEM_FALLBACK_RESTART_MS)
    }

    private fun buildRecognizerIntent(): Intent =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, HINDI_LOCALE)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, MAX_RESULTS)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, packageName)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, usingOnDeviceRecognizer)

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                putStringArrayListExtra(
                    RecognizerIntent.EXTRA_BIASING_STRINGS,
                    ArrayList(DICE_BIASING_STRINGS),
                )
                putExtra(RecognizerIntent.EXTRA_ENABLE_BIASING_DEVICE_CONTEXT, false)
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                putExtra(
                    RecognizerIntent.EXTRA_ENABLE_LANGUAGE_SWITCH,
                    RecognizerIntent.LANGUAGE_SWITCH_QUICK_RESPONSE,
                )
                putStringArrayListExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_SWITCH_ALLOWED_LANGUAGES,
                    ArrayList(VOICE_LOCALES),
                )
                putExtra(RecognizerIntent.EXTRA_ENABLE_LANGUAGE_DETECTION, true)
                putStringArrayListExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_DETECTION_ALLOWED_LANGUAGES,
                    ArrayList(VOICE_LOCALES),
                )
            }

            if (Build.VERSION.SDK_INT >= 35) {
                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_SWITCH_INITIAL_ACTIVE_DURATION_TIME_MILLIS,
                    LANGUAGE_SWITCH_ACTIVE_MS,
                )
                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_SWITCH_MAX_SWITCHES,
                    LANGUAGE_SWITCH_MAX_SWITCHES,
                )
            }

            // These hints are deliberately bounded for a one-word command. OEM
            // recognizers may ignore them, so correctness never depends on them.
            putExtra(
                RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS,
                POSSIBLY_COMPLETE_SILENCE_MS,
            )
            putExtra(
                RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS,
                COMPLETE_SILENCE_MS,
            )
        }

    private fun startSession() {
        if (!shouldListen() || sessionActive) return
        if (!hasMicrophonePermission()) {
            ensurePermissionAndStart()
            return
        }

        val binding = currentBinding ?: return
        val speech = ensureRecognizer() ?: return

        mainHandler.removeCallbacks(restartRunnable)
        cancelVoiceWatchdogs()
        recognitionBinding = binding
        sessionSerial += 1L
        activeSessionId = sessionSerial

        try {
            sessionActive = true
            speech.startListening(buildRecognizerIntent())
            armReadyWatchdog(recognizerEpoch)
        } catch (error: Throwable) {
            sessionActive = false
            recognitionBinding = null
            activeSessionId = 0L
            cancelVoiceWatchdogs()
            emitListening(false)
            emit(
                mapOf(
                    "type" to "error",
                    "recoverable" to true,
                    "message" to (error.message ?: "Could not start Android voice recognition."),
                ),
            )
            destroyRecognizer()
            scheduleRestart(START_FAILURE_RESTART_MS)
        }
    }

    /**
     * A context change means a different roll generation/turn. We deliberately
     * destroy the recognizer object here instead of merely canceling it. That
     * rotates recognizerEpoch synchronously, making every old-turn callback
     * harmless before the new turn can begin listening.
     */
    private fun restartForContextChange() {
        mainHandler.removeCallbacks(restartRunnable)
        cancelVoiceWatchdogs()
        sessionActive = false
        recognitionBinding = null
        activeSessionId = 0L
        emitListening(false)
        destroyRecognizer()
        if (shouldListen()) scheduleRestart(CONTEXT_REARM_MS)
    }

    private fun pauseCurrentSession() {
        mainHandler.removeCallbacks(restartRunnable)
        cancelVoiceWatchdogs()
        sessionActive = false
        recognitionBinding = null
        activeSessionId = 0L
        emitListening(false)
        destroyRecognizer()
    }

    private fun recycleStuckRecognizer(epoch: Long) {
        if (!isCurrentEpoch(epoch)) return
        val restart = shouldListen()
        destroyRecognizer()
        emitListening(false)
        if (restart) {
            emit(
                mapOf(
                    "type" to "error",
                    "recoverable" to true,
                    "message" to "Voice listener recovered automatically.",
                ),
            )
            scheduleRestart(STUCK_RESTART_MS)
        }
    }

    private fun armReadyWatchdog(epoch: Long) {
        cancelReadyWatchdog()
        val task = Runnable {
            if (sessionActive && shouldListen()) recycleStuckRecognizer(epoch)
        }
        readyWatchdog = task
        mainHandler.postDelayed(task, READY_WATCHDOG_MS)
    }

    private fun armSessionWatchdog(epoch: Long, delayMs: Long) {
        cancelSessionWatchdog()
        val task = Runnable {
            if (sessionActive && shouldListen()) recycleStuckRecognizer(epoch)
        }
        sessionWatchdog = task
        mainHandler.postDelayed(task, delayMs)
    }

    private fun armResultWatchdog(epoch: Long) {
        cancelResultWatchdog()
        val task = Runnable {
            if (sessionActive && shouldListen()) recycleStuckRecognizer(epoch)
        }
        resultWatchdog = task
        mainHandler.postDelayed(task, RESULT_WATCHDOG_MS)
    }

    private fun cancelReadyWatchdog() {
        readyWatchdog?.let(mainHandler::removeCallbacks)
        readyWatchdog = null
    }

    private fun cancelSessionWatchdog() {
        sessionWatchdog?.let(mainHandler::removeCallbacks)
        sessionWatchdog = null
    }

    private fun cancelResultWatchdog() {
        resultWatchdog?.let(mainHandler::removeCallbacks)
        resultWatchdog = null
    }

    private fun cancelVoiceWatchdogs() {
        cancelReadyWatchdog()
        cancelSessionWatchdog()
        cancelResultWatchdog()
    }

    private fun destroyRecognizer() {
        cancelVoiceWatchdogs()
        // Invalidate callbacks before cancel/destroy can synchronously or
        // asynchronously deliver anything from the old recognizer.
        recognizerEpoch += 1L
        sessionActive = false
        recognitionBinding = null
        activeSessionId = 0L

        val speech = recognizer
        recognizer = null
        usingOnDeviceRecognizer = false
        if (speech == null) return

        try {
            speech.cancel()
        } catch (_: Throwable) {
        }
        try {
            speech.destroy()
        } catch (_: Throwable) {
        }
    }

    private fun resultRestartDelay(): Long =
        if (usingOnDeviceRecognizer) ON_DEVICE_RESULT_RESTART_MS else SYSTEM_RESULT_RESTART_MS

    private fun restartDelayFor(error: Int): Long {
        if (error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) {
            restartAttempt = 0
            return if (usingOnDeviceRecognizer) ON_DEVICE_NO_MATCH_RESTART_MS else SYSTEM_NO_MATCH_RESTART_MS
        }

        val base = when (error) {
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> 360L
            SpeechRecognizer.ERROR_NETWORK,
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT,
            SpeechRecognizer.ERROR_SERVER,
            -> 700L
            else -> 220L
        }
        val factor = 1L shl restartAttempt.coerceAtMost(3)
        restartAttempt = (restartAttempt + 1).coerceAtMost(4)
        return max(1L, (base * factor).coerceAtMost(4_000L))
    }

    private fun scheduleRestart(delayMs: Long) {
        if (!shouldListen()) return
        mainHandler.removeCallbacks(restartRunnable)
        mainHandler.postDelayed(restartRunnable, delayMs)
    }

    private fun emitSpeech(bundle: Bundle?, isFinal: Boolean, epoch: Long) {
        if (!isCurrentEpoch(epoch) || !sessionActive || !shouldListen()) return

        val binding = recognitionBinding ?: return
        val sessionId = activeSessionId
        if (binding != currentBinding || sessionId <= 0L) return

        val texts = bundle
            ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            ?.asSequence()
            ?.map { it.trim() }
            ?.filter { it.isNotEmpty() }
            ?.distinct()
            ?.take(MAX_RESULTS)
            ?.toList()
            .orEmpty()

        if (texts.isEmpty()) return

        emit(
            mapOf(
                "type" to "speech",
                "final" to isFinal,
                "texts" to texts,
                // Confidence arrays are deliberately omitted. Short/quiet dice
                // commands can receive poor OEM confidence despite a correct
                // lexical hypothesis; the bounded grammar is the primary filter.
                "confidences" to emptyList<Double>(),
                "recognizedAtMs" to System.currentTimeMillis(),
                "recognizerEpoch" to epoch,
                "sessionId" to sessionId,
                "matchId" to binding.matchId,
                "playerId" to binding.playerId,
                "turnId" to binding.turnId,
            ),
        )
    }

    private fun emitAvailability() {
        emit(
            mapOf(
                "type" to "availability",
                "available" to isAnyRecognitionAvailable(),
                "onDevice" to isOnDeviceRecognitionUsable(),
            ),
        )
    }

    private fun emitListening(active: Boolean) {
        emit(mapOf("type" to "listening", "active" to (active && shouldListen())))
    }

    private fun emit(event: Map<String, Any?>) {
        eventSink?.success(event)
    }

    private fun recognitionErrorMessage(error: Int): String =
        when (error) {
            SpeechRecognizer.ERROR_AUDIO -> "Microphone audio error. Retrying…"
            SpeechRecognizer.ERROR_CLIENT -> "Voice recognizer restarted."
            SpeechRecognizer.ERROR_NETWORK -> "Voice network error. Retrying…"
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Voice network timeout. Retrying…"
            SpeechRecognizer.ERROR_NO_MATCH -> "Listening for a dice number…"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Voice recognizer is busy. Retrying…"
            SpeechRecognizer.ERROR_SERVER -> "Voice service error. Retrying…"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Listening for a dice number…"
            SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED -> "Hindi speech recognition is not supported on this device."
            SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE -> "Hindi speech recognition is not currently available on this device."
            else -> "Voice recognizer error $error. Retrying…"
        }

    override fun onResume() {
        super.onResume()
        activityResumed = true
        emit(mapOf("type" to "lifecycle", "active" to true))
        if (shouldListen()) ensurePermissionAndStart()
    }

    override fun onPause() {
        emit(mapOf("type" to "lifecycle", "active" to false))
        activityResumed = false
        pauseCurrentSession()
        super.onPause()
    }

    override fun onDestroy() {
        voiceEnabled = false
        pausedByFlutter = true
        pendingStartAfterPermission = false
        currentBinding = null
        mainHandler.removeCallbacks(restartRunnable)
        destroyRecognizer()
        eventSink = null
        super.onDestroy()
    }

    companion object {
        private const val VOICE_METHOD_CHANNEL = "voice_ludo/speech"
        private const val VOICE_EVENT_CHANNEL = "voice_ludo/speech_events"
        private const val REQUEST_AUDIO_PERMISSION = 7301

        private const val HINDI_LOCALE = "hi-IN"
        private const val MAX_RESULTS = 16
        private const val ON_DEVICE_NO_MATCH_FALLBACK_THRESHOLD = 2

        private const val POSSIBLY_COMPLETE_SILENCE_MS = 260L
        private const val COMPLETE_SILENCE_MS = 650L
        private const val LANGUAGE_SWITCH_ACTIVE_MS = 2_800
        private const val LANGUAGE_SWITCH_MAX_SWITCHES = 3

        private val VOICE_LOCALES = listOf("hi-IN", "en-IN", "en-US")

        private const val ON_DEVICE_RESULT_RESTART_MS = 24L
        private const val SYSTEM_RESULT_RESTART_MS = 55L
        private const val ON_DEVICE_NO_MATCH_RESTART_MS = 35L
        private const val SYSTEM_NO_MATCH_RESTART_MS = 65L
        private const val CONTEXT_REARM_MS = 42L
        private const val SYSTEM_FALLBACK_RESTART_MS = 55L
        private const val STUCK_RESTART_MS = 60L
        private const val START_FAILURE_RESTART_MS = 280L

        private const val READY_WATCHDOG_MS = 2_300L
        private const val SESSION_IDLE_WATCHDOG_MS = 24_000L
        private const val SPEECH_WATCHDOG_MS = 8_000L
        private const val RESULT_WATCHDOG_MS = 2_000L

        private val DICE_BIASING_STRINGS = listOf(
            "एक", "इक", "one", "वन", "1", "१",
            "दो", "two", "टू", "2", "२",
            "तीन", "three", "थ्री", "3", "३",
            "चार", "four", "फोर", "फौर", "4", "४",
            "पाँच", "पांच", "पाच", "पान्च", "five", "फाइव", "फाईव", "5", "५",
            "छक्का", "छका", "छक्क", "छक", "छक्के", "छह", "छः", "छे",
            "चक्का", "चका", "चक्क", "शक्का", "छको",
            "six", "सिक्स", "सिक्सर", "सिक", "chakka", "chaka", "chhakka",
            "chhaka", "chhakkaa", "shakka", "6", "६",
            "छक्का छक्का", "छह छह", "six six",
            "पाँच पाँच", "पांच पांच", "five five",
            "चार चार", "four four", "तीन तीन", "three three",
            "दो दो", "two two", "एक एक", "one one",
            "छक्का दे", "छक्का चाहिए", "छक्का लाओ", "छक्का आना चाहिए",
            "पाँच दे", "पाँच चाहिए", "चार दे", "तीन दे", "दो दे", "एक दे",
            "dice six", "give me six", "roll six", "six please",
            "five please", "four please", "three please", "two please", "one please",
        )
    }
}
