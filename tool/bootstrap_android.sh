#!/usr/bin/env bash
set -euo pipefail

if ! command -v flutter >/dev/null 2>&1; then
  echo "ERROR: Flutter is not installed or not on PATH."
  exit 1
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

permissions = [
    '<uses-permission android:name="android.permission.RECORD_AUDIO" />',
    '<uses-permission android:name="android.permission.INTERNET" />',
]

marker = '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
if marker not in text:
    raise SystemExit('Could not locate <manifest> header.')

missing = [p for p in permissions if p not in text]
if missing:
    text = text.replace(marker, marker + '\n    ' + '\n    '.join(missing), 1)

queries = '''    <queries>
        <intent>
            <action android:name="android.speech.RecognitionService" />
        </intent>
    </queries>
'''
if 'android.speech.RecognitionService' not in text:
    app_marker = '    <application'
    if app_marker not in text:
        raise SystemExit('Could not locate <application> node.')
    text = text.replace(app_marker, queries + app_marker, 1)

manifest.write_text(text, encoding='utf-8')
PY

flutter pub get

echo "Android scaffold ready. Run: flutter build apk --release"
