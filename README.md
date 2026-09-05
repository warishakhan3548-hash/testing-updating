# Voice Ludo Masti 🎲🎤

A local 2/3/4-player Flutter Ludo game where the **latest spoken dice number controls the next roll**.

## Exact voice behaviour

- Say `एक / वन` through `छक्का / सिक्स` in a normal voice.
- Recognition runs continuously while the game is ready for a command.
- As soon as a valid number is heard, that value is **latched with no timeout**.
- Tap **ROLL** whenever you want; the latched number is consumed and that exact dice value is produced.
- The command is consumed for exactly one roll, so `छक्का → ROLL` gives 6 once.
- After the move, saying `छक्का` again arms 6 again for the next roll.
- If you say a different valid number before rolling, the newest number replaces the older one.
- If no number is armed, ROLL remains a normal random 1–6 roll.

```text
say: छक्का
wait if you want
tap ROLL
=> 6

move the token
say: छक्का
tap ROLL
=> 6
```

There is no three-sixes penalty. Six can intentionally be rolled repeatedly.

## Voice architecture

The old bundled Vosk Hindi-model path has been removed. It could fail during model preparation on real phones and it also expired a spoken command after about 1.4 seconds, which did not match the intended game interaction.

The app now uses Android's native `SpeechRecognizer` service through a small permanent Kotlin bridge in `MainActivity.kt`:

- language: `hi-IN`
- partial results: enabled for fast command capture
- normal Android recognition service: no app-bundled speech model
- recognizer session automatically restarts after silence, final results, or recoverable errors
- microphone permission is handled by the Android bridge
- the recognizer pauses only at the roll boundary so buffered speech cannot leak into the same roll

Dart receives speech events through `voice_ludo/speech_events` and controls the native recognizer through `voice_ludo/speech`.

`VoiceDiceLatch` is the single source of truth for the pending dice command. It deliberately has **no freshness timer**. The value only changes when a newer valid command is heard or when ROLL consumes it.

## Ludo rules included

- 2, 3 or 4 local players.
- Four tokens per player.
- A six releases a token from the yard.
- A six gives another turn.
- Landing on an opponent on a non-safe track cell captures it and gives another turn.
- Safe cells cannot be captured.
- Exact roll is required to reach the final home position.
- Winner ranking continues until all players are ranked.

## Android build contract

The repository contains a permanent Android project. `MainActivity.kt` owns the `SpeechRecognizer` bridge, so do not replace `android/` with a newly generated Flutter scaffold.

The manifest includes `RECORD_AUDIO` and the Android 11+ `android.speech.RecognitionService` query. The Flutter dependency on `vosk_flutter_service` is intentionally gone, and the build no longer downloads or packages a Vosk model.

The project currently keeps AGP 9 legacy Kotlin mode (`android.builtInKotlin=false`), so `android/app/build.gradle.kts` explicitly applies `org.jetbrains.kotlin.android` before Flutter's Gradle plugin.

## Local verification

With Flutter installed, run:

```bash
bash tool/bootstrap_android.sh
```

The script validates the permanent Android speech bridge, removes any stale Vosk ZIP left by an older local checkout, then runs dependencies, tests, and analysis.

Build with:

```bash
flutter build apk --release
```

## Runtime note

Android `SpeechRecognizer` uses the speech service installed on the phone. On typical Google-enabled Android phones it can use the device/Google speech service and may use network connectivity depending on the phone's installed language recognition capabilities.
