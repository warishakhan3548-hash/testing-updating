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

class MainActivity : FlutterActivity() {
    private val mainHandler = Handler(Looper.getMainLooper())

    private var speechRecognizer: SpeechRecognizer? = null
    private var eventSink: EventChannel.EventSink? = null
    private var voiceEnabled = false
    private var pausedByFlutter = false
    private var activityResumed = false
    private var sessionActive = false
    private var pendingStartAfterPermission = false

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
                "isAvailable" -> result.success(SpeechRecognizer.isRecognitionAvailable(this))
                "startListening" -> {
                    voiceEnabled = true
                    pausedByFlutter = false
                    ensurePermissionAndStart()
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
                    pauseCurrentSession()
                    result.success(null)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun shouldListen(): Boolean =
        voiceEnabled && !pausedByFlutter && activityResumed

    private fun ensurePermissionAndStart() {
        if (!shouldListen()) return

        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
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
            ensureRecognizer()
            startSession()
            return
        }

        pendingStartAfterPermission = true
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_AUDIO_PERMISSION)
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

        val granted = grantResults.isNotEmpty() &&
            grantResults[0] == PackageManager.PERMISSION_GRANTED
        emit(mapOf("type" to "permission", "granted" to granted))

        if (!granted) {
            voiceEnabled = false
            pendingStartAfterPermission = false
            emitListening(false)
            return
        }

        if (pendingStartAfterPermission && shouldListen()) {
            pendingStartAfterPermission = false
            ensureRecognizer()
            startSession()
        }
    }

    private fun ensureRecognizer() {
        if (speechRecognizer != null) return

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).also { recognizer ->
            recognizer.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {
                    sessionActive = true
                    emitListening(true)
                }

                override fun onBeginningOfSpeech() = Unit
                override fun onRmsChanged(rmsdB: Float) = Unit
                override fun onBufferReceived(buffer: ByteArray?) = Unit

                override fun onEndOfSpeech() {
                    emitListening(false)
                }

                override fun onError(error: Int) {
                    sessionActive = false
                    emitListening(false)

                    if (error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS) {
                        voiceEnabled = false
                        emit(mapOf("type" to "permission", "granted" to false))
                        return
                    }

                    if (!shouldListen()) return

                    val delayMs = when (error) {
                        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> 700L
                        SpeechRecognizer.ERROR_NETWORK,
                        SpeechRecognizer.ERROR_NETWORK_TIMEOUT,
                        SpeechRecognizer.ERROR_SERVER -> 1000L
                        else -> 220L
                    }

                    emit(
                        mapOf(
                            "type" to "error",
                            "code" to error,
                            "recoverable" to true,
                            "message" to recognitionErrorMessage(error),
                        ),
                    )
                    scheduleRestart(delayMs)
                }

                override fun onResults(results: Bundle?) {
                    emitSpeech(results, isFinal = true)
                    sessionActive = false
                    emitListening(false)
                    scheduleRestart(140L)
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    emitSpeech(partialResults, isFinal = false)
                }

                override fun onEvent(eventType: Int, params: Bundle?) = Unit
            })
        }
    }

    private fun startSession() {
        if (!shouldListen() || sessionActive) return
        if (!hasMicrophonePermission()) {
            ensurePermissionAndStart()
            return
        }

        ensureRecognizer()
        val recognizer = speechRecognizer ?: return
        mainHandler.removeCallbacks(restartRunnable)

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, HINDI_LOCALE)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, MAX_RESULTS)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, packageName)
        }

        try {
            sessionActive = true
            recognizer.startListening(intent)
        } catch (error: Throwable) {
            sessionActive = false
            emitListening(false)
            emit(
                mapOf(
                    "type" to "error",
                    "recoverable" to true,
                    "message" to (error.message ?: "Could not start Android voice recognition."),
                ),
            )
            scheduleRestart(700L)
        }
    }

    private fun pauseCurrentSession() {
        mainHandler.removeCallbacks(restartRunnable)
        sessionActive = false
        try {
            speechRecognizer?.cancel()
        } catch (_: Throwable) {
        }
        emitListening(false)
    }

    private fun scheduleRestart(delayMs: Long) {
        if (!shouldListen()) return
        mainHandler.removeCallbacks(restartRunnable)
        mainHandler.postDelayed(restartRunnable, delayMs)
    }

    private fun emitSpeech(bundle: Bundle?, isFinal: Boolean) {
        val texts = bundle
            ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            ?.filter { it.isNotBlank() }
            .orEmpty()
        if (texts.isEmpty()) return

        emit(
            mapOf(
                "type" to "speech",
                "final" to isFinal,
                "texts" to texts,
            ),
        )
    }

    private fun emitAvailability() {
        emit(
            mapOf(
                "type" to "availability",
                "available" to SpeechRecognizer.isRecognitionAvailable(this),
            ),
        )
    }

    private fun emitListening(active: Boolean) {
        emit(mapOf("type" to "listening", "active" to (active && shouldListen())))
    }

    private fun emit(event: Map<String, Any?>) {
        eventSink?.success(event)
    }

    private fun recognitionErrorMessage(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_AUDIO -> "Microphone audio error. Retrying…"
        SpeechRecognizer.ERROR_CLIENT -> "Voice recognizer restarted."
        SpeechRecognizer.ERROR_NETWORK -> "Voice network error. Retrying…"
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Voice network timeout. Retrying…"
        SpeechRecognizer.ERROR_NO_MATCH -> "Listening for a dice number…"
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Voice recognizer is busy. Retrying…"
        SpeechRecognizer.ERROR_SERVER -> "Voice service error. Retrying…"
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Listening for a dice number…"
        else -> "Voice recognizer error $error. Retrying…"
    }

    override fun onResume() {
        super.onResume()
        activityResumed = true
        if (shouldListen()) ensurePermissionAndStart()
    }

    override fun onPause() {
        activityResumed = false
        pauseCurrentSession()
        super.onPause()
    }

    override fun onDestroy() {
        voiceEnabled = false
        pausedByFlutter = true
        mainHandler.removeCallbacks(restartRunnable)
        try {
            speechRecognizer?.destroy()
        } catch (_: Throwable) {
        }
        speechRecognizer = null
        eventSink = null
        super.onDestroy()
    }

    companion object {
        private const val VOICE_METHOD_CHANNEL = "voice_ludo/speech"
        private const val VOICE_EVENT_CHANNEL = "voice_ludo/speech_events"
        private const val REQUEST_AUDIO_PERMISSION = 7301
        private const val HINDI_LOCALE = "hi-IN"
        private const val MAX_RESULTS = 5
    }
}
