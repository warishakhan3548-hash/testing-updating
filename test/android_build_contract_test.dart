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

    test('offline model is a native Android asset, not a generated Flutter asset', () {
      final pubspec = File('pubspec.yaml').readAsStringSync();
      final appGradle = File('android/app/build.gradle.kts').readAsStringSync();
      final mainActivity = File(
        'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
      ).readAsStringSync();

      expect(
        pubspec,
        isNot(contains('assets/models/vosk-model-small-hi-0.22.zip')),
      );
      expect(
        appGradle,
        contains('src/main/assets/vosk-model-small-hi-0.22.zip'),
      );
      expect(appGradle, contains('tasks.named("preBuild")'));
      expect(appGradle, contains('dependsOn(prepareOfflineVoiceModel)'));
      expect(appGradle, contains('name.startsWith("merge")'));
      expect(appGradle, contains('name.endsWith("Assets")'));
      expect(mainActivity, contains('voice_ludo/native_model'));
      expect(mainActivity, contains('prepareOfflineVoskModel'));
      expect(mainActivity, contains('assets.open(MODEL_ANDROID_ASSET)'));
      expect(
        mainActivity,
        contains(
          'private const val MODEL_ANDROID_ASSET = "vosk-model-small-hi-0.22.zip"',
        ),
      );
      expect(mainActivity, isNot(contains('FlutterInjector')));
      expect(mainActivity, isNot(contains('getLookupKeyForAsset')));
    });

    test('local bootstrap preserves the permanent Android integration', () {
      final bootstrap = File('tool/bootstrap_android.sh').readAsStringSync();

      expect(bootstrap, isNot(contains('rm -rf android')));
      expect(bootstrap, isNot(contains('flutter create')));
      expect(
        bootstrap,
        contains(
          'android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt',
        ),
      );
      expect(bootstrap, contains('voice_ludo/native_model'));
      expect(
        bootstrap,
        contains(
          'android/app/src/main/assets/vosk-model-small-hi-0.22.zip',
        ),
      );
    });
  });
}
