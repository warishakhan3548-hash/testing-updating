import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Android build contract', () {
    test('legacy Kotlin mode explicitly applies KGP before Flutter plugin', () {
      final properties = File('android/gradle.properties').readAsStringSync();
      final appGradle = File('android/app/build.gradle.kts').readAsStringSync();

      expect(properties, contains('android.builtInKotlin=false'));

      const kotlinPlugin = 'id("org.jetbrains.kotlin.android")';
      const flutterPlugin = 'id("dev.flutter.flutter-gradle-plugin")';
      final kotlinIndex = appGradle.indexOf(kotlinPlugin);
      final flutterIndex = appGradle.indexOf(flutterPlugin);

      expect(kotlinIndex, greaterThanOrEqualTo(0));
      expect(flutterIndex, greaterThan(kotlinIndex));
    });

    test('voice uses Android SpeechRecognizer instead of a bundled Vosk model', () {
      final pubspec = File('pubspec.yaml').readAsStringSync();
      final appGradle = File('android/app/build.gradle.kts').readAsStringSync();
      final manifest = File(
        'android/app/src/main/AndroidManifest.xml',
      ).readAsStringSync();
      final mainActivity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(pubspec, isNot(contains('vosk_flutter_service')));
      expect(appGradle, isNot(contains('alphacephei.com/vosk')));
      expect(appGradle, isNot(contains('prepareOfflineVoiceModel')));
      expect(mainActivity, contains('SpeechRecognizer.createSpeechRecognizer'));
      expect(mainActivity, contains('RecognizerIntent.EXTRA_LANGUAGE'));
      expect(mainActivity, contains('private const val HINDI_LOCALE = "hi-IN"'));
      expect(mainActivity, contains('voice_ludo/speech'));
      expect(mainActivity, contains('voice_ludo/speech_events'));
      expect(mainActivity, contains('pauseListening'));
      expect(manifest, contains('android.permission.RECORD_AUDIO'));
      expect(manifest, contains('android.speech.RecognitionService'));
    });

    test('native speech bridge is match-scoped, latency-biased, and lifecycle-aware', () {
      final mainActivity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(mainActivity, contains('data class VoiceBinding'));
      expect(mainActivity, contains('"updateContext"'));
      expect(mainActivity, contains('currentBinding'));
      expect(mainActivity, contains('recognitionBinding'));
      expect(mainActivity, contains('"matchId" to binding.matchId'));
      expect(mainActivity, contains('"playerId" to binding.playerId'));
      expect(mainActivity, contains('"turnId" to binding.turnId'));
      expect(mainActivity, contains('"recognizedAtMs" to System.currentTimeMillis()'));
      expect(mainActivity, contains('"type" to "lifecycle"'));
      expect(mainActivity, contains('override fun onResume()'));
      expect(mainActivity, contains('override fun onPause()'));
      expect(mainActivity, contains('EXTRA_PREFER_OFFLINE'));
      expect(mainActivity, contains('EXTRA_PARTIAL_RESULTS'));
      expect(mainActivity, contains('EXTRA_BIASING_STRINGS'));
      expect(mainActivity, contains('DICE_BIASING_STRINGS'));
      expect(mainActivity, contains('includeConfidences = false'));
      expect(mainActivity, contains('armReadyWatchdog(recognizerEpoch)'));
      expect(mainActivity, contains('recycleStuckRecognizer'));
      expect(
        mainActivity,
        contains('EXTRA_PREFER_OFFLINE, usingOnDeviceRecognizer'),
      );
    });

    test('permission denial remains an optional voice failure, not a game dependency', () {
      final mainActivity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();
      final engine = File('lib/game/ludo_engine.dart').readAsStringSync();

      expect(mainActivity, contains('SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS'));
      expect(mainActivity, contains('"type" to "permission"'));
      expect(controller, contains('_enabled = false'));
      expect(controller, contains('_clearPendingIntent()'));
      expect(engine, contains('DiceRollSource.random'));
      expect(engine, contains('randomDice()'));
    });

    test('local bootstrap preserves the permanent Android speech bridge', () {
      final bootstrap = File('tool/bootstrap_android.sh').readAsStringSync();

      expect(bootstrap, isNot(contains('rm -rf android')));
      expect(bootstrap, isNot(contains('flutter create')));
      expect(bootstrap, contains('voice_ludo/speech'));
      expect(bootstrap, contains('SpeechRecognizer.createSpeechRecognizer'));
      expect(bootstrap, isNot(contains('alphacephei.com/vosk')));
    });
  });
}
