#!/usr/bin/env bash
set -euo pipefail

if ! command -v flutter >/dev/null 2>&1; then
  echo "ERROR: Flutter is not installed or not on PATH."
  exit 1
fi

mkdir -p assets/models
MODEL="assets/models/vosk-model-small-hi-0.22.zip"
if [ ! -s "$MODEL" ]; then
  echo "Downloading offline Hindi Vosk model..."
  curl --fail --location --retry 4 --retry-delay 2 \
    --output "$MODEL" \
    "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"
fi

TMP_DIR="${TMPDIR:-/tmp}/voice_ludo_android_scaffold"
rm -rf "$TMP_DIR"

flutter create "$TMP_DIR" \
  --platforms=android \
  --project-name voice_ludo_masti \
  --org com.aaris

rm -rf android
cp -R "$TMP_DIR/android" ./android

python3 - <<'PY'
from pathlib import Path

manifest = Path('android/app/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
permission = '<uses-permission android:name="android.permission.RECORD_AUDIO" />'
marker = '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
if marker not in text:
    raise SystemExit('Could not locate <manifest> header.')
if permission not in text:
    text = text.replace(marker, marker + '\n    ' + permission, 1)
manifest.write_text(text, encoding='utf-8')

proguard = Path('android/app/proguard-rules.pro')
proguard.write_text(
    '-keep class com.sun.jna.* { *; }\n'
    '-keepclassmembers class * extends com.sun.jna.* { public *; }\n',
    encoding='utf-8',
)
PY

flutter pub get
flutter test
flutter analyze

echo "Android + offline voice scaffold ready. Run: flutter build apk --release"
