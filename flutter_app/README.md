# Aarish Diary Pro — Flutter

Native Flutter conversion of the existing Aarish Diary web app. The original
`index.html` and `style.css` remain untouched; this project lives entirely in
`flutter_app/` and targets Android / Google Play first.

## What is included

- Google/Firebase Authentication
- Realtime Database compatibility with `users/{uid}/appData`
- Dashboard totals and combined Party Ledger
- Milk, Credit, Expenses, Salary, Personal Diary and Business Hub
- Create, search, filter, detail, export and permanent delete flows
- Direct Gemini AI Hub with explicit user confirmation before every mutation
- PDF share and complete CSV export
- Light/dark themes and native haptics
- Durable offline state + outbox, reconnect replay and cross-device reconciliation

Only two production Dart files are authored:

- `lib/main.dart` — native UI, forms, calculations, exports and AI Hub
- `lib/firebase_sync.dart` — schema normalization and durable Firebase sync

## Run and verify

Install current Flutter stable and Java 17, then:

```bash
cd flutter_app
flutter pub get
flutter analyze
flutter test
flutter run
```

The current execution environment used to create this conversion did not have
the Flutter SDK installed, so the repository includes deterministic logic tests
but they must be executed on a Flutter-enabled machine or CI runner.

## Firebase / Google Sign-In production requirement

The Android package is taken directly from the supplied Firebase file:

```text
com.aaris.diary.financial
```

Before testing Google Sign-In or publishing:

1. Create the Play upload key.
2. Add that key's SHA-1 and SHA-256 fingerprints to the Android app in Firebase.
3. Download the refreshed `google-services.json` and replace
   `android/app/google-services.json` if Firebase adds an Android OAuth client.

The checked-in JSON includes the Android OAuth client for the current upload
certificate. After enrolling in Play App Signing, also register the SHA-1 and
SHA-256 shown under Play Console > App integrity, then refresh this JSON before
the production rollout so Play-installed builds can use Google Sign-In.

Recommended Realtime Database rule boundary:

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "auth != null && auth.uid == $uid",
        ".write": "auth != null && auth.uid == $uid"
      }
    }
  }
}
```

## Release bundle

Codemagic signing (`CM_KEYSTORE_*`) and Flutter's local
`android/key.properties` format are supported. The keystore and passwords must
remain private and must never be committed. Once either signing source is
configured, run:

```bash
flutter build appbundle --release
```

The output is `build/app/outputs/bundle/release/app-release.aab`.

## Data safety design

Each UI mutation is first stored as one crash-safe local envelope containing
both the new state and its pending Firebase operation. Only then does the UI
repaint. Firebase acknowledgements remove operations from the outbox after the
server update succeeds; a crash between server write and acknowledgement simply
replays the idempotent write.

Deletes use explicit `null` path updates. On login/reconnect, pending operations
are replayed over the fetched cloud snapshot before it reaches the UI, so stale
cache cannot resurrect a deleted item. The sync metadata remains compatible
with the website's `AARISH_FIREBASE_COST_CORE_V12_VECTOR` protocol, including
change tokens, table revisions and compact deltas.

Firebase reads are cost-conscious: one small change-token listener while signed
in, changed-table fetches when necessary, compact delta application when safe,
and a full integrity audit no more than once per 24 hours.

The supplied iOS Firebase plist is preserved at
`firebase/GoogleService-Info.plist` for a future iOS scaffold. It is not needed
for the Google Play build.
