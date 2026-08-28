# Aarish Dairy Pro — Flutter

Native Flutter conversion of the Aarish Dairy web app, targeting Android / Google Play first. The real Flutter project now lives at the repository root, so Codemagic project path `.` resolves this `pubspec.yaml` directly.

## What is included

- Google/Firebase Authentication
- Realtime Database compatibility with `users/{uid}/appData`
- Dashboard totals and combined Party Ledger
- Milk, Credit, Expenses, Salary, Personal Diary and Business Hub
- Create, search, filter, detail, export and permanent delete flows
- Direct Gemini AI Hub with explicit user confirmation before every mutation
- Export Center with PDF, complete CSV and AI-readable ledger for all seven scopes
- Light/dark themes and native haptics
- Native date picker, debounced search and active-tab-only Firebase repainting
- Durable offline state + outbox, reconnect replay and cross-device reconciliation

Only two production Dart files are authored:

- `lib/main.dart` — native UI, forms, calculations, exports and AI Hub
- `lib/firebase_sync.dart` — schema normalization and durable Firebase sync

## Run and verify

Install current Flutter stable and Java 17, then:

```bash
flutter pub get
flutter analyze
flutter test
flutter run
```

The current execution environment used to create this conversion did not have the Flutter SDK installed, so the repository includes deterministic logic tests but they must be executed in CI / Codemagic or on a Flutter-enabled developer machine.

## Android / Firebase

The checked-in Android project uses package id `com.aarish.dairypro`.

For a real Firebase build, place the Android Firebase config at:

```text
android/app/google-services.json
```

Do not commit signing secrets. Release signing is wired to read environment variables or `android/key.properties` when supplied by the build system.

## Codemagic

Use repository root as the project directory and Flutter stable. A typical pipeline is:

```bash
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

For Play Store delivery, configure signing in Codemagic and build an app bundle:

```bash
flutter build appbundle --release
```
