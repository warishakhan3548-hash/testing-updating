import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Voice reliability', () {
    test('native recognizer is single-instance guarded and continuously re-arms', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(activity, contains('recognizer?.let { return it }'));
      expect(activity, contains('SpeechRecognizer.createOnDeviceSpeechRecognizer'));
      expect(activity, contains('SpeechRecognizer.createSpeechRecognizer'));
      expect(activity, contains('destroyRecognizer()'));
      expect(activity, contains('recognizer = null'));
      expect(activity, contains('scheduleRestart(resultRestartDelay())'));
      expect(activity, contains('scheduleRestart(restartDelayFor(error))'));
      expect(activity, contains('mainHandler.removeCallbacks(restartRunnable)'));
      expect(activity, contains('SpeechRecognizer.ERROR_RECOGNIZER_BUSY'));
      expect(activity, contains('override fun onPartialResults'));
      expect(activity, contains('override fun onResults'));
      expect(activity, contains('pausedByFlutter'));
      expect(activity, contains('activityResumed'));
      expect(activity, contains('restartDelayFor'));
      expect(activity, contains('coerceAtMost(4_000L)'));
      expect(activity, contains('armReadyWatchdog(recognizerEpoch)'));
      expect(activity, contains('armResultWatchdog(epoch)'));
      expect(activity, contains('recycleStuckRecognizer(epoch)'));
    });

    test('Android 13+ biases recognition toward the tiny dice vocabulary', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(activity, contains('Build.VERSION_CODES.TIRAMISU'));
      expect(activity, contains('RecognizerIntent.EXTRA_BIASING_STRINGS'));
      expect(activity, contains('DICE_BIASING_STRINGS'));
      expect(activity, contains('"छक्का"'));
      expect(activity, contains('"छक्क"'));
      expect(activity, contains('"शक्का"'));
      expect(activity, contains('"पाँच"'));
      expect(activity, contains('"six"'));
      expect(activity, contains('"confidences" to emptyList<Double>()'));
      expect(activity, contains('isFinal = false'));
    });

    test('native speech callbacks carry exact turn and utterance identity', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();
      final engine = File('lib/game/ludo_engine.dart').readAsStringSync();

      expect(activity, contains('data class VoiceBinding'));
      expect(activity, contains('recognitionBinding = binding'));
      expect(activity, contains('if (binding != currentBinding || sessionId <= 0L) return'));
      expect(activity, contains('"matchId" to binding.matchId'));
      expect(activity, contains('"playerId" to binding.playerId'));
      expect(activity, contains('"turnId" to binding.turnId'));
      expect(activity, contains('"recognizerEpoch" to epoch'));
      expect(activity, contains('"sessionId" to sessionId'));
      expect(controller, contains('eventBinding != currentBinding'));
      expect(controller, contains('_SpeechSessionKey'));
      expect(controller, contains('speechSession == _lastAcceptedSpeechSession'));
      expect(engine, contains('current.recognizedAt.isAfter'));
    });

    test('turn rebind destroys old recognizer before new turn can listen', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(activity, contains('private var recognizerEpoch = 0L'));
      expect(activity, contains('restartForContextChange()'));
      expect(activity, contains('recognizerEpoch += 1L'));
      expect(activity, contains('if (!isCurrentEpoch(epoch) || !sessionActive) return'));

      final rebindStart = activity.indexOf('private fun restartForContextChange()');
      final pauseStart = activity.indexOf('private fun pauseCurrentSession()', rebindStart);
      final rebindBody = activity.substring(rebindStart, pauseStart);
      expect(rebindBody, contains('destroyRecognizer()'));
      expect(rebindBody, contains('scheduleRestart(CONTEXT_REARM_MS)'));
    });

    test('roll boundary gates Dart commands without canceling the warm recognizer', () {
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();

      final suspendStart = controller.indexOf('Future<int?> suspendForRoll()');
      final resumeStart = controller.indexOf('Future<void> resumeAfterRoll()', suspendStart);
      expect(suspendStart, greaterThanOrEqualTo(0));
      expect(resumeStart, greaterThan(suspendStart));

      final suspendBody = controller.substring(suspendStart, resumeStart);
      expect(suspendBody, contains('reserveDiceRoll'));
      expect(suspendBody, contains('_rollSuspended = true'));
      expect(suspendBody, contains('VoiceSessionState.processing'));
      expect(suspendBody, isNot(contains('pauseListening')));
    });

    test('Dart event stream and auto-roll are duplicate guarded', () {
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();
      final gameScreen = File('lib/ui/game_screen.dart').readAsStringSync();

      expect(controller, contains('_eventSub ??='));
      expect(controller, contains('_starting ||'));
      expect(controller, contains('_nativeListening ||'));
      expect(controller, contains('reserveDiceRoll'));
      expect(controller, contains('_lastAcceptedSpeechSession = speechSession'));
      expect(gameScreen, contains('_handledVoiceIntentSerial'));
      expect(gameScreen, contains('_voice.acceptedIntentSerial'));
      expect(gameScreen, contains('_rollActionBusy'));
      expect(gameScreen, contains('_voice.pendingValue == null'));
    });

    test('microphone permission prompt cannot be requested repeatedly in parallel', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(activity, contains('permissionRequestInFlight'));
      expect(activity, contains('!permissionRequestInFlight'));
      expect(activity, contains('permissionRequestInFlight = true'));
      expect(activity, contains('permissionRequestInFlight = false'));
    });

    test('on-device language failure falls back once instead of restart-looping', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(activity, contains('onDeviceRejectedForProcess'));
      expect(activity, contains('isLanguageAvailabilityError(error) && usingOnDeviceRecognizer'));
      expect(activity, contains('fallBackFromOnDeviceRecognizer()'));
      expect(activity, contains('"recoverable" to false'));
    });

    test('old model extraction and global debounce paths are absent', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();

      expect(activity, isNot(contains('ZipInputStream')));
      expect(activity, isNot(contains('prepareOfflineVoskModel')));
      expect(activity, isNot(contains('MIN_VOSK_HEADROOM_MB')));
      expect(controller, isNot(contains('vosk_flutter_service')));
      expect(controller, isNot(contains('candidateFreshness')));
      expect(controller, isNot(contains('Timer(')));
      expect(controller, isNot(contains('class VoiceDiceLatch')));
    });
  });
}
