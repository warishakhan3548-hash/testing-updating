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
