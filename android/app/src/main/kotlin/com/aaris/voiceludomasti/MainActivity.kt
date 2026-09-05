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

class MainActivity : FlutterActivity() {
    private data class VoiceBinding(
        val matchId: String,
        val playerId: String,
        val turnId: Long,
    )

    private val mainHandler = Handler(Looper.getMainLooper())

    private var speechRecognizer: SpeechRecognizer? = null
    private var eventSink: EventChannel.EventSink? = null

    private var voiceEnabled = false
    private var pausedByFlutter = false
    private var activityResumed = false
    private var sessionActive = false

    private var pendingStartAfterPermission = false
    private var permissionRequestInFlight = false

    private var currentBinding: VoiceBinding? = null
    private var recognitionBinding: VoiceBinding? = null

    private var restartAttempt = 0
    private var consecutiveNoMatch = 0
    private var usingOnDeviceRecognizer = false
    private var onDeviceRejectedForProcess = false
    private var recognizerEpoch = 0L

    private var readyWatchdog: Runnable? = null
    private var sessionWatchdog: Runnable? = null
    private var resultWatchdog: Runnable? = null

    private val restartRunnable = Runnable {
        if (shouldListen()) startSession()
    }

    private val warmStandbyRunnable = Runnable {
        if (shouldKeepWarm()) ensureRecognizer()
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
                    if (available && hasMicrophonePermission()) {
                        mainHandler.post {
                            if (activityResumed && speechRecognizer == null) {
                                ensureRecognizer()
                            }
                        }
                    }
                }

                "startListening" -> {
                    val binding = bindingFrom(call.arguments)
                    if (binding == null) {
                        result.error(
                            "invalid_context",
                            "A match/turn voice context is required.",
                            null,
                        )
                        return@setMethodCallHandler
                    }

                    val previousBinding = currentBinding
                    val changedWhileBound = previousBinding != null && previousBinding != binding

                    currentBinding = binding
                    voiceEnabled = true
                    pausedByFlutter = false
                    cancelWarmStandby()

                    if (changedWhileBound && sessionActive) {
                        restartForContextChange()
                    } else {
                        ensurePermissionAndStart()
                    }
                    result.success(null)
                }

                "updateContext" -> {
                    val binding = bindingFrom(call.arguments)
                    if (binding == null) {
                        result.error(
                            "invalid_context",
                            "A match/turn voice context is required.",
                            null,
                        )
                        return@setMethodCallHandler
                    }

                    val changed = currentBinding != binding
                    currentBinding = binding

                    if (changed && voiceEnabled && !pausedByFlutter && sessionActive) {
                        restartForContextChange()
                    }
                    result.success(null)
                }

                "pauseListening" -> {
                    pausedByFlutter = true
                    pauseCurrentSession(keepWarm = true)
                    result.success(null)
                }

