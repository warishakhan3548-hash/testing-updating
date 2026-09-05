#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for command_name in flutter curl python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: $command_name is not installed or not on PATH."
    exit 1
  fi
done

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

if ! grep -Fq 'voice_ludo/native_model' \
  android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt; then
  echo "ERROR: native offline-model MethodChannel is missing from MainActivity.kt."
  exit 1
fi

if grep -Fq 'assets/models/vosk-model-small-hi-0.22.zip' pubspec.yaml; then
  echo "ERROR: the Vosk ZIP must not be a generated Flutter asset."
  exit 1
fi

if ! grep -Fq 'src/main/assets/vosk-model-small-hi-0.22.zip' android/app/build.gradle.kts; then
  echo "ERROR: Gradle is not targeting the native Android Vosk asset path."
  exit 1
fi

if ! grep -Fq 'tasks.named("preBuild")' android/app/build.gradle.kts; then
  echo "ERROR: native voice model preparation is not attached to Android preBuild."
  exit 1
fi

if ! grep -Fq 'assets.open(MODEL_ANDROID_ASSET)' \
  android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt; then
  echo "ERROR: MainActivity is not reading the native Android model asset."
  exit 1
fi

mkdir -p android/app/src/main/assets
MODEL="android/app/src/main/assets/vosk-model-small-hi-0.22.zip"
URL="https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"

model_is_valid() {
  python3 - "$MODEL" <<'PY'
from pathlib import Path
import sys
import zipfile

model = Path(sys.argv[1])
if not model.is_file() or model.stat().st_size < 10_000_000:
    raise SystemExit(1)

try:
    with zipfile.ZipFile(model) as archive:
        if archive.testzip() is not None:
            raise SystemExit(1)
        names = archive.namelist()
        if not any(
            name.endswith('/am/final.mdl') or name == 'am/final.mdl'
            for name in names
        ):
            raise SystemExit(1)
except (OSError, zipfile.BadZipFile):
    raise SystemExit(1)
PY
}

if ! model_is_valid; then
  echo "Downloading offline Hindi Vosk model into native Android assets..."
  PARTIAL="${MODEL}.part"
  rm -f "$PARTIAL"
  trap 'rm -f "$PARTIAL"' EXIT

  curl --fail --location --retry 4 --retry-delay 2 \
    --output "$PARTIAL" \
    "$URL"

  mv "$PARTIAL" "$MODEL"
  trap - EXIT

  if ! model_is_valid; then
    rm -f "$MODEL"
    echo "ERROR: downloaded offline model failed integrity validation."
    exit 1
  fi
fi

echo "Permanent Android + native voice bridge: OK"
echo "Native Android Hindi model integrity: OK"

flutter pub get
flutter test
flutter analyze --no-fatal-infos --no-fatal-warnings

echo "Android + offline voice integration verified. Run: flutter build apk --release"
