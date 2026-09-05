#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v flutter >/dev/null 2>&1; then
  echo "ERROR: flutter is not installed or not on PATH."
  exit 1
fi

required_android_files=(
  "android/settings.gradle.kts"
  "android/build.gradle.kts"
  "android/gradle.properties"
  "android/app/build.gradle.kts"
  "android/app/src/main/AndroidManifest.xml"
  "android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt"
)

for file in "${required_android_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "ERROR: required permanent Android integration is missing: $file"
    exit 1
  fi
done

if ! grep -Fq 'android.builtInKotlin=false' android/gradle.properties; then
  echo "ERROR: Android Kotlin mode no longer matches this project's verified legacy-KGP setup."
  exit 1
fi

if ! grep -Fq 'id("org.jetbrains.kotlin.android")' android/app/build.gradle.kts; then
  echo "ERROR: Kotlin Android plugin is not applied; MainActivity.kt would not be compiled."
  exit 1
fi

ACTIVITY="android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt"
if ! grep -Fq 'voice_ludo/speech' "$ACTIVITY" || \
   ! grep -Fq 'SpeechRecognizer.createSpeechRecognizer' "$ACTIVITY"; then
  echo "ERROR: native Android speech-recognition bridge is missing."
  exit 1
fi

if ! grep -Fq 'android.speech.RecognitionService' android/app/src/main/AndroidManifest.xml; then
  echo "ERROR: Android 11+ speech-recognition service query is missing."
  exit 1
fi

if grep -Fq 'vosk_flutter_service' pubspec.yaml; then
  echo "ERROR: legacy Vosk dependency is still present."
  exit 1
fi

# Remove any large Vosk ZIP left behind by an older local checkout so it cannot
# silently bloat the next APK after this migration.
rm -f \
  android/app/src/main/assets/vosk-model-small-hi-0.22.zip \
  android/app/src/main/assets/vosk-model-small-hi-0.22.zip.part

echo "Permanent Android + system speech bridge: OK"
echo "Legacy Vosk model path: removed"

flutter pub get
flutter test
flutter analyze --no-fatal-infos --no-fatal-warnings

echo "Voice integration verified. Run: flutter build apk --release"
