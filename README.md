# Voice Ludo Masti 🎲🎤

A local 2/3/4-player Flutter Ludo game where the **latest spoken dice number controls the next roll**.

## Core behaviour

- Say `एक / one / 1` through `छक्का / six / 6`.
- The latest valid number replaces any older pending number.
- Tap **ROLL** and the animated dice resolves to that number.
- The voice command is consumed for exactly one roll.
- If no voice number is pending, the dice uses a normal random 1–6 value.
- Recognition is suspended at the roll boundary and while choosing a token, so late/stale speech callbacks cannot leak into the next player's roll.
- There is **no three-sixes penalty**. Six can be intentionally rolled any number of times.

## Ludo rules included

- 2, 3 or 4 local players.
- Four tokens per player.
- A six releases a token from the yard.
- A six gives another turn.
- Landing on an opponent on a non-safe track cell captures it and gives another turn.
- Safe cells cannot be captured.
- Exact roll is required to reach the final home position.
- Winner ranking continues until all players are ranked.

## Voice architecture

`speech_to_text` is used as a short-command recognizer. The app automatically re-opens listening sessions when the platform closes one. Each listen session has a monotonic generation ID; callbacks from an older generation are ignored. Starting a dice roll increments the generation and stops recognition before consuming the pending value.

This makes the important sequence deterministic:

```text
say: six
say: five
say: four
tap ROLL
=> 4
```

## Run

This repository contains the Flutter app source. If platform scaffolding is not present yet, from the project root run:

```bash
flutter create . --platforms=android
flutter pub get
```

Then add microphone permission to `android/app/src/main/AndroidManifest.xml` if your generated scaffold does not already contain it:

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```

Run on a physical Android phone for the best speech-recognition experience:

```bash
flutter run
```

## Notes

Speech recognition depends on the speech service installed on the device and may require network access depending on that service. Hindi is preferred when available, with Indian English/system locale fallback. The parser also accepts common Hindi, English and transliterated number forms.
