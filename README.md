# Voice Ludo Masti 🎲🎤

A local 2/3/4-player Flutter Ludo game with match-scoped Hindi + Hinglish + English voice-controlled dice.

## Voice behaviour

When a match becomes playable, voice control starts automatically after microphone permission is granted. The player does **not** need to press the microphone every turn.

Supported examples include:

- `एक / one / 1` → 1
- `दो / two / 2` → 2
- `तीन / three / 3` → 3
- `चार / four / 4` → 4
- `पाँच / पांच / five / 5` → 5
- `छक्का / छह / six / 6` → 6

Common short ASR variants such as `छक्क`, `छक`, `छका`, `शक्का`, `फौर`, `पान्च`, `chakka`, `chhakka`, and repeated phrases such as `छक्का छक्का` are normalized by a deliberately tiny six-command grammar.

A reliable partial result can trigger immediately. The accepted command automatically enters the same authoritative roll pipeline used by touch input; it does not merely change the dice artwork.

If the user taps first, the random touch roll is frozen and a later voice callback cannot overwrite it. If voice commits first, a later tap cannot create a second roll.

## Deterministic turn binding

Every playable roll opportunity has an immutable binding:

```text
matchId + playerId + turnId
```

A voice callback must match all three values before it can affect game state. Extra turns receive a new `turnId`, even when the same player remains active.

The native Android bridge also attaches:

```text
recognizerEpoch + sessionId
```

`recognizerEpoch` changes whenever the recognizer object is recreated. A **turn/context change hard-rotates the recognizer epoch before the next turn listens**, so delayed callbacks from a canceled old turn are automatically invalid.

`sessionId` identifies one recognition utterance/session. Dart uses it with the turn binding to deduplicate partial/final callbacks without a global time debounce.

## Continuous listening architecture

The app uses Android's native `SpeechRecognizer` through the permanent Kotlin bridge in:

`android/app/src/main/kotlin/com/aaris/voiceludomasti/MainActivity.kt`

The bridge provides:

- `hi-IN` as the base recognition locale
- Android 14+ language switching/detection for `hi-IN`, `en-IN`, and `en-US`
- partial results for low time-to-command
- Android 13+ biasing strings for the tiny dice vocabulary
- system recognizer first for accuracy, with on-device fallback where available
- intelligent re-arm after final results, silence, and recoverable errors
- lifecycle-safe stop/restart on app pause/resume
- permission handling for `RECORD_AUDIO`
- watchdog recovery for recognizer sessions that become stuck

The recognizer is **not** canceled for every dice animation. During rolling/token movement it may remain physically warm, but Dart places voice input behind a logical roll gate, so speech cannot mutate a non-ready roll. When a new turn binding opens, the native recognizer context is rotated safely.

This reduces avoidable microphone restart gaps while preserving strict game-state safety.

## Tiny grammar safety

The voice parser is intentionally bounded. It does not perform conversational AI or broad fuzzy semantic matching.

Exact/normalized dice aliases dominate. Repeated copies of the same value are accepted, while ambiguous phrases containing different dice values are rejected instead of guessed. For example:

```text
छक्का छक्का  -> 6
six six       -> 6
six five      -> rejected
```

Raw transcripts and ASR confidence are not surfaced in the production game UI; the UI only needs the resolved game command and a compact voice-ready state.

## Authoritative dice pipeline

`LudoEngine.reserveDiceRoll()` is the atomic roll reservation point.

It chooses exactly one immutable `DiceRollResult` from either:

- a valid current-turn voice intent, or
- the normal random dice source.

Once reserved, another voice/touch action cannot reserve a second result for that roll generation.

The existing Ludo engine remains authoritative for:

- six/extra-turn rules
- token release
- legal movement
- captures
- safe cells
- exact-home movement
- player rotation
- winner ranking

## Performance notes

High-frequency speech internals are isolated from the board rendering path. Android RMS callbacks are intentionally not sent over the Flutter event channel because the production UI does not render an audio meter.

The voice controller also avoids notifying Flutter for every rejected/raw partial transcript. UI updates are limited to meaningful availability/listening/error/accepted-command state changes.

## Ludo rules included

- 2, 3 or 4 local players
- Four tokens per player
- A six releases a token from the yard
- A six gives another turn
- Landing on an opponent on a non-safe track cell captures it and gives another turn
- Safe cells cannot be captured
- Exact roll is required to reach the final home position
- Winner ranking continues until all players are ranked

There is no three-sixes penalty in the current game rules.

## Android build contract

The repository contains a permanent Android project. Do not replace `android/` with a newly generated Flutter scaffold because `MainActivity.kt` owns the speech bridge.

The manifest includes `RECORD_AUDIO` and the Android 11+ `android.speech.RecognitionService` query. The old bundled Vosk model path is intentionally absent.

The project currently keeps AGP 9 legacy Kotlin mode (`android.builtInKotlin=false`), so `android/app/build.gradle.kts` explicitly applies `org.jetbrains.kotlin.android` before Flutter's Gradle plugin.

## Local verification

With Flutter installed:

```bash
bash tool/bootstrap_android.sh
```

That script validates the permanent Android speech bridge and runs the repository's available Flutter dependency/test/analyze checks.

Release build:

```bash
flutter build apk --release
```

Android `SpeechRecognizer` ultimately depends on the speech service installed on the phone. Recognition quality, offline availability, and language-model behavior can vary by device/OEM. Software cannot recover speech that never reaches the microphone, but the app architecture is designed to minimize avoidable latency, stale callbacks, duplicate rolls, and turn leakage.
