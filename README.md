# Voice Ludo Masti 🎲🎤

A local 2/3/4-player Flutter Ludo game where the **latest spoken dice number controls the next roll**. Voice recognition is designed to run **fully offline on Android** with a bundled Vosk Hindi mobile model.

## Core behaviour

- Say `एक / वन` through `छक्का / सिक्स` (the parser also understands common English/transliterated variants).
- The latest valid number replaces any older pending number.
- Tap **ROLL** and the animated dice resolves to that number.
- The voice command is consumed for exactly one roll.
- If no voice number is pending, the dice uses a normal random 1–6 value.
- Recognition is frozen at the roll boundary and while choosing a token, so stale microphone results cannot leak into the next player's roll.
- There is **no three-sixes penalty**. Six can be intentionally rolled any number of times.
- A six still earns another roll even when the exact-home rule leaves no legal move.

## Ludo rules included

- 2, 3 or 4 local players.
- Four tokens per player.
- A six releases a token from the yard.
- A six gives another turn.
- Landing on an opponent on a non-safe track cell captures it and gives another turn.
- Safe cells cannot be captured.
- Exact roll is required to reach the final home position.
- Winner ranking continues until all players are ranked.

## Advanced offline voice architecture

The app uses **Vosk** with `vosk-model-small-hi-0.22`, a lightweight Hindi model intended for mobile/offline use. The APK bundles the model during the Codemagic build, so the installed game does not need internet access for dice recognition.

The recognizer uses a deliberately tiny command grammar containing only dice words plus `[unk]`. This has two advantages:

1. General room conversation can be rejected instead of being forced into a number.
2. Very short commands such as `छक्का`, `पाँच`, `फाइव`, or `सिक्स` are cheaper and faster to recognize than full dictation.

Partial recognition uses a stability filter. Two matching partial frames normally lock a command, while a very recent candidate is still allowed at the exact roll boundary so a fast `say four → instantly tap roll` interaction remains responsive.

There is no command queue. The newest accepted value overwrites the older one:

```text
say: छक्का
say: पाँच
say: चार
tap ROLL
=> 4
```

Recognition is reset between resolved rolls to prevent buffered audio from one turn affecting another turn.

## Android build contract

The repository contains a **permanent Android project** with a native MethodChannel that streams the bundled Vosk ZIP to app-private storage. Do not replace the `android/` directory with a freshly generated Flutter scaffold: doing so removes the native `voice_ludo/native_model` bridge and breaks offline voice initialization.

This project currently keeps AGP 9 legacy Kotlin mode (`android.builtInKotlin=false`) for plugin compatibility. Therefore `android/app/build.gradle.kts` must explicitly apply `org.jetbrains.kotlin.android` so `MainActivity.kt` and the native voice bridge are compiled.

## Codemagic build

Use the `Voice Ludo Offline AI APK` workflow from the root `codemagic.yaml`.

The workflow:

1. Verifies the permanent Android project, Kotlin configuration, and native voice bridge.
2. Downloads and integrity-checks the official Hindi Vosk mobile model into `assets/models/`.
3. Runs `flutter pub get`.
4. Runs the logic and Android build-contract tests.
5. Runs `flutter analyze`.
6. Builds the release APK.

The built APK is published as a Codemagic artifact.

## Local Android setup

With Flutter installed, run:

```bash
bash tool/bootstrap_android.sh
```

The script is intentionally **non-destructive**. It validates the permanent Android/Kotlin/native voice integration, downloads and verifies the offline model when necessary, then runs dependencies, tests, and analysis. It never deletes or regenerates the `android/` directory.

After it succeeds, build with:

```bash
flutter build apk --release
```

## Privacy / network behaviour

Runtime speech recognition is local. The Android app only needs microphone permission for voice dice. The model download occurs at build/setup time, not while playing.
