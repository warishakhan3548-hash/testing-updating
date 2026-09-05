#!/usr/bin/env bash
set -euo pipefail

if ! command -v flutter >/dev/null 2>&1; then
  echo "ERROR: Flutter is not installed or not on PATH."
  exit 1
fi

flutter create . --platforms=android --project-name voice_ludo_masti --org com.aaris

python3 - <<'PY'
from pathlib import Path

manifest = Path('android/app/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
permissions = [
    '<uses-permission android:name="android.permission.RECORD_AUDIO" />',
    '<uses-permission android:name="android.permission.INTERNET" />',
]

insert = '\n'.join(p for p in permissions if p not in text)
if insert:
    marker = '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
    if marker not in text:
        raise SystemExit('Could not locate <manifest> header to add microphone permission.')
    text = text.replace(marker, marker + '\n    ' + insert.replace('\n', '\n    '), 1)
    manifest.write_text(text, encoding='utf-8')
PY

flutter pub get

echo "Android scaffold ready. Run: flutter run"