                "stopListening" -> {
                    voiceEnabled = false
                    pausedByFlutter = false
                    pendingStartAfterPermission = false
                    currentBinding = null
                    pauseCurrentSession(keepWarm = false)
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
        voiceEnabled &&
            !pausedByFlutter &&
            activityResumed &&
            currentBinding != null

    private fun shouldKeepWarm(): Boolean =
        voiceEnabled &&
            pausedByFlutter &&
            activityResumed &&
            currentBinding != null &&
            hasMicrophonePermission()

    private fun isOnDeviceRecognitionUsable(): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            !onDeviceRejectedForProcess &&
            SpeechRecognizer.isOnDeviceRecognitionAvailable(this)

    private fun isAnyRecognitionAvailable(): Boolean =
        isOnDeviceRecognitionUsable() || SpeechRecognizer.isRecognitionAvailable(this)

    private fun ensurePermissionAndStart() {
        if (!shouldListen()) return

        if (!isAnyRecognitionAvailable()) {
            voiceEnabled = false
            emit(
                mapOf(
                    "type" to "unavailable",
                    "message" to "Android speech recognition service is unavailable on this device.",
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
            requestPermissions(
                arrayOf(Manifest.permission.RECORD_AUDIO),
                REQUEST_AUDIO_PERMISSION,
            )
        }
    }

    private fun hasMicrophonePermission(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.M ||
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != REQUEST_AUDIO_PERMISSION) return

        permissionRequestInFlight = false
        val granted =
            grantResults.isNotEmpty() &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED
        emit(mapOf("type" to "permission", "granted" to granted))

        if (!granted) {
            voiceEnabled = false
            pendingStartAfterPermission = false
            pauseCurrentSession(keepWarm = false)
            return
        }

        if (pendingStartAfterPermission && shouldListen()) {
            pendingStartAfterPermission = false
            startSession()
        } else if (shouldKeepWarm()) {
            scheduleWarmStandby()
        }
    }

    private fun ensureRecognizer(): SpeechRecognizer? {
        speechRecognizer?.let { return it }

        val recognizer =
            if (isOnDeviceRecognitionUsable()) {
                try {
                    usingOnDeviceRecognizer = true
                    SpeechRecognizer.createOnDeviceSpeechRecognizer(this)
                } catch (onDeviceError: Throwable) {
                    onDeviceRejectedForProcess = true
                    usingOnDeviceRecognizer = false
                    createSystemRecognizer(onDeviceError)
                }
            } else {
                createSystemRecognizer(null)
            } ?: return null

        speechRecognizer = recognizer
        recognizerEpoch += 1L
        val epoch = recognizerEpoch
        recognizer.setRecognitionListener(createRecognitionListener(epoch))
        return recognizer
    }

    private fun createSystemRecognizer(fallbackCause: Throwable?): SpeechRecognizer? {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            emitRecognizerCreationFailure(
                fallbackCause ?: IllegalStateException("No Android speech recognizer is available."),
            )
            return null
        }

        return try {
            usingOnDeviceRecognizer = false
            SpeechRecognizer.createSpeechRecognizer(this)
        } catch (systemError: Throwable) {
            emitRecognizerCreationFailure(systemError)
            null
        }
    }

    private fun emitRecognizerCreationFailure(error: Throwable) {
        sessionActive = false
        voiceEnabled = false
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
                if (!isCurrentRecognizerEpoch(epoch)) return
                cancelReadyWatchdog()
                restartAttempt = 0
                sessionActive = true
                armSessionWatchdog(epoch, SESSION_IDLE_WATCHDOG_MS)
                emitListening(true)
            }

            override fun onBeginningOfSpeech() {
                if (!isCurrentRecognizerEpoch(epoch)) return
                cancelReadyWatchdog()
                armSessionWatchdog(epoch, SPEECH_WATCHDOG_MS)
            }

            override fun onRmsChanged(rmsdB: Float) = Unit

            override fun onBufferReceived(buffer: ByteArray?) = Unit

            override fun onEndOfSpeech() {
                if (!isCurrentRecognizerEpoch(epoch)) return
                cancelSessionWatchdog()
                armResultWatchdog(epoch)
                emitListening(false)
            }

            override fun onError(error: Int) {
                if (!isCurrentRecognizerEpoch(epoch)) return

                cancelVoiceWatchdogs()
                sessionActive = false
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

                if (!shouldListen()) {
                    if (shouldKeepWarm()) scheduleWarmStandby()
                    return
                }

                if (error == SpeechRecognizer.ERROR_NO_MATCH ||
                    error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT
                ) {
                    consecutiveNoMatch += 1
                    if (usingOnDeviceRecognizer &&
                        consecutiveNoMatch >= ON_DEVICE_NO_MATCH_FALLBACK_THRESHOLD &&
                        SpeechRecognizer.isRecognitionAvailable(this@MainActivity)
                    ) {
                        onDeviceRejectedForProcess = true
                        destroyRecognizer()
                        emit(
                            mapOf(
                                "type" to "error",
                                "recoverable" to true,
                                "message" to "Voice accuracy boosted using system speech recognition.",
                            ),
                        )
                        scheduleRestart(SYSTEM_FALLBACK_RESTART_MS)
                        return
                    }
                }

                if (
                    error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY ||
                        error == SpeechRecognizer.ERROR_CLIENT
                ) {
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
                if (!isCurrentRecognizerEpoch(epoch)) return
                cancelVoiceWatchdogs()
                consecutiveNoMatch = 0

                emitSpeech(
                    results,
                    isFinal = true,
                    epoch = epoch,
                    includeConfidences = false,
                )

                restartAttempt = 0
                sessionActive = false
                emitListening(false)
                scheduleRestart(resultRestartDelay())
            }

            override fun onPartialResults(partialResults: Bundle?) {
                if (!isCurrentRecognizerEpoch(epoch)) return

                consecutiveNoMatch = 0
                armSessionWatchdog(epoch, SPEECH_WATCHDOG_MS)
                emitSpeech(
                    partialResults,
                    isFinal = true,
                    epoch = epoch,
                    includeConfidences = false,
                )
            }

            override fun onEvent(eventType: Int, params: Bundle?) = Unit
        }

    private fun isCurrentRecognizerEpoch(epoch: Long): Boolean =
        epoch == recognizerEpoch && speechRecognizer != null

    private fun isLanguageAvailabilityError(error: Int): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            (
                error == SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED ||
                    error == SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE
            )

    private fun fallBackFromOnDeviceRecognizer() {
        mainHandler.removeCallbacks(restartRunnable)
        cancelWarmStandby()
        onDeviceRejectedForProcess = true
        consecutiveNoMatch = 0
        destroyRecognizer()

        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            voiceEnabled = false
            emit(
                mapOf(
                    "type" to "unavailable",
                    "message" to
                        "On-device Hindi speech is unavailable and no system recognizer fallback exists.",
                ),
            )
            return
        }

        emit(
            mapOf(
                "type" to "error",
                "recoverable" to true,
                "message" to "On-device Hindi model unavailable. Using system speech recognition.",
            ),
        )
        scheduleRestart(SYSTEM_FALLBACK_RESTART_MS)
    }

