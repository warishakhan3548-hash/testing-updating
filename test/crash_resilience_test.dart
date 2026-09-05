import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Voice reliability', () {
    test('native recognizer is single-instance and continuously re-arms safely', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(
        RegExp(r'SpeechRecognizer\.createSpeechRecognizer')
            .allMatches(activity)
            .length,
        1,
      );
      expect(activity, contains('scheduleRestart(140L)'));
      expect(activity, contains('mainHandler.removeCallbacks(restartRunnable)'));
      expect(activity, contains('SpeechRecognizer.ERROR_RECOGNIZER_BUSY'));
      expect(activity, contains('override fun onPartialResults'));
      expect(activity, contains('override fun onResults'));
      expect(activity, contains('pausedByFlutter'));
      expect(activity, contains('activityResumed'));
      expect(activity, contains('restartDelayFor'));
      expect(activity, contains('coerceAtMost(4_000L)'));
    });

    test('native speech cycles carry exact match/player/turn binding', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();
      final engine = File('lib/game/ludo_engine.dart').readAsStringSync();

      expect(activity, contains('data class VoiceBinding'));
      expect(activity, contains('recognitionBinding = binding'));
      expect(activity, contains('"matchId" to binding.matchId'));
      expect(activity, contains('"playerId" to binding.playerId'));
      expect(activity, contains('"turnId" to binding.turnId'));
      expect(activity, contains('"recognizedAtMs" to System.currentTimeMillis()'));
      expect(controller, contains('eventBinding != currentBinding'));
      expect(engine, contains('current.recognizedAt.isAfter'));
    });

    test('Dart event stream and start calls are duplicate-guarded', () {
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();

      expect(controller, contains('_eventSub ??='));
      expect(controller, contains('_starting ||'));
      expect(controller, contains('reserveDiceRoll'));
      expect(controller, contains('_rollSuspended = true'));
    });

    test('the old model extraction crash path is completely removed', () {
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
      expect(controller, isNot(contains('class VoiceDiceLatch')));
    });
  });
}
