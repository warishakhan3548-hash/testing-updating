import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:voice_ludo_masti/services/voice_dice_controller.dart';

void main() {
  group('Voice reliability', () {
    test('spoken command stays armed until a roll consumes it', () {
      final latch = VoiceDiceLatch()..setValue(6);

      expect(latch.value, 6);
      expect(latch.take(), 6);
      expect(latch.value, isNull);
      expect(latch.take(), isNull);
    });

    test('same number can be armed again after the previous roll', () {
      final latch = VoiceDiceLatch()..setValue(6);
      expect(latch.take(), 6);

      latch.setValue(6);
      expect(latch.take(), 6);
    });

    test('latest valid command replaces an older pending command', () {
      final latch = VoiceDiceLatch()
        ..setValue(4)
        ..setValue(6)
        ..setValue(2);

      expect(latch.take(), 2);
    });

    test('native recognizer automatically restarts after final/error callbacks', () {
      final activity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(activity, contains('scheduleRestart(140L)'));
      expect(activity, contains('SpeechRecognizer.ERROR_RECOGNIZER_BUSY'));
      expect(activity, contains('override fun onPartialResults'));
      expect(activity, contains('override fun onResults'));
      expect(activity, contains('pausedByFlutter'));
      expect(activity, contains('activityResumed'));
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
    });
  });
}