    private fun buildRecognizerIntent(): Intent =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
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

            // Some OEM recognizers do not produce partial callbacks for one-word
            // utterances. These balanced endpoint values keep softly spoken commands
            // alive long enough to stabilize while still committing final results
            // quickly when the user says only "छक्का", "five" or "six".
            putExtra(
                RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS,
                COMPLETE_SILENCE_MS,
            )
            putExtra(
                RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS,
                POSSIBLY_COMPLETE_SILENCE_MS,
            )
        }

    private fun startSession() {
        if (!shouldListen() || sessionActive) return
        if (!hasMicrophonePermission()) {
            ensurePermissionAndStart()
            return
        }

        val binding = currentBinding ?: return
        val recognizer = ensureRecognizer() ?: return

        mainHandler.removeCallbacks(restartRunnable)
        cancelWarmStandby()
        cancelVoiceWatchdogs()

        recognitionBinding = binding

        try {
            sessionActive = true
            recognizer.startListening(buildRecognizerIntent())
            armReadyWatchdog(recognizerEpoch)
        } catch (error: Throwable) {
            sessionActive = false
            cancelVoiceWatchdogs()
            emitListening(false)
            emit(
                mapOf(
                    "type" to "error",
                    "recoverable" to true,
                    "message" to
                        (error.message ?: "Could not start Android voice recognition."),
                ),
            )
            destroyRecognizer()
            scheduleRestart(START_FAILURE_RESTART_MS)
        }
    }

    private fun restartForContextChange() {
        mainHandler.removeCallbacks(restartRunnable)
        cancelWarmStandby()
        consecutiveNoMatch = 0
        destroyRecognizer()
        emitListening(false)
        scheduleRestart(CONTEXT_RESTART_MS)
    }

    private fun pauseCurrentSession(keepWarm: Boolean) {
        mainHandler.removeCallbacks(restartRunnable)
        cancelWarmStandby()
        destroyRecognizer()
        emitListening(false)

        if (keepWarm && shouldKeepWarm()) {
            scheduleWarmStandby()
        }
    }

    private fun scheduleWarmStandby() {
        if (!shouldKeepWarm()) return
        cancelWarmStandby()
        mainHandler.postDelayed(warmStandbyRunnable, WARM_STANDBY_DELAY_MS)
    }

    private fun cancelWarmStandby() {
        mainHandler.removeCallbacks(warmStandbyRunnable)
    }

    private fun recycleStuckRecognizer(epoch: Long) {
        if (!isCurrentRecognizerEpoch(epoch)) return
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
        } else if (shouldKeepWarm()) {
            scheduleWarmStandby()
        }
    }

    private fun armReadyWatchdog(epoch: Long) {
        cancelReadyWatchdog()
        val runnable = Runnable {
            if (sessionActive && shouldListen()) recycleStuckRecognizer(epoch)
        }
        readyWatchdog = runnable
        mainHandler.postDelayed(runnable, READY_WATCHDOG_MS)
    }

    private fun armSessionWatchdog(epoch: Long, delayMs: Long) {
        cancelSessionWatchdog()
        val runnable = Runnable {
            if (sessionActive && shouldListen()) recycleStuckRecognizer(epoch)
        }
        sessionWatchdog = runnable
        mainHandler.postDelayed(runnable, delayMs)
    }

    private fun armResultWatchdog(epoch: Long) {
        cancelResultWatchdog()
        val runnable = Runnable {
            if (sessionActive && shouldListen()) recycleStuckRecognizer(epoch)
        }
        resultWatchdog = runnable
        mainHandler.postDelayed(runnable, RESULT_WATCHDOG_MS)
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
        recognizerEpoch += 1L
        sessionActive = false
        recognitionBinding = null

        val recognizer = speechRecognizer
        speechRecognizer = null
        usingOnDeviceRecognizer = false
        if (recognizer == null) return

        try {
            recognizer.cancel()
        } catch (_: Throwable) {
        }

        try {
            recognizer.destroy()
        } catch (_: Throwable) {
        }
    }

    private fun resultRestartDelay(): Long =
        if (usingOnDeviceRecognizer) ON_DEVICE_RESULT_RESTART_MS else SYSTEM_RESULT_RESTART_MS

    private fun restartDelayFor(error: Int): Long {
        if (
            error == SpeechRecognizer.ERROR_NO_MATCH ||
                error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT
        ) {
            restartAttempt = 0
            return if (usingOnDeviceRecognizer) {
                ON_DEVICE_NO_MATCH_RESTART_MS
            } else {
                SYSTEM_NO_MATCH_RESTART_MS
            }
        }

        val base =
            when (error) {
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> 420L
                SpeechRecognizer.ERROR_NETWORK,
                SpeechRecognizer.ERROR_NETWORK_TIMEOUT,
                SpeechRecognizer.ERROR_SERVER,
                -> 800L
                else -> 240L
            }

        val factor = 1L shl restartAttempt.coerceAtMost(3)
        restartAttempt = (restartAttempt + 1).coerceAtMost(4)
        return (base * factor).coerceAtMost(4_000L)
    }

    private fun scheduleRestart(delayMs: Long) {
        if (!shouldListen()) return
        cancelWarmStandby()
        mainHandler.removeCallbacks(restartRunnable)
        mainHandler.postDelayed(restartRunnable, delayMs)
    }

    private fun emitSpeech(
        bundle: Bundle?,
        isFinal: Boolean,
        epoch: Long,
        includeConfidences: Boolean = true,
    ) {
        if (!isCurrentRecognizerEpoch(epoch) || !shouldListen()) return

        val binding = recognitionBinding ?: return
        if (binding != currentBinding) return

        val texts =
            bundle
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.asSequence()
                ?.map { it.trim() }
                ?.filter { it.isNotEmpty() }
                ?.distinct()
                ?.take(MAX_RESULTS)
                ?.toList()
                .orEmpty()

        if (texts.isEmpty()) return

        val confidences =
            if (includeConfidences) {
                bundle
                    ?.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)
                    ?.map { it.toDouble() }
                    .orEmpty()
            } else {
                emptyList()
            }

        emit(
            mapOf(
                "type" to "speech",
                "final" to isFinal,
                "texts" to texts,
                "confidences" to confidences,
                "recognizedAtMs" to System.currentTimeMillis(),
                "recognizerEpoch" to epoch,
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
            SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED ->
                "Hindi speech recognition is not supported on this device."
            SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE ->
                "Hindi speech recognition is not currently available on this device."
            else -> "Voice recognizer error $error. Retrying…"
        }

    override fun onResume() {
        super.onResume()
        activityResumed = true
        emit(mapOf("type" to "lifecycle", "active" to true))

        when {
            shouldListen() -> ensurePermissionAndStart()
            shouldKeepWarm() -> scheduleWarmStandby()
        }
    }

    override fun onPause() {
        emit(mapOf("type" to "lifecycle", "active" to false))
        activityResumed = false
        cancelWarmStandby()
        pauseCurrentSession(keepWarm = false)
        super.onPause()
    }

    override fun onDestroy() {
        voiceEnabled = false
        pausedByFlutter = true
        pendingStartAfterPermission = false
        currentBinding = null

        mainHandler.removeCallbacks(restartRunnable)
        cancelWarmStandby()
        destroyRecognizer()
        eventSink = null

        super.onDestroy()
    }

    companion object {
        private const val VOICE_METHOD_CHANNEL = "voice_ludo/speech"
        private const val VOICE_EVENT_CHANNEL = "voice_ludo/speech_events"
        private const val REQUEST_AUDIO_PERMISSION = 7301

        private const val HINDI_LOCALE = "hi-IN"
        private const val MAX_RESULTS = 20
        private const val ON_DEVICE_NO_MATCH_FALLBACK_THRESHOLD = 2

        private const val COMPLETE_SILENCE_MS = 430L
        private const val POSSIBLY_COMPLETE_SILENCE_MS = 650L
        private const val LANGUAGE_SWITCH_ACTIVE_MS = 2_500
        private const val LANGUAGE_SWITCH_MAX_SWITCHES = 2

        private val VOICE_LOCALES = listOf("hi-IN", "en-IN", "en-US")

        private const val WARM_STANDBY_DELAY_MS = 25L

        private const val ON_DEVICE_RESULT_RESTART_MS = 30L
        private const val SYSTEM_RESULT_RESTART_MS = 70L
        private const val ON_DEVICE_NO_MATCH_RESTART_MS = 45L
        private const val SYSTEM_NO_MATCH_RESTART_MS = 85L

        private const val CONTEXT_RESTART_MS = 45L
        private const val SYSTEM_FALLBACK_RESTART_MS = 70L
        private const val STUCK_RESTART_MS = 70L
        private const val START_FAILURE_RESTART_MS = 320L

        private const val READY_WATCHDOG_MS = 2_500L
        private const val SESSION_IDLE_WATCHDOG_MS = 18_000L
        private const val SPEECH_WATCHDOG_MS = 7_000L
        private const val RESULT_WATCHDOG_MS = 2_200L

        private val DICE_BIASING_STRINGS =
            listOf(
                "एक", "इक", "one", "वन", "1", "१",
                "दो", "two", "टू", "2", "२",
                "तीन", "three", "थ्री", "3", "३",
                "चार", "four", "फोर", "4", "४",
                "पाँच", "पांच", "पाच", "पान्च", "five", "फाइव", "फाईव", "5", "५",
                "छक्का", "छका", "छक्के", "छह", "छः", "छे", "चक्का", "छको",
                "six", "सिक्स", "सिक्सर", "chakka", "chhakka", "chhakkaa", "6", "६",
                "छक्का छक्का", "छह छह", "six six",
                "पाँच पाँच", "पांच पांच", "five five",
                "चार चार", "four four",
                "तीन तीन", "three three",
                "दो दो", "two two",
                "एक एक", "one one",
                "छक्का दे", "छक्का चाहिए", "छक्का लाओ", "पाँच दे", "चार दे",
                "dice six", "give me six", "roll six", "six please",
                "five please", "four please", "three please", "two please", "one please",
            )
    }
}
