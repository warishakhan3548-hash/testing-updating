# Aarish Dairy Pro — Flutter

Native Flutter conversion of the Aarish Dairy web app, targeting Android /
Google Play first. The real Flutter project now lives at the repository root,
so Codemagic project path `.` resolves this `pubspec.yaml` directly.

## What is included

- Google/Firebase Authentication
- Realtime Database compatibility with `users/{uid}/appData`
- Dashboard totals and combined Party Ledger
- Milk, Credit, Expenses, Salary, Personal Diary and Business Hub
- Create, search, filter, detail, export and permanent delete flows
- Direct Gemini AI Hub with explicit user confirmation before every mutation
- Export Center with paginated Hindi/English PDF, complete CSV and AI-readable ledger for all seven scopes
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
Release builds fail closed when neither signing source exists; the build never
silently falls back to Android's debug certificate.

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

Record identity always comes from the authoritative RTDB child key, preventing
malformed embedded IDs from creating undeletable ghost rows. Repeated offline
edits to one exact path are compacted to their final value, while parent/child
operations retain ordering. Paths and nested values are validated against RTDB
key, depth and UTF-8 limits before the durable outbox accepts them and again
before upload. Outgoing multi-location writes are split by encoded bytes and
the same 24-path limit used by delta metadata, so large queues do not become
stuck on one oversized request or force an avoidable full-table fallback.

Firebase reads are cost-conscious: one small change-token listener while signed
in, compact delta application when safe, targeted changed-record reads for
large values, changed-table fallback fetches when necessary, and an automatic
full integrity audit no more than once every seven days. Dashboard, navigation
tones, party balances and module summary cards share one immutable monthly
projection, so connection/status repaints never rescan the complete ledger.
Reconciliation and uncached month reads wait for a positive
`.info/connected` signal, preventing Firebase's offline `get()` fallback from
mistaking a stale SDK cache entry for current server state.

## Guarded monthly Diary projection

`ledgerV2` is an opt-in server-owned read model. The Flutter app uses it only
when `meta/diary` reports schema version 2 and both its `sourceRevision` and
per-writer `sourceClockHash` exactly match the legacy V12 `diaryDB` source.
The vector-clock hash also distinguishes concurrent writes that happen to use
the same numeric revision. Any mismatch fails closed to `users/{uid}/appData`,
preserving existing website and older-client behavior.

When active, startup downloads only the current Diary month. The compact period
index drives the month picker and an older month is fetched only when selected.
An All Data/Diary export or AI snapshot explicitly reads one stable,
authoritative `diaryDB` snapshot, checks the source metadata before and after
the read, and replays pending local writes over it. This keeps normal browsing
month-scoped without ever silently producing a partial full-history export.

The Firebase function consumes V12 metadata in revision order, projects only
the changed Diary IDs for normal writes, and performs a stable full rebuild for
first migration, an oversized batch, or a broken/out-of-order revision chain.
Full rebuilds reuse their single source snapshot instead of rereading every
Diary entry. Retried events whose target is already projected are discarded
instead of triggering another full rebuild, keeping RTDB read amplification
bounded as a ledger grows.
The database rules keep `ledgerV2` client read-only and index `_period`; deploy
the function and rules together. The checked-in Firebase project alias targets
`diary-book-21a91`, reducing accidental deployment to a different project. An
admin-only `backfillDiaryV2` callable can
prebuild an existing user's projection, while the first later Diary mutation
also bootstraps it automatically.

Function dependencies are pinned by `functions/package-lock.json`; CI installs
that exact graph on Node 22 and loads the deployed entrypoint before running
projection tests. The production dependency audit also fails the build on any
high or critical advisory.

The supplied iOS Firebase plist is preserved at
`firebase/GoogleService-Info.plist` for a future iOS scaffold. It is not needed
for the Google Play build.
