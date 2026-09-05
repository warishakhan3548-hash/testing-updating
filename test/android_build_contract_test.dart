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

    test('voice uses Android SpeechRecognizer instead of a bundled model', () {
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
      expect(mainActivity, contains('SpeechRecognizer.createOnDeviceSpeechRecognizer'));
      expect(mainActivity, contains('RecognizerIntent.EXTRA_LANGUAGE'));
      expect(mainActivity, contains('private const val HINDI_LOCALE = "hi-IN"'));
      expect(mainActivity, contains('voice_ludo/speech'));
      expect(mainActivity, contains('voice_ludo/speech_events'));
      expect(manifest, contains('android.permission.RECORD_AUDIO'));
      expect(manifest, contains('android.speech.RecognitionService'));
    });

    test('native speech bridge is match scoped and partial-result optimized', () {
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
      expect(mainActivity, contains('RecognizerIntent.EXTRA_PARTIAL_RESULTS'));
      expect(mainActivity, contains('RecognizerIntent.EXTRA_BIASING_STRINGS'));
      expect(mainActivity, contains('DICE_BIASING_STRINGS'));
      expect(mainActivity, contains('EXTRA_ENABLE_LANGUAGE_SWITCH'));
      expect(mainActivity, contains('EXTRA_ENABLE_LANGUAGE_DETECTION'));
      expect(mainActivity, contains('VOICE_LOCALES = listOf("hi-IN", "en-IN", "en-US")'));
      expect(mainActivity, contains('EXTRA_PREFER_OFFLINE, usingOnDeviceRecognizer'));
      expect(mainActivity, contains('isFinal = false'));
      expect(mainActivity, contains('"छक्का छक्का"'));
      expect(mainActivity, contains('"पाँच पाँच"'));
      expect(mainActivity, contains('"six six"'));
    });

    test('turn changes hard invalidate stale native callbacks', () {
      final mainActivity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(mainActivity, contains('private var recognizerEpoch = 0L'));
      expect(mainActivity, contains('private var sessionSerial = 0L'));
      expect(mainActivity, contains('private var activeSessionId = 0L'));
      expect(mainActivity, contains('restartForContextChange()'));
      expect(mainActivity, contains('destroyRecognizer()'));
      expect(mainActivity, contains('recognizerEpoch += 1L'));
      expect(mainActivity, contains('if (!isCurrentEpoch(epoch) || !sessionActive) return'));
      expect(mainActivity, contains('if (binding != currentBinding || sessionId <= 0L) return'));
      expect(mainActivity, contains('"recognizerEpoch" to epoch'));
      expect(mainActivity, contains('"sessionId" to sessionId'));
    });

    test('high-frequency RMS callbacks never cross into Flutter', () {
      final mainActivity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(mainActivity, contains('override fun onRmsChanged(rmsdB: Float) = Unit'));
      expect(mainActivity, isNot(contains('"type" to "rms"')));
    });

    test('accepted voice intent auto-rolls through the existing atomic roll path', () {
      final gameScreen = File('lib/ui/game_screen.dart').readAsStringSync();
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();
      final engine = File('lib/game/ludo_engine.dart').readAsStringSync();

      expect(gameScreen, contains('VoiceDiceController(engine: _engine)'));
      expect(gameScreen, contains('_voice.acceptedIntentSerial'));
      expect(gameScreen, contains('scheduleMicrotask(()'));
      expect(gameScreen, contains('unawaited(_rollDice())'));
      expect(gameScreen, contains('_voice.pendingValue == null'));
      expect(controller, contains('DiceVoiceIntentParser.isDiceOnlyPhrase(heard)'));
      expect(controller, contains('reserveDiceRoll'));
      expect(engine, contains('_reservedRollResult'));
      expect(engine, contains('if (!canRoll || _reservedRollResult != null) return null'));
    });

    test('voice stays physically warm during roll but Dart gates commands', () {
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();

      expect(controller, contains('_rollSuspended = true'));
      expect(controller, contains('VoiceSessionState.processing'));
      expect(controller, contains("case 'speech':"));
      expect(controller, contains('_rollSuspended)'));
      expect(controller, contains('if (_nativeListening)'));
      expect(controller, contains('The native recognizer stays warm during dice animation/token movement'));
    });

    test('production UI does not receive raw speech transcript or confidence', () {
      final controller =
          File('lib/services/voice_dice_controller.dart').readAsStringSync();

      expect(controller, contains("String get lastHeard => '';"));
      expect(controller, contains('double? get lastConfidence => null;'));
      expect(controller, isNot(contains('_lastHeard =')));
      expect(controller, isNot(contains('_lastConfidence =')));
    });

    test('permission denial remains optional and random touch roll still works', () {
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
