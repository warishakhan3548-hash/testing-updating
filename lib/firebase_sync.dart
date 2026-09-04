import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;

import 'package:crypto/crypto.dart' as crypto;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:uuid/uuid.dart';

const List<String> ledgerRoots = <String>[
  'milkDB',
  'udharDB',
  'expenseDB',
  'salaryDB',
  'diaryDB',
  'projectDB',
];

const int ledgerDeltaPathLimit = 24;

const Set<String> _listRoots = <String>{'udharDB', 'expenseDB', 'diaryDB'};

const Set<String> _groupedRoots = <String>{'milkDB', 'salaryDB', 'projectDB'};

final RegExp ledgerWriterIdPattern = RegExp(r'^writer_[A-Za-z0-9_-]{10,40}$');

class LedgerSyncException implements Exception {
  const LedgerSyncException(this.message);

  final String message;

  @override
  String toString() => message;
}

class PendingWritesException extends LedgerSyncException {
  const PendingWritesException(super.message);
}

class PendingWrite {
  const PendingWrite({
    required this.id,
    required this.path,
    required this.value,
    required this.createdAt,
    required this.reason,
  });

  final String id;
  final String path;
  final dynamic value;
  final int createdAt;
  final String reason;

  factory PendingWrite.fromJson(Map<String, dynamic> json) => PendingWrite(
    id: '${json['id'] ?? ''}',
    path: '${json['path'] ?? ''}',
    value: json['value'],
    createdAt: _asInt(json['createdAt']),
    reason: '${json['reason'] ?? 'local-mutation'}',
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'id': id,
    'path': path,
    'value': value,
    'createdAt': createdAt,
    'reason': reason,
  };
}

class SyncEnvelope {
  const SyncEnvelope({
    required this.state,
    required this.outbox,
    required this.changeToken,
    required this.revision,
    required this.tableRevisions,
    required this.tableClocks,
    required this.lastFullAuditAt,
  });

  factory SyncEnvelope.empty() => SyncEnvelope(
    state: LedgerCodec.emptyState(),
    outbox: const <PendingWrite>[],
    changeToken: '',
    revision: 0,
    tableRevisions: const <String, int>{},
    tableClocks: const <String, Map<String, String>>{},
    lastFullAuditAt: 0,
  );

  factory SyncEnvelope.fromJson(Map<String, dynamic> json) {
    final List<PendingWrite> writes = <PendingWrite>[];
    final dynamic rawOutbox = json['outbox'];
    if (rawOutbox is List) {
      for (final dynamic item in rawOutbox) {
        if (item is Map) {
          final PendingWrite write = PendingWrite.fromJson(
            LedgerCodec.objectMap(item),
          );
          if (write.id.isNotEmpty && write.path.isNotEmpty) {
            writes.add(write);
          }
        }
      }
    }
    final Map<String, int> tableRevisions = <String, int>{};
    for (final MapEntry<String, dynamic> entry in LedgerCodec.objectMap(
      json['tableRevisions'],
    ).entries) {
      final int value = _asInt(entry.value);
      if (value > 0) tableRevisions[entry.key] = value;
    }
    return SyncEnvelope(
      state: LedgerCodec.normalizeState(json['state']),
      outbox: writes,
      changeToken: '${json['changeToken'] ?? ''}',
      revision: _asInt(json['revision']),
      tableRevisions: tableRevisions,
      tableClocks: LedgerCodec.canonicalTableClocks(json['tableClocks']),
      lastFullAuditAt: _asInt(json['lastFullAuditAt']),
    );
  }

  final Map<String, dynamic> state;
  final List<PendingWrite> outbox;
  final String changeToken;
  final int revision;
  final Map<String, int> tableRevisions;
  final Map<String, Map<String, String>> tableClocks;
  final int lastFullAuditAt;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'version': 1,
    'state': state,
    'outbox': outbox.map((PendingWrite write) => write.toJson()).toList(),
    'changeToken': changeToken,
    'revision': revision,
    'tableRevisions': tableRevisions,
    'tableClocks': tableClocks,
    'lastFullAuditAt': lastFullAuditAt,
  };
}

class LedgerCodec {
  LedgerCodec._();

  static Map<String, dynamic> emptyState() => <String, dynamic>{
    'milkDB': <String, dynamic>{},
    'udharDB': <Map<String, dynamic>>[],
    'expenseDB': <Map<String, dynamic>>[],
    'salaryDB': <String, dynamic>{},
    'diaryDB': <Map<String, dynamic>>[],
    'projectDB': <String, dynamic>{},
  };

  static Map<String, dynamic> objectMap(dynamic value) {
    if (value is! Map) return <String, dynamic>{};
    return value.map<String, dynamic>(
      (dynamic key, dynamic item) => MapEntry<String, dynamic>('$key', item),
    );
  }

  static Map<String, Map<String, String>> canonicalTableClocks(dynamic value) {
    final Map<String, Map<String, String>> result =
        <String, Map<String, String>>{};
    final Map<String, dynamic> tables = objectMap(value);
    for (final String root in ledgerRoots) {
      final Map<String, dynamic> rawWriters = objectMap(tables[root]);
      final Map<String, String> writers = <String, String>{};
      for (final String writer in rawWriters.keys.toList()..sort()) {
        if (!ledgerWriterIdPattern.hasMatch(writer)) continue;
        final String token = '${rawWriters[writer] ?? ''}';
        if (token.isNotEmpty && token.length <= 120) {
          writers[writer] = token;
        }
      }
      if (writers.isNotEmpty) result[root] = writers;
    }
    return result;
  }

  static dynamic clone(dynamic value) {
    if (value == null || value is String || value is bool || value is num) {
      return value;
    }
    return jsonDecode(jsonEncode(value));
  }

  static List<Map<String, dynamic>> canonicalList(dynamic value) {
    final List<Map<String, dynamic>> result = <Map<String, dynamic>>[];
    if (value is List) {
      for (int index = 0; index < value.length; index++) {
        final dynamic item = value[index];
        if (item is! Map) continue;
        final Map<String, dynamic> row = objectMap(clone(item));
        final String candidate = '${row['id'] ?? row['key'] ?? ''}';
        final String id = candidate.isEmpty ? '$index' : candidate;
        row['id'] = id;
        row['key'] = id;
        result.add(row);
      }
      return result;
    }
    if (value is Map) {
      for (final MapEntry<String, dynamic> entry in objectMap(value).entries) {
        if (entry.value is! Map) continue;
        final Map<String, dynamic> row = objectMap(clone(entry.value));
        // The RTDB child key is the only identity that can be used to update
        // or delete this row. Trusting an embedded legacy `id` can target a
        // different path and make the original record reappear on reconcile.
        row['id'] = entry.key;
        row['key'] = entry.key;
        result.add(row);
      }
    }
    return result;
  }

  static Map<String, dynamic> normalizeState(dynamic value) {
    final Map<String, dynamic> source = objectMap(value);
    final Map<String, dynamic> state = emptyState();
    for (final String root in _listRoots) {
      state[root] = canonicalList(source[root]);
    }
    for (final String root in _groupedRoots) {
      final Map<String, dynamic> profiles = <String, dynamic>{};
      for (final MapEntry<String, dynamic> entry in objectMap(
        source[root],
      ).entries) {
        if (entry.value is! Map) continue;
        final Map<String, dynamic> profile = objectMap(clone(entry.value));
        profile['records'] = canonicalList(profile['records']);
        profiles[entry.key] = profile;
      }
      state[root] = profiles;
    }
    return state;
  }

  static bool applyPath(
    Map<String, dynamic> state,
    String path,
    dynamic value,
  ) {
    final List<String> parts = path.split('/');
    if (parts.isEmpty || !ledgerRoots.contains(parts.first)) return false;
    final String root = parts.first;

    if (_listRoots.contains(root)) {
      if (parts.length == 1) {
        state[root] = canonicalList(value);
        return true;
      }
      if (parts.length != 2) return false;
      final String id = parts[1];
      final List<Map<String, dynamic>> rows = canonicalList(state[root]);
      final int index = rows.indexWhere(
        (Map<String, dynamic> row) => '${row['id'] ?? row['key']}' == id,
      );
      if (value == null) {
        if (index >= 0) rows.removeAt(index);
      } else {
        if (value is! Map) return false;
        final Map<String, dynamic> row = objectMap(clone(value));
        row['id'] = id;
        row.putIfAbsent('key', () => id);
        if (index >= 0) {
          rows[index] = row;
        } else {
          rows.insert(0, row);
        }
      }
      state[root] = rows;
      return true;
    }

    final Map<String, dynamic> profiles = objectMap(state[root]);
    if (parts.length == 1) {
      state[root] = normalizeState(<String, dynamic>{root: value})[root];
      return true;
    }
    final String name = parts[1];
    if (parts.length == 2) {
      if (value == null) {
        profiles.remove(name);
      } else {
        if (value is! Map) return false;
        final Map<String, dynamic> profile = objectMap(clone(value));
        profile['records'] = canonicalList(profile['records']);
        profiles[name] = profile;
      }
      state[root] = profiles;
      return true;
    }

    final dynamic rawProfile = profiles[name];
    // A concurrent first-time profile can arrive as safe child deltas. Create
    // the local shell lazily for non-null child writes so those deltas apply
    // without forcing a destructive whole-parent fallback. Deleting a child of
    // a profile that does not exist remains an idempotent no-op.
    if (rawProfile is! Map && value == null) return true;
    final Map<String, dynamic> profile = rawProfile is Map
        ? objectMap(rawProfile)
        : <String, dynamic>{'records': <dynamic>[]};
    if (parts.length == 3) {
      if (parts[2] == 'records') {
        profile['records'] = canonicalList(value);
      } else if (value == null) {
        profile.remove(parts[2]);
      } else {
        profile[parts[2]] = clone(value);
      }
      profiles[name] = profile;
      state[root] = profiles;
      return true;
    }
    if (parts.length != 4 || parts[2] != 'records') return false;

    final String id = parts[3];
    final List<Map<String, dynamic>> records = canonicalList(
      profile['records'],
    );
    final int index = records.indexWhere(
      (Map<String, dynamic> row) => '${row['id'] ?? row['key']}' == id,
    );
    if (value == null) {
      if (index >= 0) records.removeAt(index);
    } else {
      if (value is! Map) return false;
      final Map<String, dynamic> row = objectMap(clone(value));
      row['id'] = id;
      row.putIfAbsent('key', () => id);
      if (index >= 0) {
        records[index] = row;
      } else {
        records.insert(0, row);
      }
    }
    profile['records'] = records;
    profiles[name] = profile;
    state[root] = profiles;
    return true;
  }
}

class DiarySourceVersion {
  const DiarySourceVersion({required this.revision, required this.clockHash});

  factory DiarySourceVersion.fromMetadata(dynamic value) {
    final Map<String, dynamic> metadata = LedgerCodec.objectMap(value);
    final Map<String, dynamic> tables = LedgerCodec.objectMap(
      metadata['tables'],
    );
    final Map<String, Map<String, String>> clocks =
        LedgerCodec.canonicalTableClocks(metadata['tableClocks']);
    return DiarySourceVersion(
      revision: _asInt(tables['diaryDB']),
      clockHash: LedgerDeltaPolicy.tableClockHash(
        clocks['diaryDB'] ?? const <String, String>{},
      ),
    );
  }

  final int revision;
  final String clockHash;

  String get cacheKey => '$revision:$clockHash';
}

class DiaryReadConsistency {
  DiaryReadConsistency._();

  static bool sameSource(DiarySourceVersion left, DiarySourceVersion right) =>
      left.cacheKey == right.cacheKey;

  static bool canApplyProjectedMonth({
    required DiaryProjectionMetadata projection,
    required DiarySourceVersion requestedSource,
    required DiarySourceVersion currentSource,
  }) =>
      projection.matchesSource(requestedSource) &&
      sameSource(requestedSource, currentSource);
}

class DiaryProjectionMetadata {
  const DiaryProjectionMetadata({
    required this.schemaVersion,
    required this.ready,
    required this.sourceRevision,
    required this.sourceClockHash,
  });

  const DiaryProjectionMetadata.unavailable()
    : schemaVersion = 0,
      ready = false,
      sourceRevision = -1,
      sourceClockHash = '';

  factory DiaryProjectionMetadata.fromValue(dynamic value) {
    final Map<String, dynamic> map = LedgerCodec.objectMap(value);
    return DiaryProjectionMetadata(
      schemaVersion: _asInt(map['schemaVersion']),
      ready: map['ready'] == true,
      sourceRevision: _asInt(map['sourceRevision']),
      sourceClockHash: '${map['sourceClockHash'] ?? ''}',
    );
  }

  static const int supportedSchemaVersion = 2;

  final int schemaVersion;
  final bool ready;
  final int sourceRevision;
  final String sourceClockHash;

  bool matchesSource(DiarySourceVersion source) =>
      ready &&
      schemaVersion == supportedSchemaVersion &&
      sourceRevision == source.revision &&
      sourceClockHash == source.clockHash;
}

class DiaryMonthCodec {
  DiaryMonthCodec._();

  static const String invalidPeriodKey = '_invalid';
  static final RegExp _periodPattern = RegExp(r'^(\d{4})-(\d{2})$');

  static String periodKey(int year, int month) =>
      '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';

  static DateTime? parsePeriod(dynamic value) {
    final RegExpMatch? match = _periodPattern.firstMatch('$value');
    if (match == null) return null;
    final int year = int.parse(match.group(1)!);
    final int month = int.parse(match.group(2)!);
    if (year < 1 || month < 1 || month > 12) return null;
    return DateTime(year, month);
  }

  static String? periodForRecord(dynamic value) {
    final DateTime? date = LedgerMath.strictDate(
      LedgerCodec.objectMap(value)['date'],
    );
    return date == null ? null : periodKey(date.year, date.month);
  }

  static List<DateTime> periodsFromIndex(dynamic value) {
    final Set<String> keys = <String>{};
    for (final dynamic raw in LedgerCodec.objectMap(value).values) {
      final String key = raw is Map
          ? '${LedgerCodec.objectMap(raw)['p'] ?? ''}'
          : '$raw';
      if (parsePeriod(key) != null) keys.add(key);
    }
    final List<DateTime> result = keys
        .map(parsePeriod)
        .whereType<DateTime>()
        .toList(growable: false);
    result.sort((DateTime a, DateTime b) => b.compareTo(a));
    return result;
  }

  static List<Map<String, dynamic>> decodeMonthEntries(
    dynamic value, {
    required int year,
    required int month,
  }) {
    final String expectedPeriod = periodKey(year, month);
    final List<Map<String, dynamic>> result = <Map<String, dynamic>>[];
    for (final Map<String, dynamic> raw in LedgerCodec.canonicalList(value)) {
      if (raw['_deleted'] == true || '${raw['_period']}' != expectedPeriod) {
        continue;
      }
      final Map<String, dynamic> entry = _publicEntry(raw);
      if (LedgerMath.strictDate(entry['date']) == null) continue;
      result.add(entry);
    }
    return result;
  }

  static List<Map<String, dynamic>> decodeInvalidEntries(dynamic value) {
    final List<Map<String, dynamic>> result = <Map<String, dynamic>>[];
    for (final Map<String, dynamic> raw in LedgerCodec.canonicalList(value)) {
      if (raw['_deleted'] == true || '${raw['_period']}' != invalidPeriodKey) {
        continue;
      }
      final Map<String, dynamic> entry = _publicEntry(raw);
      if (LedgerMath.strictDate(entry['date']) == null) result.add(entry);
    }
    return result;
  }

  static Map<String, dynamic> _publicEntry(Map<String, dynamic> raw) =>
      Map<String, dynamic>.from(raw)
        ..remove('_period')
        ..remove('_sourceHash')
        ..remove('_version')
        ..remove('_deleted')
        ..remove('_pending')
        ..remove('_seen');

  static void replaceMonth(
    Map<String, dynamic> state, {
    required int year,
    required int month,
    required List<Map<String, dynamic>> entries,
  }) {
    final String target = periodKey(year, month);
    final Map<String, Map<String, dynamic>> byId =
        <String, Map<String, dynamic>>{};
    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['diaryDB'],
    )) {
      if (periodForRecord(row) == target) continue;
      byId['${row['id'] ?? row['key']}'] = row;
    }
    for (final Map<String, dynamic> row in entries) {
      if (periodForRecord(row) != target) continue;
      final String id = '${row['id'] ?? row['key'] ?? ''}';
      if (id.isEmpty) continue;
      byId[id] = LedgerCodec.objectMap(LedgerCodec.clone(row));
    }
    state['diaryDB'] = byId.values.toList(growable: false);
  }

  static void replaceInvalidEntries(
    Map<String, dynamic> state,
    List<Map<String, dynamic>> entries,
  ) {
    final Map<String, Map<String, dynamic>> byId =
        <String, Map<String, dynamic>>{};
    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['diaryDB'],
    )) {
      if (periodForRecord(row) == null) continue;
      byId['${row['id'] ?? row['key']}'] = row;
    }
    for (final Map<String, dynamic> row in entries) {
      if (periodForRecord(row) != null) continue;
      final String id = '${row['id'] ?? row['key'] ?? ''}';
      if (id.isEmpty) continue;
      byId[id] = LedgerCodec.objectMap(LedgerCodec.clone(row));
    }
    state['diaryDB'] = byId.values.toList(growable: false);
  }
}

class OutboxPlanner {
  OutboxPlanner._();

  // Keep multi-location SDK writes comfortably below the transport ceiling,
  // including the sync metadata that is added immediately before upload.
  static const int maxBatchBytes = 12 * 1024 * 1024;

  static bool overlaps(String left, String right) =>
      left == right || left.startsWith('$right/') || right.startsWith('$left/');

  static List<PendingWrite> nextCompatibleBatch(
    List<PendingWrite> queue, {
    int limit = ledgerDeltaPathLimit,
    int maxBytes = maxBatchBytes,
  }) {
    final List<PendingWrite> batch = <PendingWrite>[];
    int batchBytes = 0;
    for (final PendingWrite write in queue) {
      if (batch.length >= limit) break;
      if (batch.any(
        (PendingWrite existing) => overlaps(existing.path, write.path),
      )) {
        break;
      }
      final int writeBytes = estimatedMutationBytes(write);
      if (batch.isNotEmpty && batchBytes + writeBytes > maxBytes) break;
      if (batch.isEmpty && writeBytes > maxBytes) {
        throw LedgerSyncException(
          'A pending Firebase write exceeds the safe batch size.',
        );
      }
      batch.add(write);
      batchBytes += writeBytes;
    }
    return batch;
  }

  static int estimatedMutationBytes(PendingWrite write) => utf8
      .encode(jsonEncode(<String, dynamic>{write.path: write.value}))
      .length;

  // Stable across process restarts because PendingWrite IDs are durable in the
  // Hive envelope. Firebase stores this digest atomically with the data batch,
  // allowing reconcile to distinguish "committed but local ack crashed" from
  // a genuinely unsent pending mutation.
  static String batchId(Iterable<PendingWrite> batch) => crypto.sha256
      .convert(
        utf8.encode(
          jsonEncode(batch.map((PendingWrite write) => write.id).toList()),
        ),
      )
      .toString();

  static void addCompacted(List<PendingWrite> queue, PendingWrite next) {
    // A newer parent replacement/delete semantically dominates every older
    // pending descendant. Keep the inverse ordering intact: a newer child write
    // after a parent mutation may intentionally recreate/modify that child.
    final String descendantPrefix = '${next.path}/';
    queue.removeWhere(
      (PendingWrite pending) =>
          pending.path == next.path ||
          pending.path.startsWith(descendantPrefix),
    );
    queue.add(next);
  }
}

class LedgerFirebasePolicy {
  LedgerFirebasePolicy._();

  static const int maxPathBytes = 768;
  static const int maxRelativeDepth = 29;
  static const int maxValueNesting = 24;
  static const int maxMutationBytes = 8 * 1024 * 1024;
  static final RegExp _forbiddenKey = RegExp(r'[.#$\[\]/\u0000-\u001F\u007F]');
  static const Set<String> _unsafeObjectKeys = <String>{
    '__proto__',
    'constructor',
    'prototype',
  };

  static String validatePath(String rawPath) {
    final String path = rawPath
        .trim()
        .replaceAll(RegExp(r'^/+|/+$'), '')
        .replaceAll(RegExp(r'/+'), '/');
    final List<String> parts = path.split('/');
    if (path.isEmpty || !ledgerRoots.contains(parts.first)) {
      throw LedgerSyncException('Unsafe Firebase path: $rawPath');
    }
    if (parts.any(
      (String part) =>
          part.isEmpty ||
          part == '.' ||
          part == '..' ||
          part == '_syncMeta' ||
          part.length > 180 ||
          _unsafeObjectKeys.contains(part) ||
          _forbiddenKey.hasMatch(part),
    )) {
      throw LedgerSyncException('Unsafe Firebase path: $rawPath');
    }
    _validateLocation(path);
    if (_listRoots.contains(parts.first) && parts.length > 2) {
      throw LedgerSyncException('Unsupported list path: $rawPath');
    }
    if (_groupedRoots.contains(parts.first)) {
      // Grouped profiles support metadata leaf writes as well as record writes.
      // _groupedProfileDiff deliberately decomposes parent replacements into
      // these leaf paths so concurrent records are never clobbered.
      final bool valid =
          parts.length <= 3 || (parts.length == 4 && parts[2] == 'records');
      if (!valid) {
        throw LedgerSyncException('Unsupported profile path: $rawPath');
      }
    }
    return path;
  }

  static dynamic sanitizeValue(dynamic value, String path) {
    final dynamic sanitized = _sanitize(value, path, 0);
    final int bytes = utf8.encode(jsonEncode(sanitized)).length;
    if (bytes > maxMutationBytes) {
      throw LedgerSyncException('Firebase value is too large at $path');
    }
    return sanitized;
  }

  static dynamic _sanitize(dynamic value, String path, int nesting) {
    _validateLocation(path);
    if (nesting > maxValueNesting) {
      throw LedgerSyncException('Firebase value is nested too deeply at $path');
    }
    if (value == null || value is bool || value is String) return value;
    if (value is num) {
      if (!value.isFinite) {
        throw LedgerSyncException('Invalid number at $path');
      }
      return value;
    }
    if (value is List) {
      return List<dynamic>.generate(
        value.length,
        (int index) => _sanitize(value[index], '$path/$index', nesting + 1),
        growable: false,
      );
    }
    if (value is Map) {
      final Map<String, dynamic> result = <String, dynamic>{};
      for (final MapEntry<String, dynamic> entry in LedgerCodec.objectMap(
        value,
      ).entries) {
        if (entry.key.isEmpty ||
            entry.key.length > 180 ||
            _unsafeObjectKeys.contains(entry.key) ||
            _forbiddenKey.hasMatch(entry.key)) {
          throw LedgerSyncException('Invalid field name at $path');
        }
        final String childPath = '$path/${entry.key}';
        result[entry.key] = _sanitize(entry.value, childPath, nesting + 1);
      }
      return result;
    }
    throw LedgerSyncException('Unsupported value at $path');
  }

  static void _validateLocation(String path) {
    if (path.split('/').length > maxRelativeDepth ||
        utf8.encode(path).length > maxPathBytes) {
      throw LedgerSyncException('Firebase path exceeds safe limits: $path');
    }
  }
}

class SyncAuditPolicy {
  SyncAuditPolicy._();

  static bool isDue({
    required int now,
    required int lastFullAuditAt,
    required Duration interval,
  }) =>
      lastFullAuditAt <= 0 ||
      lastFullAuditAt > now ||
      now - lastFullAuditAt >= interval.inMilliseconds;
}

class SyncConnectionPolicy {
  SyncConnectionPolicy._();

  /// Firebase `get()` may fall back to its local persistence cache. Network
  /// reconciliation is therefore safe only after `.info/connected` has
  /// positively confirmed this client is connected, not while it is unknown.
  static bool canContactServer(bool? connected) => connected == true;
}

/// Keeps the sync metadata small while allowing another device to fetch only
/// the records touched by a write whose value is too large for `deltaWrites`.
/// Older clients can ignore this optional field and keep using table reads.
class DeltaPathCodec {
  DeltaPathCodec._();

  static const int maxPaths = ledgerDeltaPathLimit;
  static const int maxEncodedLength = 1800;

  static String? encode(Iterable<String> paths) {
    final List<String> unique = paths.toSet().toList(growable: false);
    if (unique.isEmpty || unique.length > maxPaths) return null;
    final String encoded = jsonEncode(unique);
    return encoded.length <= maxEncodedLength ? encoded : null;
  }

  static List<String> decode(dynamic value) {
    if (value is! String || value.isEmpty || value.length > maxEncodedLength) {
      return const <String>[];
    }
    try {
      final dynamic decoded = jsonDecode(value);
      if (decoded is! List || decoded.isEmpty || decoded.length > maxPaths) {
        return const <String>[];
      }
      final List<String> paths = <String>[];
      for (final dynamic item in decoded) {
        if (item is! String || item.isEmpty || paths.contains(item)) {
          return const <String>[];
        }
        paths.add(item);
      }
      return paths;
    } catch (_) {
      return const <String>[];
    }
  }
}

class LedgerDeltaPolicy {
  LedgerDeltaPolicy._();

  static String tableClockHash(Map<String, String> clocks) {
    final Map<String, String> canonical = <String, String>{};
    final List<String> writers = clocks.keys.toList()..sort();
    for (final String writer in writers) {
      final String token = clocks[writer] ?? '';
      if (ledgerWriterIdPattern.hasMatch(writer) &&
          token.isNotEmpty &&
          token.length <= 120) {
        canonical[writer] = token;
      }
    }
    return crypto.sha256.convert(utf8.encode(jsonEncode(canonical))).toString();
  }

  static Set<String> changedRoots({
    required Map<String, int> remoteRevisions,
    required Map<String, int> localRevisions,
    required Map<String, Map<String, String>> remoteClocks,
    required Map<String, Map<String, String>> localClocks,
  }) {
    final Set<String> changed = <String>{};
    for (final String root in ledgerRoots) {
      final Map<String, String> remote =
          remoteClocks[root] ?? const <String, String>{};
      final Map<String, String> local =
          localClocks[root] ?? const <String, String>{};
      if (remote.isNotEmpty || local.isNotEmpty) {
        if (!_sameWriterClocks(remote, local)) changed.add(root);
      } else {
        final int remoteRevision = remoteRevisions[root] ?? 0;
        if (remoteRevision > 0 &&
            remoteRevision != (localRevisions[root] ?? 0)) {
          changed.add(root);
        }
      }
    }
    return changed;
  }

  static bool canApplyDelta({
    required String remoteWriterId,
    required String predecessorToken,
    required String localToken,
    required Set<String> changedRoots,
    required Set<String> deltaRoots,
    required Map<String, Map<String, String>> remoteClocks,
    required Map<String, Map<String, String>> localClocks,
  }) {
    if (localToken.isEmpty || predecessorToken != localToken) return false;
    if (!ledgerWriterIdPattern.hasMatch(remoteWriterId)) return false;
    if (changedRoots.isEmpty || !changedRoots.every(deltaRoots.contains)) {
      return false;
    }
    for (final String root in changedRoots) {
      final Map<String, String> remote =
          remoteClocks[root] ?? const <String, String>{};
      final Map<String, String> local =
          localClocks[root] ?? const <String, String>{};
      final Set<String> writers = <String>{...remote.keys, ...local.keys};
      final List<String> changedWriters = writers
          .where((String writer) => remote[writer] != local[writer])
          .toList(growable: false);
      if (changedWriters.length != 1 ||
          changedWriters.single != remoteWriterId) {
        return false;
      }
    }
    return true;
  }

  static bool _sameWriterClocks(
    Map<String, String> left,
    Map<String, String> right,
  ) {
    if (left.length != right.length) return false;
    for (final MapEntry<String, String> entry in left.entries) {
      if (right[entry.key] != entry.value) return false;
    }
    return true;
  }
}

class MilkTotals {
  const MilkTotals({
    required this.givenKg,
    required this.takenKg,
    required this.givenAmount,
    required this.takenAmount,
  });

  final double givenKg;
  final double takenKg;
  final double givenAmount;
  final double takenAmount;

  double get netKg => _cleanZero(givenKg - takenKg);
  double get netAmount => _cleanZero(givenAmount - takenAmount);
}

class DashboardTotals {
  const DashboardTotals({
    required this.toReceive,
    required this.toPay,
    required this.monthExpense,
    required this.monthProfit,
    required this.creditReceive,
    required this.creditPay,
  });

  final double toReceive;
  final double toPay;
  final double monthExpense;
  final double monthProfit;
  final double creditReceive;
  final double creditPay;
}

class PartyBalance {
  const PartyBalance({
    required this.name,
    required this.milk,
    required this.credit,
  });

  final String name;
  final double milk;
  final double credit;

  double get net => _cleanZero(milk + credit);
}

class CreditPartySummary {
  const CreditPartySummary({
    required this.name,
    required this.net,
    required this.lastDate,
  });

  final String name;
  final double net;
  final String lastDate;
}

class ExpenseCategorySummary {
  const ExpenseCategorySummary({
    required this.category,
    required this.monthTotal,
    required this.lastDate,
  });

  final String category;
  final double monthTotal;
  final String lastDate;
}

/// A single, immutable calculation pass over one ledger state and month.
///
/// UI rebuilds also happen for connection, retry, theme and outbox changes.
/// Keeping these values together lets [LedgerSyncService] reuse the exact same
/// projection until either the state identity or the calendar month changes.
class LedgerProjection {
  const LedgerProjection._({
    required this.month,
    required this.year,
    required this.dashboard,
    required this.partyBalances,
    required this.milkTotalsByProfile,
    required this.salaryNetByProfile,
    required this.creditParties,
    required this.expenseCategories,
    required this.businessRecordCounts,
    required this.milkLifetimeNet,
    required this.creditLifetimeNet,
    required this.salaryMonthNet,
    required this.expenseMonthTotal,
  });

  final int month;
  final int year;
  final DashboardTotals dashboard;
  final List<PartyBalance> partyBalances;
  final Map<String, MilkTotals> milkTotalsByProfile;
  final Map<String, double> salaryNetByProfile;
  final List<CreditPartySummary> creditParties;
  final List<ExpenseCategorySummary> expenseCategories;
  final Map<String, int> businessRecordCounts;
  final double milkLifetimeNet;
  final double creditLifetimeNet;
  final double salaryMonthNet;
  final double expenseMonthTotal;

  factory LedgerProjection.fromState(
    Map<String, dynamic> state, {
    required int month,
    required int year,
  }) {
    final Map<String, MilkTotals> milkTotalsByProfile = <String, MilkTotals>{};
    final Map<String, double> salaryNetByProfile = <String, double>{};
    final Map<String, double> partyMilk = <String, double>{};
    final Map<String, _CreditSummaryBuilder> partyCredit =
        <String, _CreditSummaryBuilder>{};
    final Map<String, String> partyDisplayNames = <String, String>{};
    final Map<String, _ExpenseSummaryBuilder> expenseByCategory =
        <String, _ExpenseSummaryBuilder>{};
    final Map<String, int> businessRecordCounts = <String, int>{};

    double revenue = 0;
    double expense = 0;
    double receive = 0;
    double pay = 0;
    double creditReceive = 0;
    double creditPay = 0;
    double milkLifetimeNet = 0;
    double creditLifetimeNet = 0;
    double salaryMonthNet = 0;
    double expenseMonthTotal = 0;

    for (final MapEntry<String, dynamic> entry in LedgerCodec.objectMap(
      state['milkDB'],
    ).entries) {
      final MilkTotals lifetime = LedgerMath.milkTotals(entry.value);
      final MilkTotals monthly = LedgerMath.milkTotals(
        entry.value,
        month: month,
        year: year,
      );
      milkTotalsByProfile[entry.key] = lifetime;
      milkLifetimeNet += lifetime.netAmount;

      if (monthly.netAmount >= 0) {
        revenue += monthly.netAmount;
      } else {
        expense += monthly.netAmount.abs();
      }
      if (lifetime.netAmount >= 0) {
        receive += lifetime.netAmount;
      } else {
        pay += lifetime.netAmount.abs();
      }

      final String partyName = LedgerMath.cleanName(entry.key);
      if (partyName.isNotEmpty) {
        final String partyKey = partyName.toLowerCase();
        partyDisplayNames.putIfAbsent(partyKey, () => partyName);
        partyMilk[partyKey] = (partyMilk[partyKey] ?? 0) + lifetime.netAmount;
      }
    }

    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['udharDB'],
    )) {
      final double signed = LedgerMath.creditSigned(row);
      creditLifetimeNet += signed;
      final String partyName = LedgerMath.cleanName(row['name']);
      if (partyName.isEmpty) continue;
      final String partyKey = partyName.toLowerCase();
      partyDisplayNames.putIfAbsent(partyKey, () => partyName);
      final _CreditSummaryBuilder builder = partyCredit.putIfAbsent(
        partyKey,
        () => _CreditSummaryBuilder(partyDisplayNames[partyKey]!),
      );
      builder.net += signed;
      final String rowDate = '${row['date'] ?? ''}';
      if (rowDate.compareTo(builder.lastDate) > 0) {
        builder.lastDate = rowDate;
      }
    }

    for (final _CreditSummaryBuilder builder in partyCredit.values) {
      final double net = _cleanZero(builder.net);
      if (net > 0) {
        receive += net;
        creditReceive += net;
      } else if (net < 0) {
        pay += net.abs();
        creditPay += net.abs();
      }
    }

    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['expenseDB'],
    )) {
      final String cleanedCategory = LedgerMath.cleanKey(row['category']);
      final String category = cleanedCategory.isEmpty
          ? 'Other'
          : cleanedCategory;
      final _ExpenseSummaryBuilder builder = expenseByCategory.putIfAbsent(
        category,
        () => _ExpenseSummaryBuilder(category),
      );
      if (LedgerMath.inMonth(row, month, year)) {
        final double amount = LedgerMath.number(row['amount']).abs();
        builder.monthTotal += amount;
        expenseMonthTotal += amount;
        expense += amount;
      }
      final String rowDate = '${row['date'] ?? ''}';
      if (rowDate.compareTo(builder.lastDate) > 0) {
        builder.lastDate = rowDate;
      }
    }

    for (final MapEntry<String, dynamic> entry in LedgerCodec.objectMap(
      state['salaryDB'],
    ).entries) {
      final double net = LedgerMath.salaryNet(entry.value, month, year);
      salaryNetByProfile[entry.key] = net;
      salaryMonthNet += net;
      if (net >= 0) {
        revenue += net;
      } else {
        expense += net.abs();
      }
    }

    for (final MapEntry<String, dynamic> entry in LedgerCodec.objectMap(
      state['projectDB'],
    ).entries) {
      businessRecordCounts[entry.key] = LedgerCodec.canonicalList(
        LedgerCodec.objectMap(entry.value)['records'],
      ).length;
    }

    final Set<String> partyNames = <String>{
      ...partyMilk.keys,
      ...partyCredit.keys,
    };
    final List<PartyBalance> partyBalances = partyNames
        .map(
          (String key) => PartyBalance(
            name: partyDisplayNames[key] ?? partyCredit[key]?.name ?? key,
            milk: partyMilk[key] ?? 0,
            credit: partyCredit[key]?.net ?? 0,
          ),
        )
        .toList();
    partyBalances.sort((PartyBalance a, PartyBalance b) {
      final int byAbsolute = b.net.abs().compareTo(a.net.abs());
      return byAbsolute != 0 ? byAbsolute : a.name.compareTo(b.name);
    });

    final List<CreditPartySummary> creditParties = partyCredit.values
        .map(
          (_CreditSummaryBuilder builder) => CreditPartySummary(
            name: builder.name,
            net: builder.net,
            lastDate: builder.lastDate,
          ),
        )
        .toList();
    creditParties.sort((CreditPartySummary a, CreditPartySummary b) {
      final int byDate = b.lastDate.compareTo(a.lastDate);
      return byDate != 0 ? byDate : a.name.compareTo(b.name);
    });

    final List<ExpenseCategorySummary> expenseCategories = expenseByCategory
        .values
        .map(
          (_ExpenseSummaryBuilder builder) => ExpenseCategorySummary(
            category: builder.category,
            monthTotal: builder.monthTotal,
            lastDate: builder.lastDate,
          ),
        )
        .toList();
    expenseCategories.sort((
      ExpenseCategorySummary a,
      ExpenseCategorySummary b,
    ) {
      final int byLatest = b.lastDate.compareTo(a.lastDate);
      return byLatest != 0 ? byLatest : a.category.compareTo(b.category);
    });

    return LedgerProjection._(
      month: month,
      year: year,
      dashboard: DashboardTotals(
        toReceive: receive,
        toPay: pay,
        monthExpense: expense,
        monthProfit: revenue - expense,
        creditReceive: creditReceive,
        creditPay: creditPay,
      ),
      partyBalances: List<PartyBalance>.unmodifiable(partyBalances),
      milkTotalsByProfile: Map<String, MilkTotals>.unmodifiable(
        milkTotalsByProfile,
      ),
      salaryNetByProfile: Map<String, double>.unmodifiable(salaryNetByProfile),
      creditParties: List<CreditPartySummary>.unmodifiable(creditParties),
      expenseCategories: List<ExpenseCategorySummary>.unmodifiable(
        expenseCategories,
      ),
      businessRecordCounts: Map<String, int>.unmodifiable(businessRecordCounts),
      milkLifetimeNet: milkLifetimeNet,
      creditLifetimeNet: creditLifetimeNet,
      salaryMonthNet: salaryMonthNet,
      expenseMonthTotal: expenseMonthTotal,
    );
  }
}

class _CreditSummaryBuilder {
  _CreditSummaryBuilder(this.name);

  final String name;
  double net = 0;
  String lastDate = '';
}

class _ExpenseSummaryBuilder {
  _ExpenseSummaryBuilder(this.category);

  final String category;
  double monthTotal = 0;
  String lastDate = '';
}

class LedgerMath {
  LedgerMath._();

  static const double defaultMilkRate = 55;
  static final RegExp _strictDatePattern = RegExp(
    r'^(\d{4})-(\d{2})-(\d{2})$',
  );

  static double number(dynamic value) {
    if (value is num) return value.isFinite ? value.toDouble() : 0;
    final double? parsed = double.tryParse('$value'.trim());
    return parsed != null && parsed.isFinite ? parsed : 0;
  }

  static DateTime? date(dynamic value) {
    final String raw = '${value ?? ''}'.trim();
    if (raw.isEmpty) return null;
    return DateTime.tryParse(raw);
  }

  static DateTime? strictDate(dynamic value) {
    final String raw = '${value ?? ''}'.trim();
    final RegExpMatch? match = _strictDatePattern.firstMatch(raw);
    if (match == null) return null;
    final int year = int.parse(match.group(1)!);
    final int month = int.parse(match.group(2)!);
    final int day = int.parse(match.group(3)!);
    final DateTime? parsed = DateTime.tryParse(raw);
    if (parsed == null ||
        parsed.year != year ||
        parsed.month != month ||
        parsed.day != day) {
      return null;
    }
    return parsed;
  }

  static bool inMonth(dynamic record, int month, int year) {
    final Map<String, dynamic> row = LedgerCodec.objectMap(record);
    final DateTime? parsed = date(row['date']);
    return parsed != null && parsed.month == month && parsed.year == year;
  }

  /// Returns only the distinct year/month pairs that contain a valid record.
  /// The newest period is first so callers have a deterministic fallback when
  /// the requested period is empty or its final record has just been deleted.
  static List<DateTime> recordPeriods(dynamic records) {
    final Map<int, DateTime> periods = <int, DateTime>{};
    final Iterable<dynamic> source = records is List
        ? records
        : LedgerCodec.canonicalList(records);
    for (final dynamic value in source) {
      if (value is! Map) continue;
      final Map<String, dynamic> row = LedgerCodec.objectMap(value);
      final DateTime? parsed = date(row['date']);
      if (parsed == null) continue;
      final int key = parsed.year * 100 + parsed.month;
      periods[key] = DateTime(parsed.year, parsed.month);
    }
    final List<DateTime> result = periods.values.toList()
      ..sort((DateTime a, DateTime b) => b.compareTo(a));
    return result;
  }

  /// Keeps the requested period when it contains data. Otherwise it stays in
  /// the requested year when possible, then falls back to the latest period.
  /// No synthetic empty period is returned.
  static DateTime? resolveRecordPeriod(
    List<DateTime> periods, {
    required int month,
    required int year,
  }) {
    for (final DateTime period in periods) {
      if (period.month == month && period.year == year) return period;
    }
    for (final DateTime period in periods) {
      if (period.year == year) return period;
    }
    return periods.isEmpty ? null : periods.first;
  }

  static String milkFlow(dynamic record, dynamic customer) {
    final Map<String, dynamic> row = LedgerCodec.objectMap(record);
    final Map<String, dynamic> profile = LedgerCodec.objectMap(customer);
    final String raw =
        '${row['flow'] ?? row['milkFlow'] ?? row['direction'] ?? row['entryType'] ?? row['type'] ?? row['mode'] ?? ''}'
            .toLowerCase();
    const List<String> taken = <String>[
      'taken',
      'take',
      'minus',
      'debit',
      'pay',
      'paid',
      'dene_wala',
      'buyer',
      'negative',
      'out',
    ];
    const List<String> given = <String>[
      'given',
      'give',
      'plus',
      'credit',
      'receive',
      'received',
      'lene_wala',
      'seller',
      'positive',
      'in',
    ];
    if (taken.contains(raw)) return 'taken';
    if (given.contains(raw)) return 'given';
    return profile['type'] == 'dene_wala' ? 'taken' : 'given';
  }

  static double milkQuantity(dynamic record) {
    final Map<String, dynamic> row = LedgerCodec.objectMap(record);
    final double morning = number(row['morning']);
    final double evening = number(row['evening']);
    if (morning != 0 || evening != 0) return (morning + evening).abs();
    return number(
      row['kg'] ??
          row['qty'] ??
          row['quantity'] ??
          row['totalKg'] ??
          row['total'],
    ).abs();
  }

  static double milkRate(dynamic record, dynamic customer) {
    final Map<String, dynamic> row = LedgerCodec.objectMap(record);
    final Map<String, dynamic> profile = LedgerCodec.objectMap(customer);
    final double recordRate = number(row['rate']);
    if (recordRate > 0) return recordRate;
    final double profileRate = number(profile['rate']);
    return profileRate > 0 ? profileRate : defaultMilkRate;
  }

  static MilkTotals milkTotals(dynamic customer, {int? month, int? year}) {
    final Map<String, dynamic> profile = LedgerCodec.objectMap(customer);
    final List<Map<String, dynamic>> rows = LedgerCodec.canonicalList(
      profile['records'],
    );
    double givenKg = 0;
    double takenKg = 0;
    double givenAmount = 0;
    double takenAmount = 0;
    for (final Map<String, dynamic> row in rows) {
      if (month != null && year != null && !inMonth(row, month, year)) {
        continue;
      }
      final double quantity = milkQuantity(row);
      if (quantity == 0) continue;
      final double rate = milkRate(row, profile);
      if (milkFlow(row, profile) == 'taken') {
        takenKg += quantity;
        takenAmount += quantity * rate;
      } else {
        givenKg += quantity;
        givenAmount += quantity * rate;
      }
    }
    return MilkTotals(
      givenKg: givenKg,
      takenKg: takenKg,
      givenAmount: givenAmount,
      takenAmount: takenAmount,
    );
  }

  static double creditSigned(dynamic entry) {
    final Map<String, dynamic> row = LedgerCodec.objectMap(entry);
    final double amount = number(
      row['amount'] ??
          row['amt'] ??
          row['total'] ??
          row['price'] ??
          row['value'],
    ).abs();
    final String raw =
        '${row['type'] ?? row['entryType'] ?? row['flow'] ?? row['direction'] ?? row['status'] ?? row['mode'] ?? ''}'
            .toLowerCase();
    if (raw.contains('debit') ||
        raw.contains('dena') ||
        raw.contains('pay') ||
        raw.contains('paid') ||
        raw.contains('minus') ||
        raw.contains('negative') ||
        raw.contains('taken') ||
        raw == 'out') {
      return -amount;
    }
    return amount;
  }

  static double salaryNet(dynamic person, int month, int year) {
    final Map<String, dynamic> profile = LedgerCodec.objectMap(person);
    double total = 0;
    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      profile['records'],
    )) {
      if (inMonth(row, month, year)) total += number(row['amount']);
    }
    return profile['type'] == 'lene_wala' ? total : -total;
  }

  static DashboardTotals dashboard(
    Map<String, dynamic> state, {
    required int month,
    required int year,
  }) {
    double revenue = 0;
    double expense = 0;
    double receive = 0;
    double pay = 0;
    double creditReceive = 0;
    double creditPay = 0;

    for (final dynamic customer in LedgerCodec.objectMap(
      state['milkDB'],
    ).values) {
      final MilkTotals monthly = milkTotals(customer, month: month, year: year);
      final MilkTotals lifetime = milkTotals(customer);
      if (monthly.netAmount >= 0) {
        revenue += monthly.netAmount;
      } else {
        expense += monthly.netAmount.abs();
      }
      if (lifetime.netAmount >= 0) {
        receive += lifetime.netAmount;
      } else {
        pay += lifetime.netAmount.abs();
      }
    }

    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['expenseDB'],
    )) {
      if (inMonth(row, month, year)) expense += number(row['amount']).abs();
    }

    final Map<String, double> creditByParty = <String, double>{};
    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['udharDB'],
    )) {
      final String name = cleanName(row['name']);
      if (name.isEmpty) continue;
      final String partyKey = name.toLowerCase();
      creditByParty[partyKey] =
          (creditByParty[partyKey] ?? 0) + creditSigned(row);
    }
    for (final double raw in creditByParty.values) {
      final double net = _cleanZero(raw);
      if (net > 0) {
        receive += net;
        creditReceive += net;
      } else if (net < 0) {
        pay += net.abs();
        creditPay += net.abs();
      }
    }

    for (final dynamic person in LedgerCodec.objectMap(
      state['salaryDB'],
    ).values) {
      final double net = salaryNet(person, month, year);
      if (net >= 0) {
        revenue += net;
      } else {
        expense += net.abs();
      }
    }

    return DashboardTotals(
      toReceive: receive,
      toPay: pay,
      monthExpense: expense,
      monthProfit: revenue - expense,
      creditReceive: creditReceive,
      creditPay: creditPay,
    );
  }

  static List<PartyBalance> partyBalances(Map<String, dynamic> state) {
    final Map<String, double> milk = <String, double>{};
    final Map<String, double> credit = <String, double>{};
    final Map<String, String> displayNames = <String, String>{};
    for (final MapEntry<String, dynamic> entry in LedgerCodec.objectMap(
      state['milkDB'],
    ).entries) {
      final String name = cleanName(entry.key);
      if (name.isEmpty) continue;
      final String partyKey = name.toLowerCase();
      displayNames.putIfAbsent(partyKey, () => name);
      milk[partyKey] =
          (milk[partyKey] ?? 0) + milkTotals(entry.value).netAmount;
    }
    for (final Map<String, dynamic> row in LedgerCodec.canonicalList(
      state['udharDB'],
    )) {
      final String name = cleanName(row['name']);
      if (name.isEmpty) continue;
      final String partyKey = name.toLowerCase();
      displayNames.putIfAbsent(partyKey, () => name);
      credit[partyKey] = (credit[partyKey] ?? 0) + creditSigned(row);
    }
    final Set<String> names = <String>{...milk.keys, ...credit.keys};
    final List<PartyBalance> result = names
        .map(
          (String key) => PartyBalance(
            name: displayNames[key] ?? key,
            milk: milk[key] ?? 0,
            credit: credit[key] ?? 0,
          ),
        )
        .toList();
    result.sort((PartyBalance a, PartyBalance b) {
      final int byAbsolute = b.net.abs().compareTo(a.net.abs());
      return byAbsolute != 0 ? byAbsolute : a.name.compareTo(b.name);
    });
    return result;
  }

  static String cleanName(dynamic value) => '${value ?? ''}'
      .replaceAll(RegExp(r'[\u0000-\u001F\u007F]'), ' ')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();

  static String cleanKey(dynamic value) => '${value ?? ''}'
      .replaceAll(RegExp(r'[.#$\[\]<>/\\]'), ' ')
      .replaceAll("'", ' ')
      .replaceAll('"', ' ')
      .replaceAll('`', ' ')
      .replaceAll(RegExp(r'[\u0000-\u001F\u007F]'), ' ')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();
}

class LedgerSyncService extends ChangeNotifier {
  LedgerSyncService({FirebaseAuth? auth, FirebaseDatabase? database})
    : auth = auth ?? FirebaseAuth.instance,
      database = database ?? FirebaseDatabase.instance;

  final FirebaseAuth auth;
  final FirebaseDatabase database;
  final Uuid _uuid = const Uuid();

  static const Duration _passiveReconcileCooldown = Duration(seconds: 15);
  static const Duration _automaticFullAuditInterval = Duration(days: 7);

  late Box<String> _box;
  Map<String, dynamic> _state = LedgerCodec.emptyState();
  List<PendingWrite> _outbox = <PendingWrite>[];
  Map<String, int> _tableRevisions = <String, int>{};
  Map<String, Map<String, String>> _tableClocks =
      <String, Map<String, String>>{};
  String _changeToken = '';
  int _revision = 0;
  int _lastFullAuditAt = 0;
  int _lastMetadataReadAt = 0;
  String _writerId = '';
  String? _activeUid;
  DatabaseReference? _appDataRef;
  DatabaseReference? _ledgerV2Ref;
  StreamSubscription<User?>? _authSubscription;
  StreamSubscription<DatabaseEvent>? _connectionSubscription;
  StreamSubscription<DatabaseEvent>? _tokenSubscription;
  StreamSubscription<DatabaseEvent>? _diaryProjectionSubscription;
  Timer? _flushTimer;
  Timer? _reconcileTimer;
  Timer? _retryTimer;
  Future<void> _gate = Future<void>.value();
  int _retryAttempt = 0;
  bool _booting = true;
  bool _syncing = false;
  bool _darkMode = false;
  bool _disposed = false;
  bool? _connected;
  Object? _lastError;
  SyncEnvelope? _pendingServerAck;
  String? _pendingServerAckUid;
  DiaryProjectionMetadata _advertisedDiaryProjection =
      const DiaryProjectionMetadata.unavailable();
  DiaryProjectionMetadata _diaryProjection =
      const DiaryProjectionMetadata.unavailable();
  Map<String, dynamic> _diaryPeriodsByEntry = <String, dynamic>{};
  final Map<String, String> _loadedDiaryMonthVersions = <String, String>{};
  final Map<String, Future<void>> _diaryMonthLoads = <String, Future<void>>{};
  final Map<String, Object> _diaryMonthErrors = <String, Object>{};
  String _lastDiaryProjectionProbeSource = '';
  String? _completeDiarySourceKey;
  int _diaryPeriodVersion = 0;

  User? get user => auth.currentUser;
  bool get booting => _booting;
  bool get syncing => _syncing;
  bool get darkMode => _darkMode;
  bool get isConnected => SyncConnectionPolicy.canContactServer(_connected);
  bool get isOffline => _connected == false;
  int get pendingWrites => _outbox.length;
  Object? get lastError => _lastError;
  Map<String, dynamic> get state => _state;
  Map<String, dynamic>? _projectedState;
  LedgerProjection? _projection;
  final ChangeNotifier _contentChanges = ChangeNotifier();

  Listenable get contentChanges => _contentChanges;

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  void _notifyContent() {
    if (_disposed) return;
    _contentChanges.notifyListeners();
    notifyListeners();
  }

  void _invalidateProjectionCache() {
    _projectedState = null;
    _projection = null;
  }

  LedgerProjection projectionAt(DateTime date) {
    final LedgerProjection? cached = _projection;
    if (cached != null &&
        identical(_projectedState, _state) &&
        cached.month == date.month &&
        cached.year == date.year) {
      return cached;
    }
    final LedgerProjection computed = LedgerProjection.fromState(
      _state,
      month: date.month,
      year: date.year,
    );
    _projectedState = _state;
    _projection = computed;
    return computed;
  }

  LedgerProjection get currentProjection => projectionAt(DateTime.now());

  DiarySourceVersion _diarySourceVersion({
    Map<String, int>? tableRevisions,
    Map<String, Map<String, String>>? tableClocks,
  }) {
    final Map<String, int> revisions = tableRevisions ?? _tableRevisions;
    final Map<String, Map<String, String>> clocks = tableClocks ?? _tableClocks;
    return DiarySourceVersion(
      revision: revisions['diaryDB'] ?? 0,
      clockHash: LedgerDeltaPolicy.tableClockHash(
        clocks['diaryDB'] ?? const <String, String>{},
      ),
    );
  }

  bool get diaryMonthlyMode =>
      _diaryProjection.matchesSource(_diarySourceVersion());

  int get diaryPeriodVersion => _diaryPeriodVersion;

  List<DateTime> get diaryAvailablePeriods {
    final Map<int, DateTime> periods = <int, DateTime>{};
    for (final DateTime period in LedgerMath.recordPeriods(_state['diaryDB'])) {
      periods[period.year * 100 + period.month] = period;
    }
    if (diaryMonthlyMode) {
      for (final DateTime period in DiaryMonthCodec.periodsFromIndex(
        _diaryPeriodsByEntry,
      )) {
        periods[period.year * 100 + period.month] = period;
      }
    }
    final List<DateTime> result = periods.values.toList()
      ..sort((DateTime a, DateTime b) => b.compareTo(a));
    return result;
  }

  bool isDiaryMonthLoading(int year, int month) =>
      _diaryMonthLoads.containsKey(DiaryMonthCodec.periodKey(year, month));

  Object? diaryMonthError(int year, int month) =>
      _diaryMonthErrors[DiaryMonthCodec.periodKey(year, month)];

  Future<void> initialize() async {
    if (_disposed) return;
    await Hive.initFlutter();
    _box = await Hive.openBox<String>('aarish_sync_v1');
    _darkMode = _box.get('setting.darkMode') == 'true';
    _writerId = _box.get('setting.writerId') ?? '';
    if (!ledgerWriterIdPattern.hasMatch(_writerId)) {
      _writerId =
          'writer_flt_${_uuid.v4().replaceAll('-', '').substring(0, 20)}';
      await _box.put('setting.writerId', _writerId);
    }
    // Do not enable RTDB disk persistence here. This service already owns the
    // single durable offline queue in Hive (`SyncEnvelope.outbox`). Enabling a
    // second durable Firebase queue lets one logical mutation survive/replay
    // through two independent lifecycles after process death.
    await _activateUser(auth.currentUser);
    if (_disposed) return;
    _authSubscription = auth.userChanges().listen(
      (User? nextUser) => unawaited(_activateUser(nextUser)),
    );
  }

  Future<T> _locked<T>(Future<T> Function() operation) async {
    final Future<void> previous = _gate;
    final Completer<void> release = Completer<void>();
    _gate = release.future;
    await previous;
    try {
      return await operation();
    } finally {
      if (!release.isCompleted) release.complete();
    }
  }

  Future<void> _activateUser(User? nextUser) async {
    if (_disposed) return;
    bool shouldReconcile = false;
    await _locked<void>(() async {
      if (_disposed) return;
      final String? nextUid = nextUser?.uid;
      if (!_booting && nextUid == _activeUid) return;
      await _detachUserStreams();
      _flushTimer?.cancel();
      _reconcileTimer?.cancel();
      _retryTimer?.cancel();
      _activeUid = nextUid;
      _connected = null;
      _lastError = null;
      _retryAttempt = 0;
      _lastMetadataReadAt = 0;
      _pendingServerAck = null;
      _pendingServerAckUid = null;
      _resetDiaryProjection();

      if (nextUid == null || nextUid.isEmpty) {
        _state = LedgerCodec.emptyState();
        _invalidateProjectionCache();
        _outbox = <PendingWrite>[];
        _tableRevisions = <String, int>{};
        _tableClocks = <String, Map<String, String>>{};
        _changeToken = '';
        _revision = 0;
        _lastFullAuditAt = 0;
        _appDataRef = null;
        _ledgerV2Ref = null;
        _connected = null;
        _booting = false;
        _notifyContent();
        return;
      }

      final SyncEnvelope envelope = _readEnvelope(nextUid);
      _state = envelope.state;
      _invalidateProjectionCache();
      _outbox = List<PendingWrite>.from(envelope.outbox);
      _tableRevisions = Map<String, int>.from(envelope.tableRevisions);
      _tableClocks = LedgerCodec.canonicalTableClocks(envelope.tableClocks);
      _changeToken = envelope.changeToken;
      _revision = envelope.revision;
      _lastFullAuditAt = envelope.lastFullAuditAt;
      _appDataRef = database.ref('users/$nextUid/appData');
      _ledgerV2Ref = database.ref('users/$nextUid/ledgerV2');
      _readDiaryProjectionCache(nextUid);
      _booting = false;
      _attachUserStreams(nextUid);
      _notifyContent();
      shouldReconcile = true;
    });
    if (shouldReconcile && !_disposed) {
      unawaited(reconcile(reason: 'auth-ready', force: _lastFullAuditAt == 0));
    }
  }

  void _scheduleObservedMetadataCheck(String uid, Map<String, dynamic> meta) {
    if (_disposed || uid != _activeUid) return;

    final String remoteToken = '${meta['changeToken'] ?? ''}';

    final Map<String, Map<String, String>> remoteClocks =
        LedgerCodec.canonicalTableClocks(meta['tableClocks']);

    bool tableClockChanged = false;

    final Set<String> roots = <String>{
      ...remoteClocks.keys,
      ..._tableClocks.keys,
    };

    for (final String root in roots) {
      final Map<String, String> remote =
          remoteClocks[root] ?? const <String, String>{};

      final Map<String, String> local =
          _tableClocks[root] ?? const <String, String>{};

      if (!mapEquals(remote, local)) {
        tableClockChanged = true;
        break;
      }
    }

    final bool tokenChanged =
        remoteToken.isNotEmpty && remoteToken != _changeToken;

    if (!tokenChanged && !tableClockChanged) return;

    _scheduleReconcile(
      const Duration(milliseconds: 180),
      tableClockChanged ? 'remote-vector-clock' : 'remote-token',
      expectedRemoteToken: remoteToken.isEmpty ? null : remoteToken,
    );
  }

  void _resetDiaryProjection() {
    _advertisedDiaryProjection = const DiaryProjectionMetadata.unavailable();
    _diaryProjection = const DiaryProjectionMetadata.unavailable();
    _diaryPeriodsByEntry = <String, dynamic>{};
    _loadedDiaryMonthVersions.clear();
    _diaryMonthLoads.clear();
    _diaryMonthErrors.clear();
    _lastDiaryProjectionProbeSource = '';
    _completeDiarySourceKey = null;
    _diaryPeriodVersion++;
  }

  void _readDiaryProjectionCache(String uid) {
    final String? raw = _box.get('diaryProjection.$uid');
    if (raw == null || raw.isEmpty) return;
    try {
      final dynamic decoded = jsonDecode(raw);
      if (decoded is! Map) return;
      final Map<String, dynamic> cache = LedgerCodec.objectMap(decoded);
      _diaryPeriodsByEntry = LedgerCodec.objectMap(cache['periods']);
      _diaryPeriodVersion++;
    } catch (_) {
      // Projection cache is only an optimization; V12 remains authoritative.
    }
  }

  Future<void> _persistDiaryProjectionCache(String uid) async {
    await _box.put(
      'diaryProjection.$uid',
      jsonEncode(<String, dynamic>{
        'version': 1,
        'periods': _diaryPeriodsByEntry,
      }),
    );
  }

  SyncEnvelope _readEnvelope(String uid) {
    final String? raw = _box.get('ledger.$uid');
    if (raw == null || raw.isEmpty) return SyncEnvelope.empty();
    try {
      final dynamic decoded = jsonDecode(raw);
      if (decoded is Map) {
        return SyncEnvelope.fromJson(LedgerCodec.objectMap(decoded));
      }
    } catch (_) {
      // A corrupt local cache is ignored; Firebase remains the source of truth.
    }
    return SyncEnvelope.empty();
  }

  SyncEnvelope _currentEnvelope({
    Map<String, dynamic>? state,
    List<PendingWrite>? outbox,
    String? changeToken,
    int? revision,
    Map<String, int>? tableRevisions,
    Map<String, Map<String, String>>? tableClocks,
    int? lastFullAuditAt,
  }) => SyncEnvelope(
    state: state ?? _state,
    outbox: outbox ?? _outbox,
    changeToken: changeToken ?? _changeToken,
    revision: revision ?? _revision,
    tableRevisions: tableRevisions ?? _tableRevisions,
    tableClocks: tableClocks ?? _tableClocks,
    lastFullAuditAt: lastFullAuditAt ?? _lastFullAuditAt,
  );

  Future<void> _persistEnvelope(String uid, SyncEnvelope envelope) async {
    await _box.put('ledger.$uid', jsonEncode(envelope.toJson()));
  }

  Future<void> _persistPendingServerAckLocked(String uid) async {
    final SyncEnvelope? pending = _pendingServerAck;
    if (pending == null) return;
    if (_pendingServerAckUid != uid) {
      throw const LedgerSyncException(
        'Account changed before local sync acknowledgement.',
      );
    }
    await _persistEnvelope(uid, pending);
    if (uid == _activeUid &&
        _pendingServerAckUid == uid &&
        identical(_pendingServerAck, pending)) {
      _pendingServerAck = null;
      _pendingServerAckUid = null;
    }
  }

  Future<bool> _refreshDiaryProjection(
    String uid,
    DiarySourceVersion source,
  ) async {
    final DatabaseReference? reference = _ledgerV2Ref;
    if (reference == null || uid != _activeUid) return false;
    if (_diaryProjection.matchesSource(source)) return true;

    DiaryProjectionMetadata metadata = _advertisedDiaryProjection;
    final bool shouldProbe =
        metadata.ready || _lastDiaryProjectionProbeSource != source.cacheKey;
    if (!shouldProbe) return false;
    _lastDiaryProjectionProbeSource = source.cacheKey;

    try {
      final DataSnapshot metadataSnapshot = await reference
          .child('meta/diary')
          .get();
      if (uid != _activeUid) return false;
      metadata = DiaryProjectionMetadata.fromValue(metadataSnapshot.value);
      _advertisedDiaryProjection = metadata;
      if (!metadata.matchesSource(source)) {
        if (_diaryProjection.ready) _diaryPeriodVersion++;
        _diaryProjection = metadata;
        return false;
      }

      final DataSnapshot periodsSnapshot = await reference
          .child('diaryPeriods')
          .get();
      final DataSnapshot confirmationSnapshot = await reference
          .child('meta/diary')
          .get();
      if (uid != _activeUid) return false;
      final DiaryProjectionMetadata confirmed =
          DiaryProjectionMetadata.fromValue(confirmationSnapshot.value);
      if (!confirmed.matchesSource(source) ||
          confirmed.sourceRevision != metadata.sourceRevision ||
          confirmed.sourceClockHash != metadata.sourceClockHash) {
        _advertisedDiaryProjection = confirmed;
        _diaryProjection = confirmed;
        return false;
      }

      _diaryProjection = confirmed;
      _advertisedDiaryProjection = confirmed;
      _diaryPeriodsByEntry = LedgerCodec.objectMap(periodsSnapshot.value);
      _diaryPeriodVersion++;
      await _persistDiaryProjectionCache(uid);
      return true;
    } catch (_) {
      _diaryProjection = const DiaryProjectionMetadata.unavailable();
      return false;
    }
  }

  Future<Map<String, dynamic>?> _readStateWithProjectedDiary({
    required String uid,
    required DatabaseReference appData,
    required DiarySourceVersion sourceVersion,
    required int year,
    required int month,
  }) async {
    final DatabaseReference? projection = _ledgerV2Ref;
    if (projection == null) return null;
    try {
      final List<String> roots = ledgerRoots
          .where((String root) => root != 'diaryDB')
          .toList(growable: false);
      final List<Future<DataSnapshot>> rootReads = roots
          .map((String root) => appData.child(root).get())
          .toList(growable: false);
      final Query diaryQuery = projection
          .child('diaryEntries')
          .orderByChild('_period')
          .equalTo(DiaryMonthCodec.periodKey(year, month));
      final Query invalidDiaryQuery = projection
          .child('diaryEntries')
          .orderByChild('_period')
          .equalTo(DiaryMonthCodec.invalidPeriodKey);
      final Future<DataSnapshot> diaryRead = diaryQuery.get();
      final Future<DataSnapshot> invalidDiaryRead = invalidDiaryQuery.get();
      final List<DataSnapshot> rootSnapshots = await Future.wait(rootReads);
      final DataSnapshot diarySnapshot = await diaryRead;
      final DataSnapshot invalidDiarySnapshot = await invalidDiaryRead;
      // Confirm projection metadata only after the entry queries complete.
      // Starting this read in parallel can pair old metadata with newer rows.
      final DataSnapshot metadataSnapshot = await projection
          .child('meta/diary')
          .get();
      if (uid != _activeUid || auth.currentUser?.uid != uid) return null;
      final DiaryProjectionMetadata confirmed =
          DiaryProjectionMetadata.fromValue(metadataSnapshot.value);
      if (!confirmed.matchesSource(sourceVersion)) return null;

      final Map<String, dynamic> source = <String, dynamic>{};
      for (int index = 0; index < roots.length; index++) {
        source[roots[index]] = rootSnapshots[index].value;
      }
      final Map<String, dynamic> state = LedgerCodec.normalizeState(source);
      state['diaryDB'] = LedgerCodec.canonicalList(_state['diaryDB']);
      DiaryMonthCodec.replaceInvalidEntries(
        state,
        DiaryMonthCodec.decodeInvalidEntries(invalidDiarySnapshot.value),
      );
      DiaryMonthCodec.replaceMonth(
        state,
        year: year,
        month: month,
        entries: DiaryMonthCodec.decodeMonthEntries(
          diarySnapshot.value,
          year: year,
          month: month,
        ),
      );
      // Do not mark this month as loaded yet. The caller must first commit
      // this reconstructed state and its matching sync metadata atomically.
      return state;
    } catch (_) {
      // Missing rules, index or projection data must never block legacy V12.
      if (uid == _activeUid) {
        _diaryProjection = const DiaryProjectionMetadata.unavailable();
        _diaryPeriodVersion++;
      }
      return null;
    }
  }

  void _attachUserStreams(String uid) {
    if (_disposed || uid != _activeUid) return;
    _connectionSubscription = database
        .ref('.info/connected')
        .onValue
        .listen(
          (DatabaseEvent event) {
            if (uid != _activeUid) return;
            _connected = event.snapshot.value == true;
            _notify();
            if (_connected == true) {
              _scheduleReconcile(
                const Duration(milliseconds: 120),
                'connection',
              );
            }
          },
          onError: (Object error) {
            if (uid != _activeUid) return;
            _connected = false;
            _lastError = error;
            _notify();
          },
        );
    _tokenSubscription = _appDataRef!
        .child('_syncMeta')
        .onValue
        .listen(
          (DatabaseEvent event) {
            if (uid != _activeUid) return;

            final Map<String, dynamic> meta = LedgerCodec.objectMap(
              event.snapshot.value,
            );

            _scheduleObservedMetadataCheck(uid, meta);
          },
          onError: (Object error) {
            if (uid != _activeUid) return;
            _lastError = error;
            _notify();
          },
        );
    _diaryProjectionSubscription = _ledgerV2Ref!
        .child('meta/diary')
        .onValue
        .listen(
          (DatabaseEvent event) {
            if (uid != _activeUid) return;
            final DiaryProjectionMetadata next =
                DiaryProjectionMetadata.fromValue(event.snapshot.value);
            final bool changed =
                next.ready != _advertisedDiaryProjection.ready ||
                next.schemaVersion !=
                    _advertisedDiaryProjection.schemaVersion ||
                next.sourceRevision !=
                    _advertisedDiaryProjection.sourceRevision ||
                next.sourceClockHash !=
                    _advertisedDiaryProjection.sourceClockHash;
            _advertisedDiaryProjection = next;
            if (changed &&
                (next.ready || _diaryProjection.ready) &&
                !_booting) {
              _scheduleReconcile(
                const Duration(milliseconds: 260),
                'diary-projection',
              );
            }
          },
          onError: (_) {
            if (uid != _activeUid) return;
            _advertisedDiaryProjection =
                const DiaryProjectionMetadata.unavailable();
          },
        );
  }

  Future<void> _detachUserStreams() async {
    await _connectionSubscription?.cancel();
    await _tokenSubscription?.cancel();
    await _diaryProjectionSubscription?.cancel();
    _connectionSubscription = null;
    _tokenSubscription = null;
    _diaryProjectionSubscription = null;
  }

  Future<void> setDarkMode(bool value) async {
    if (_disposed || value == _darkMode) return;
    await _box.put('setting.darkMode', '$value');
    if (_disposed) return;
    _darkMode = value;
    _notify();
  }

  String? readSetting(String key) => _box.get('setting.$key');

  Future<void> writeSetting(String key, String? value) async {
    if (_disposed) return;
    if (value == null) {
      await _box.delete('setting.$key');
    } else {
      await _box.put('setting.$key', value);
    }
  }

  Future<void> ensureDiaryMonthLoaded(int year, int month) {
    if (_disposed || month < 1 || month > 12 || year < 1 || !diaryMonthlyMode) {
      return Future<void>.value();
    }
    final String period = DiaryMonthCodec.periodKey(year, month);
    final DiarySourceVersion source = _diarySourceVersion();
    if (_loadedDiaryMonthVersions[period] == source.cacheKey) {
      return Future<void>.value();
    }
    final Future<void>? active = _diaryMonthLoads[period];
    if (active != null) return active;

    late final Future<void> tracked;
    tracked = _loadDiaryMonth(year: year, month: month, source: source)
        .whenComplete(() {
          if (identical(_diaryMonthLoads[period], tracked)) {
            _diaryMonthLoads.remove(period);
            if (_activeUid != null) _notify();
          }
        });
    _diaryMonthLoads[period] = tracked;
    _diaryMonthErrors.remove(period);
    _notify();
    return tracked;
  }

  Future<void> ensureAllDiaryMonthsLoaded() async {
    if (_disposed) {
      throw const LedgerSyncException('Sync service is no longer available.');
    }
    final String? uid = _activeUid;
    final DatabaseReference? appData = _appDataRef;
    if (uid == null || appData == null || auth.currentUser?.uid != uid) {
      throw const LedgerSyncException(
        'Please sign in before loading Diary history.',
      );
    }

    final DiarySourceVersion localSource = _diarySourceVersion();
    if (!SyncConnectionPolicy.canContactServer(_connected)) {
      if (_completeDiarySourceKey == localSource.cacheKey) return;
      throw const LedgerSyncException(
        'Connect to Firebase before exporting complete Diary history.',
      );
    }

    Object? lastFailure;
    for (int attempt = 0; attempt < 3; attempt++) {
      try {
        final DataSnapshot beforeSnapshot = await appData
            .child('_syncMeta')
            .get();
        if (uid != _activeUid || auth.currentUser?.uid != uid) {
          throw const LedgerSyncException(
            'Account changed while loading Diary history.',
          );
        }
        if (!SyncConnectionPolicy.canContactServer(_connected)) {
          throw const LedgerSyncException(
            'Firebase disconnected while loading Diary history.',
          );
        }
        final DiarySourceVersion before = DiarySourceVersion.fromMetadata(
          beforeSnapshot.value,
        );
        final DiarySourceVersion current = _diarySourceVersion();
        if (!DiaryReadConsistency.sameSource(before, current)) {
          await reconcile(reason: 'diary-history-refresh');
          continue;
        }
        // A revision of zero is legacy metadata and cannot prove that an older
        // client updated the change token. Re-read that history conservatively.
        if (before.revision > 0 && _completeDiarySourceKey == before.cacheKey) {
          return;
        }

        final DataSnapshot diarySnapshot = await appData.child('diaryDB').get();
        final DataSnapshot afterSnapshot = await appData
            .child('_syncMeta')
            .get();
        if (uid != _activeUid || auth.currentUser?.uid != uid) {
          throw const LedgerSyncException(
            'Account changed while loading Diary history.',
          );
        }
        if (!SyncConnectionPolicy.canContactServer(_connected)) {
          throw const LedgerSyncException(
            'Firebase disconnected while loading Diary history.',
          );
        }
        final DiarySourceVersion after = DiarySourceVersion.fromMetadata(
          afterSnapshot.value,
        );
        if (!DiaryReadConsistency.sameSource(before, after)) continue;

        bool applied = false;
        await _locked<void>(() async {
          if (_disposed ||
              uid != _activeUid ||
              auth.currentUser?.uid != uid ||
              !SyncConnectionPolicy.canContactServer(_connected)) {
            return;
          }
          final DiarySourceVersion latestLocal = _diarySourceVersion();
          if (!DiaryReadConsistency.sameSource(after, latestLocal)) return;

          final Map<String, dynamic> nextState = LedgerCodec.normalizeState(
            _state,
          );
          nextState['diaryDB'] = LedgerCodec.canonicalList(diarySnapshot.value);
          // Writes made while the network snapshot was in flight must remain
          // visible and win over that snapshot, including pending deletes.
          for (final PendingWrite write in _outbox) {
            LedgerCodec.applyPath(nextState, write.path, write.value);
          }
          final SyncEnvelope envelope = _currentEnvelope(state: nextState);
          await _persistEnvelope(uid, envelope);
          if (uid != _activeUid) return;

          _state = nextState;
          _invalidateProjectionCache();
          _completeDiarySourceKey = after.cacheKey;
          _loadedDiaryMonthVersions.clear();
          for (final DateTime period in LedgerMath.recordPeriods(
            nextState['diaryDB'],
          )) {
            _loadedDiaryMonthVersions[DiaryMonthCodec.periodKey(
                  period.year,
                  period.month,
                )] =
                after.cacheKey;
          }
          _lastError = null;
          applied = true;
          _notifyContent();
        });
        if (applied) return;
      } catch (error) {
        lastFailure = error;
        if (uid != _activeUid ||
            auth.currentUser?.uid != uid ||
            !SyncConnectionPolicy.canContactServer(_connected)) {
          break;
        }
      }
    }
    if (lastFailure is LedgerSyncException) throw lastFailure;
    throw const LedgerSyncException(
      'Diary changed while its complete history was loading. Please try again.',
    );
  }

  Future<void> _loadDiaryMonth({
    required int year,
    required int month,
    required DiarySourceVersion source,
  }) async {
    final String? uid = _activeUid;
    final DatabaseReference? projection = _ledgerV2Ref;
    final String period = DiaryMonthCodec.periodKey(year, month);
    if (uid == null || projection == null || auth.currentUser?.uid != uid) {
      return;
    }
    if (!SyncConnectionPolicy.canContactServer(_connected)) {
      throw const LedgerSyncException(
        'Connect to Firebase before loading an uncached Diary month.',
      );
    }
    try {
      final Query query = projection
          .child('diaryEntries')
          .orderByChild('_period')
          .equalTo(period);
      // Read projected rows first, then fence them with fresh metadata.
      //
      // Reading rows and metadata in parallel can pair a newer row snapshot
      // with older projection metadata during a Cloud Function update.
      final DataSnapshot entriesSnapshot = await query.get();

      if (!SyncConnectionPolicy.canContactServer(_connected)) {
        throw const LedgerSyncException(
          'Firebase disconnected while loading this Diary month.',
        );
      }

      final DataSnapshot metadataSnapshot = await projection
          .child('meta/diary')
          .get();

      if (!SyncConnectionPolicy.canContactServer(_connected)) {
        throw const LedgerSyncException(
          'Firebase disconnected while validating this Diary month.',
        );
      }

      final DiaryProjectionMetadata confirmed =
          DiaryProjectionMetadata.fromValue(metadataSnapshot.value);

      if (!confirmed.matchesSource(source)) {
        throw const LedgerSyncException(
          'Diary changed while loading. Please try this month again.',
        );
      }

      final List<Map<String, dynamic>> entries =
          DiaryMonthCodec.decodeMonthEntries(
            entriesSnapshot.value,
            year: year,
            month: month,
          );

      await _locked<void>(() async {
        if (uid != _activeUid || auth.currentUser?.uid != uid) return;
        final DiarySourceVersion currentSource = _diarySourceVersion();
        if (!DiaryReadConsistency.canApplyProjectedMonth(
          projection: _diaryProjection,
          requestedSource: source,
          currentSource: currentSource,
        )) {
          return;
        }
        final Map<String, dynamic> nextState = LedgerCodec.normalizeState(
          _state,
        );
        DiaryMonthCodec.replaceMonth(
          nextState,
          year: year,
          month: month,
          entries: entries,
        );
        for (final PendingWrite write in _outbox) {
          LedgerCodec.applyPath(nextState, write.path, write.value);
        }
        final SyncEnvelope envelope = _currentEnvelope(state: nextState);
        await _persistEnvelope(uid, envelope);
        if (uid != _activeUid) return;
        _state = nextState;
        _invalidateProjectionCache();
        _loadedDiaryMonthVersions[period] = source.cacheKey;
        _diaryMonthErrors.remove(period);
        _notifyContent();
      });
    } catch (error) {
      if (uid == _activeUid) {
        _diaryMonthErrors[period] = error;
      }
      rethrow;
    }
  }

  static const Set<String> _concurrentProfileRoots = <String>{
    'milkDB',
    'salaryDB',
    'projectDB',
  };

  static bool _deepCollectionEquals(dynamic left, dynamic right) {
    if (identical(left, right)) {
      return true;
    }

    if (left is Map && right is Map) {
      if (left.length != right.length) {
        return false;
      }

      for (final dynamic key in left.keys) {
        if (!right.containsKey(key)) {
          return false;
        }

        if (!_deepCollectionEquals(left[key], right[key])) {
          return false;
        }
      }

      return true;
    }

    if (left is List && right is List) {
      if (left.length != right.length) {
        return false;
      }

      for (int index = 0; index < left.length; index++) {
        if (!_deepCollectionEquals(left[index], right[index])) {
          return false;
        }
      }

      return true;
    }

    return left == right;
  }

  Map<String, dynamic>? _groupedProfileDiff(String path, dynamic incoming) {
    if (incoming == null || incoming is! Map) return null;

    final List<String> parts = path.split('/');

    // Only direct profile writes:
    //
    //   milkDB/<name>
    //   salaryDB/<name>
    //   projectDB/<name>
    //
    // Child record operations already have safe leaf-level paths.
    if (parts.length != 2 || !_concurrentProfileRoots.contains(parts.first)) {
      return null;
    }

    final String root = parts.first;
    final String profileName = parts[1];

    final Map<String, dynamic> database = LedgerCodec.objectMap(_state[root]);

    final dynamic existingValue = database[profileName];
    final bool profileExists = existingValue is Map;

    // Decompose first-time profiles too. Two devices can create the same
    // profile name before either has observed the other; whole-parent writes
    // would then be last-writer-wins and could erase the other device's
    // records. Child writes merge safely at Firebase.
    final Map<String, dynamic> existing = profileExists
        ? LedgerCodec.objectMap(existingValue)
        : <String, dynamic>{};

    final Map<String, dynamic> next = LedgerCodec.objectMap(incoming);

    final Map<String, dynamic> result = <String, dynamic>{};

    final Set<String> fields = <String>{...existing.keys, ...next.keys};

    for (final String field in fields) {
      final dynamic oldValue = existing[field];
      final dynamic newValue = next[field];

      if (field != 'records') {
        if (!_deepCollectionEquals(oldValue, newValue)) {
          result['$path/$field'] = newValue;
        }

        continue;
      }

      final List<dynamic> oldRecords = LedgerCodec.canonicalList(oldValue);

      final List<dynamic> newRecords = LedgerCodec.canonicalList(newValue);

      final Map<String, dynamic> oldById = <String, dynamic>{};
      final Map<String, dynamic> newById = <String, dynamic>{};

      for (final dynamic item in oldRecords) {
        if (item is! Map) continue;

        final Map<String, dynamic> row = LedgerCodec.objectMap(item);

        final String id = '${row['id'] ?? row['key'] ?? ''}'.trim();

        if (id.isNotEmpty) {
          oldById[id] = row;
        }
      }

      for (final dynamic item in newRecords) {
        if (item is! Map) continue;

        final Map<String, dynamic> row = LedgerCodec.objectMap(item);

        final String id = '${row['id'] ?? row['key'] ?? ''}'.trim();

        if (id.isNotEmpty) {
          newById[id] = row;
        }
      }

      // If legacy records have no stable IDs, retaining the existing parent
      // behavior is safer than inventing record identities.
      if (oldById.length != oldRecords.length ||
          newById.length != newRecords.length) {
        return null;
      }

      final Set<String> ids = <String>{...oldById.keys, ...newById.keys};

      for (final String id in ids) {
        final dynamic oldRecord = oldById[id];
        final dynamic newRecord = newById[id];

        if (!_deepCollectionEquals(oldRecord, newRecord)) {
          result['$path/records/$id'] = newRecord;
        }
      }
    }

    // Keep the old whole-parent behavior only for a truly empty brand-new
    // profile, otherwise an empty diff would silently skip profile creation.
    if (!profileExists && result.isEmpty) return null;
    return result;
  }

  Future<void> write(
    String path,
    dynamic value, {
    String reason = 'user-mutation',
  }) => writeBatch(<String, dynamic>{path: value}, reason: reason);

  Future<void> writeBatch(
    Map<String, dynamic> writes, {
    String reason = 'user-batch',
  }) async {
    if (writes.isEmpty) return;

    await _locked<void>(() async {
      final Map<String, dynamic> expandedWrites = <String, dynamic>{};

      for (final MapEntry<String, dynamic> entry in writes.entries) {
        final String normalizedPath = LedgerFirebasePolicy.validatePath(
          entry.key,
        );

        final Map<String, dynamic>? groupedDiff = _groupedProfileDiff(
          normalizedPath,
          entry.value,
        );

        if (groupedDiff != null) {
          expandedWrites.addAll(groupedDiff);
        } else {
          expandedWrites[normalizedPath] = entry.value;
        }
      }

      if (expandedWrites.isEmpty) return;

      if (_disposed) {
        throw const LedgerSyncException('Sync service is no longer available.');
      }
      final String? uid = _activeUid;
      if (uid == null || uid.isEmpty || auth.currentUser?.uid != uid) {
        throw const LedgerSyncException('Please sign in before saving data.');
      }
      await _persistPendingServerAckLocked(uid);
      final Map<String, dynamic> nextState = LedgerCodec.normalizeState(_state);
      final List<PendingWrite> nextOutbox = List<PendingWrite>.from(_outbox);
      int sequence = 0;
      for (final MapEntry<String, dynamic> entry in expandedWrites.entries) {
        final String path = LedgerFirebasePolicy.validatePath(entry.key);
        final dynamic safeValue = LedgerFirebasePolicy.sanitizeValue(
          entry.value,
          path,
        );
        if (!LedgerCodec.applyPath(nextState, path, safeValue)) {
          throw LedgerSyncException('Unsupported data path: $path');
        }
        OutboxPlanner.addCompacted(
          nextOutbox,
          PendingWrite(
            id: '${DateTime.now().microsecondsSinceEpoch}-${sequence++}-${_uuid.v4().substring(0, 8)}',
            path: path,
            value: safeValue,
            createdAt: DateTime.now().millisecondsSinceEpoch,
            reason: reason,
          ),
        );
      }

      final SyncEnvelope nextEnvelope = _currentEnvelope(
        state: nextState,
        outbox: nextOutbox,
      );
      // State and outbox are written as one Hive value. The UI is notified only
      // after this durable commit, eliminating the crash gap between both.
      await _persistEnvelope(uid, nextEnvelope);
      if (uid != _activeUid) {
        throw const LedgerSyncException('Account changed while saving.');
      }
      _state = nextState;
      _invalidateProjectionCache();
      _outbox = nextOutbox;
      _lastError = null;
      _notifyContent();
      _scheduleFlush(const Duration(milliseconds: 180));
    });
  }

  void _scheduleFlush(Duration delay) {
    if (_disposed) return;
    _flushTimer?.cancel();
    _flushTimer = Timer(delay, () {
      if (!_disposed) unawaited(flush());
    });
  }

  void _scheduleReconcile(
    Duration delay,
    String reason, {
    String? expectedRemoteToken,
  }) {
    if (_disposed) return;
    _reconcileTimer?.cancel();
    _reconcileTimer = Timer(delay, () {
      if (_disposed) return;
      if (expectedRemoteToken != null &&
          (expectedRemoteToken.isEmpty ||
              expectedRemoteToken == _changeToken)) {
        return;
      }
      unawaited(
        reconcile(reason: reason, expectedRemoteToken: expectedRemoteToken),
      );
    });
  }

  Future<bool> flush({bool throwOnFailure = false}) =>
      _locked<bool>(() => _flushLocked(throwOnFailure: throwOnFailure));

  Future<bool> _flushLocked({bool throwOnFailure = false}) async {
    if (_disposed) return false;
    final String? uid = _activeUid;
    final DatabaseReference? reference = _appDataRef;
    if (uid == null || reference == null) return true;
    try {
      await _persistPendingServerAckLocked(uid);
    } catch (error) {
      _lastError = error;
      _scheduleRetry();
      if (throwOnFailure) rethrow;
      return false;
    }
    if (_outbox.isEmpty) {
      _lastError = null;
      _retryAttempt = 0;
      return true;
    }
    if (!SyncConnectionPolicy.canContactServer(_connected)) return false;
    _syncing = true;
    _notify();

    try {
      int batches = 0;
      while (_outbox.isNotEmpty && batches < 8) {
        if (uid != _activeUid || auth.currentUser?.uid != uid) return false;
        final List<PendingWrite> batch = OutboxPlanner.nextCompatibleBatch(
          _outbox,
        );
        if (batch.isEmpty) break;
        final String batchId = OutboxPlanner.batchId(batch);
        final Map<String, Object?> payload = <String, Object?>{};
        final Map<String, dynamic> delta = <String, dynamic>{};
        final Set<String> touchedRoots = <String>{};
        for (final PendingWrite write in batch) {
          // Revalidate persisted operations at upload time as well. This
          // protects upgrades from malformed legacy or tampered local queues.
          final String safePath = LedgerFirebasePolicy.validatePath(write.path);
          final dynamic safeValue = LedgerFirebasePolicy.sanitizeValue(
            write.value,
            safePath,
          );
          payload[safePath] = safeValue;
          delta[safePath] = safeValue;
          touchedRoots.add(safePath.split('/').first);
        }

        final int previousRevision = _revision;
        final int revision = math.max(
          DateTime.now().millisecondsSinceEpoch,
          previousRevision + 1,
        );
        final String previousToken = _changeToken;
        final String token =
            '$_writerId:$revision:${_uuid.v4().replaceAll('-', '').substring(0, 10)}';
        payload['_syncMeta/rev'] = revision;
        payload['_syncMeta/prevRev'] = previousRevision;
        payload['_syncMeta/changeToken'] = token;
        payload['_syncMeta/prevToken'] = previousToken.isEmpty
            ? null
            : previousToken;
        payload['_syncMeta/writerId'] = _writerId;
        payload['_syncMeta/mode'] = 'AARISH_FIREBASE_COST_CORE_V12_VECTOR';
        payload['_syncMeta/updatedAt'] = ServerValue.timestamp;
        // Part of the same atomic RTDB update as the ledger mutation. Each
        // installation owns one writer child, so later devices do not erase it.
        payload['_syncMeta/lastBatchIds/$_writerId'] = batchId;
        for (final String root in touchedRoots) {
          payload['_syncMeta/tables/$root'] = revision;
          payload['_syncMeta/tableClocks/$root/$_writerId'] = token;
        }
        final String deltaJson = jsonEncode(delta);
        payload['_syncMeta/deltaWrites'] = deltaJson.length < 2500
            ? deltaJson
            : null;
        payload['_syncMeta/deltaPaths'] = DeltaPathCodec.encode(
          batch.map((PendingWrite write) => write.path),
        );

        await reference.update(payload);

        final Set<String> acknowledged = batch
            .map((PendingWrite write) => write.id)
            .toSet();
        final List<PendingWrite> remaining = _outbox
            .where((PendingWrite write) => !acknowledged.contains(write.id))
            .toList();
        final Map<String, int> nextTableRevisions = Map<String, int>.from(
          _tableRevisions,
        );
        final Map<String, Map<String, String>> nextTableClocks =
            LedgerCodec.canonicalTableClocks(_tableClocks);
        for (final String root in touchedRoots) {
          nextTableRevisions[root] = revision;
          nextTableClocks.putIfAbsent(
            root,
            () => <String, String>{},
          )[_writerId] = token;
        }
        final SyncEnvelope acknowledgedEnvelope = _currentEnvelope(
          outbox: remaining,
          changeToken: token,
          revision: revision,
          tableRevisions: nextTableRevisions,
          tableClocks: nextTableClocks,
        );
        // Firebase has committed this batch, but its local acknowledgement is
        // not durable until Hive accepts the exact envelope below. The gate is
        // deliberately installed before any later batch can advance
        // lastBatchIds; this preserves single-batch crash recovery even when a
        // local storage write fails after a successful server update.
        _pendingServerAck = acknowledgedEnvelope;
        _pendingServerAckUid = uid;
        _outbox = remaining;
        _changeToken = token;
        _revision = revision;
        _tableRevisions = nextTableRevisions;
        _tableClocks = nextTableClocks;
        _retryAttempt = 0;
        await _persistPendingServerAckLocked(uid);
        _lastError = null;
        batches++;
        _notify();
      }
      if (_outbox.isNotEmpty) {
        _scheduleFlush(const Duration(milliseconds: 250));
      }
      return _outbox.isEmpty;
    } catch (error) {
      _lastError = error;
      _scheduleRetry();
      if (throwOnFailure) rethrow;
      return false;
    } finally {
      _syncing = false;
      _notify();
    }
  }

  void _scheduleRetry() {
    if (_disposed) return;
    _retryTimer?.cancel();
    final int seconds = math.min(60, 2 << math.min(_retryAttempt, 4));
    _retryAttempt++;
    _retryTimer = Timer(Duration(seconds: seconds), () {
      if (!_disposed) unawaited(reconcile(reason: 'retry'));
    });
  }

  Future<bool> reconcile({
    String reason = 'manual',
    bool force = false,
    String? expectedRemoteToken,
  }) => _locked<bool>(() async {
    if (expectedRemoteToken != null &&
        (expectedRemoteToken.isEmpty || expectedRemoteToken == _changeToken)) {
      return true;
    }
    return _reconcileLocked(reason: reason, force: force);
  });

  Future<bool> _reconcileLocked({
    required String reason,
    required bool force,
  }) async {
    if (_disposed) return false;
    final String? uid = _activeUid;
    final DatabaseReference? reference = _appDataRef;
    if (uid == null || reference == null || auth.currentUser?.uid != uid) {
      return false;
    }
    try {
      await _persistPendingServerAckLocked(uid);
    } catch (error) {
      _lastError = error;
      _scheduleRetry();
      return false;
    }
    if (!SyncConnectionPolicy.canContactServer(_connected)) return false;
    final int startedAt = DateTime.now().millisecondsSinceEpoch;
    final bool passive = reason == 'connection' || reason == 'lifecycle-resume';
    final int passiveElapsed = startedAt - _lastMetadataReadAt;
    if (!force &&
        passive &&
        _outbox.isEmpty &&
        passiveElapsed >= 0 &&
        passiveElapsed < _passiveReconcileCooldown.inMilliseconds) {
      return true;
    }
    _syncing = true;
    _notify();
    try {
      final DataSnapshot metaSnapshot = await reference
          .child('_syncMeta')
          .get();
      if (uid != _activeUid ||
          auth.currentUser?.uid != uid ||
          !SyncConnectionPolicy.canContactServer(_connected)) {
        return false;
      }
      _lastMetadataReadAt = DateTime.now().millisecondsSinceEpoch;
      final Map<String, dynamic> meta = LedgerCodec.objectMap(
        metaSnapshot.value,
      );

      // Recover the narrow crash window where Firebase committed a batch but
      // Hive did not persist the local acknowledgement. Replaying such a batch
      // could overwrite a newer edit from another device. The writer-scoped
      // digest below is atomically committed with the data, so an exact match
      // proves that the pending prefix has already reached the server.
      final Map<String, dynamic> remoteLastBatchIds = LedgerCodec.objectMap(
        meta['lastBatchIds'],
      );
      final String remoteLastBatchId = '${remoteLastBatchIds[_writerId] ?? ''}';
      if (_outbox.isNotEmpty &&
          RegExp(r'^[a-f0-9]{64}$').hasMatch(remoteLastBatchId)) {
        final List<PendingWrite> candidate = OutboxPlanner.nextCompatibleBatch(
          _outbox,
        );
        if (candidate.isNotEmpty &&
            OutboxPlanner.batchId(candidate) == remoteLastBatchId) {
          final Set<String> acknowledgedIds = candidate
              .map((PendingWrite write) => write.id)
              .toSet();
          final List<PendingWrite> recoveredOutbox = _outbox
              .where(
                (PendingWrite write) => !acknowledgedIds.contains(write.id),
              )
              .toList();
          await _persistEnvelope(
            uid,
            _currentEnvelope(outbox: recoveredOutbox),
          );
          if (uid != _activeUid || auth.currentUser?.uid != uid) return false;
          _outbox = recoveredOutbox;
          _notify();
        }
      }

      final String remoteToken = '${meta['changeToken'] ?? ''}';
      final int remoteRevision = _asInt(meta['rev']);
      final Map<String, dynamic> rawRemoteTables = LedgerCodec.objectMap(
        meta['tables'],
      );
      final Map<String, int> remoteTables = <String, int>{};
      for (final MapEntry<String, dynamic> entry in rawRemoteTables.entries) {
        remoteTables[entry.key] = _asInt(entry.value);
      }
      final Map<String, Map<String, String>> remoteTableClocks =
          LedgerCodec.canonicalTableClocks(meta['tableClocks']);
      final String remoteWriterId = '${meta['writerId'] ?? ''}';
      final Set<String> changedRoots = LedgerDeltaPolicy.changedRoots(
        remoteRevisions: remoteTables,
        localRevisions: _tableRevisions,
        remoteClocks: remoteTableClocks,
        localClocks: _tableClocks,
      );

      final int now = DateTime.now().millisecondsSinceEpoch;
      final bool fullAuditDue = SyncAuditPolicy.isDue(
        now: now,
        lastFullAuditAt: _lastFullAuditAt,
        interval: _automaticFullAuditInterval,
      );
      final bool tokenChanged =
          remoteToken != _changeToken ||
          (remoteToken.isEmpty && remoteRevision != _revision);
      final bool cloudChanged = tokenChanged || changedRoots.isNotEmpty;
      final bool requireFull = force || fullAuditDue;
      final DiarySourceVersion remoteDiarySource = _diarySourceVersion(
        tableRevisions: remoteTables,
        tableClocks: remoteTableClocks,
      );
      bool diaryProjectionAvailable = _diaryProjection.matchesSource(
        remoteDiarySource,
      );
      if (requireFull ||
          changedRoots.contains('diaryDB') ||
          reason == 'diary-projection') {
        diaryProjectionAvailable = await _refreshDiaryProjection(
          uid,
          remoteDiarySource,
        );
        if (!SyncConnectionPolicy.canContactServer(_connected)) return false;
      }

      if (!requireFull && !cloudChanged) {
        final bool flushed = await _flushLocked();
        if (flushed) _lastError = null;
        return flushed;
      }

      Map<String, dynamic> base = LedgerCodec.normalizeState(_state);
      bool usedDelta = false;
      bool usedTargetedReads = false;
      final String? rawDelta = meta['deltaWrites'] is String
          ? meta['deltaWrites'] as String
          : null;
      final String predecessor = '${meta['prevToken'] ?? ''}';
      if (!requireFull &&
          cloudChanged &&
          rawDelta != null &&
          rawDelta.isNotEmpty &&
          rawDelta.length <= 2500) {
        try {
          final dynamic decoded = jsonDecode(rawDelta);
          if (decoded is Map) {
            final Map<String, dynamic> deltas = LedgerCodec.objectMap(decoded);
            final Set<String> deltaRoots = <String>{};
            bool valid = deltas.isNotEmpty;
            for (final MapEntry<String, dynamic> entry in deltas.entries) {
              final String safePath = LedgerFirebasePolicy.validatePath(
                entry.key,
              );
              deltaRoots.add(safePath.split('/').first);
              valid =
                  valid && LedgerCodec.applyPath(base, safePath, entry.value);
            }
            if (valid &&
                LedgerDeltaPolicy.canApplyDelta(
                  remoteWriterId: remoteWriterId,
                  predecessorToken: predecessor,
                  localToken: _changeToken,
                  changedRoots: changedRoots,
                  deltaRoots: deltaRoots,
                  remoteClocks: remoteTableClocks,
                  localClocks: _tableClocks,
                )) {
              usedDelta = true;
            }
          }
        } catch (_) {
          usedDelta = false;
          base = LedgerCodec.normalizeState(_state);
        }
        if (!usedDelta) base = LedgerCodec.normalizeState(_state);
      }

      if (!usedDelta && !requireFull && cloudChanged) {
        final List<String> advertisedPaths = DeltaPathCodec.decode(
          meta['deltaPaths'],
        );
        if (advertisedPaths.isNotEmpty) {
          final List<String> safePaths = <String>[];
          final Set<String> pathRoots = <String>{};
          bool valid = true;
          try {
            for (final String path in advertisedPaths) {
              final String safePath = LedgerFirebasePolicy.validatePath(path);
              safePaths.add(safePath);
              pathRoots.add(safePath.split('/').first);
            }
          } catch (_) {
            valid = false;
          }
          valid =
              valid &&
              LedgerDeltaPolicy.canApplyDelta(
                remoteWriterId: remoteWriterId,
                predecessorToken: predecessor,
                localToken: _changeToken,
                changedRoots: changedRoots,
                deltaRoots: pathRoots,
                remoteClocks: remoteTableClocks,
                localClocks: _tableClocks,
              );
          if (valid) {
            final List<Future<MapEntry<String, dynamic>>> reads = safePaths
                .map(
                  (String path) async => MapEntry<String, dynamic>(
                    path,
                    (await reference.child(path).get()).value,
                  ),
                )
                .toList(growable: false);
            final List<MapEntry<String, dynamic>> values = await Future.wait(
              reads,
            );
            if (uid != _activeUid ||
                auth.currentUser?.uid != uid ||
                !SyncConnectionPolicy.canContactServer(_connected)) {
              return false;
            }
            for (final MapEntry<String, dynamic> entry in values) {
              if (!LedgerCodec.applyPath(base, entry.key, entry.value)) {
                valid = false;
                break;
              }
            }
            usedTargetedReads = valid;
            if (!usedTargetedReads) {
              base = LedgerCodec.normalizeState(_state);
            }
          }
        }
      }

      int nextFullAuditAt = _lastFullAuditAt;
      String? projectedDiaryPeriod;
      if (!usedDelta && !usedTargetedReads) {
        if (requireFull || remoteTables.isEmpty) {
          final DateTime currentMonth = DateTime.now();
          final Map<String, dynamic>? projectedState = diaryProjectionAvailable
              ? await _readStateWithProjectedDiary(
                  uid: uid,
                  appData: reference,
                  sourceVersion: remoteDiarySource,
                  year: currentMonth.year,
                  month: currentMonth.month,
                )
              : null;
          if (!SyncConnectionPolicy.canContactServer(_connected)) return false;
          if (projectedState != null) {
            base = projectedState;
            projectedDiaryPeriod = DiaryMonthCodec.periodKey(
              currentMonth.year,
              currentMonth.month,
            );
          } else {
            final DataSnapshot fullSnapshot = await reference.get();
            if (uid != _activeUid ||
                auth.currentUser?.uid != uid ||
                !SyncConnectionPolicy.canContactServer(_connected)) {
              return false;
            }
            base = LedgerCodec.normalizeState(fullSnapshot.value);
            _loadedDiaryMonthVersions.clear();
          }
          nextFullAuditAt = now;
        } else {
          if (changedRoots.isEmpty && cloudChanged) {
            changedRoots.addAll(ledgerRoots);
          }
          final List<Future<MapEntry<String, dynamic>>> reads = changedRoots
              .map(
                (String root) async => MapEntry<String, dynamic>(
                  root,
                  (await reference.child(root).get()).value,
                ),
              )
              .toList();
          final List<MapEntry<String, dynamic>> values = await Future.wait(
            reads,
          );
          if (uid != _activeUid ||
              auth.currentUser?.uid != uid ||
              !SyncConnectionPolicy.canContactServer(_connected)) {
            return false;
          }
          for (final MapEntry<String, dynamic> entry in values) {
            final Map<String, dynamic> oneRoot = LedgerCodec.normalizeState(
              <String, dynamic>{entry.key: entry.value},
            );
            base[entry.key] = oneRoot[entry.key];
          }
        }
      }

      // Delta payloads live inside the metadata snapshot itself. Every other
      // reconciliation path performs one or more later RTDB reads, so confirm
      // that no remote writer advanced the authoritative metadata in between.
      // Without this fence, data from revision N+1 can be committed locally with
      // revision/token N, creating a mixed snapshot until a later reconcile.
      if (!usedDelta) {
        final DataSnapshot confirmationSnapshot = await reference
            .child('_syncMeta')
            .get();
        if (uid != _activeUid ||
            auth.currentUser?.uid != uid ||
            !SyncConnectionPolicy.canContactServer(_connected)) {
          return false;
        }
        final Map<String, dynamic> confirmationMeta = LedgerCodec.objectMap(
          confirmationSnapshot.value,
        );
        final String confirmedToken =
            '${confirmationMeta['changeToken'] ?? ''}';
        final int confirmedRevision = _asInt(confirmationMeta['rev']);
        if (confirmedToken != remoteToken ||
            confirmedRevision != remoteRevision) {
          _scheduleReconcile(const Duration(milliseconds: 40), 'snapshot-race');
          return false;
        }
      }

      // Local writes, including deletes, always replay over the cloud snapshot.
      // This is the key invariant that prevents a stale login from resurrecting
      // something the user deleted while offline.
      for (final PendingWrite write in _outbox) {
        LedgerCodec.applyPath(base, write.path, write.value);
      }
      base = LedgerCodec.normalizeState(base);

      final SyncEnvelope reconciled = _currentEnvelope(
        state: base,
        changeToken: remoteToken,
        revision: remoteRevision,
        tableRevisions: remoteTables,
        tableClocks: remoteTableClocks,
        lastFullAuditAt: nextFullAuditAt,
      );
      await _persistEnvelope(uid, reconciled);
      if (uid != _activeUid) return false;
      _state = base;
      if (projectedDiaryPeriod != null) {
        _loadedDiaryMonthVersions[projectedDiaryPeriod] =
            remoteDiarySource.cacheKey;
      }
      _invalidateProjectionCache();
      _changeToken = remoteToken;
      _revision = remoteRevision;
      _tableRevisions = remoteTables;
      _tableClocks = remoteTableClocks;
      _lastFullAuditAt = nextFullAuditAt;
      _lastError = null;
      _notifyContent();
      return _flushLocked();
    } catch (error) {
      _lastError = error;
      _scheduleRetry();
      return false;
    } finally {
      _syncing = false;
      _notify();
    }
  }

  Future<bool> drainBeforeLogout() async {
    if (_outbox.isEmpty && _pendingServerAck == null) return true;
    try {
      await flush(throwOnFailure: true);
    } catch (_) {
      return false;
    }
    return _outbox.isEmpty && _pendingServerAck == null;
  }

  Future<void> integrityCheck() async {
    if (_disposed) return;
    final bool due = SyncAuditPolicy.isDue(
      now: DateTime.now().millisecondsSinceEpoch,
      lastFullAuditAt: _lastFullAuditAt,
      interval: _automaticFullAuditInterval,
    );
    _reconcileTimer?.cancel();
    await reconcile(reason: 'lifecycle-resume', force: due);
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _flushTimer?.cancel();
    _reconcileTimer?.cancel();
    _retryTimer?.cancel();
    final StreamSubscription<User?>? authSubscription = _authSubscription;
    final StreamSubscription<DatabaseEvent>? connectionSubscription =
        _connectionSubscription;
    final StreamSubscription<DatabaseEvent>? tokenSubscription =
        _tokenSubscription;
    final StreamSubscription<DatabaseEvent>? diaryProjectionSubscription =
        _diaryProjectionSubscription;
    if (authSubscription != null) unawaited(authSubscription.cancel());
    if (connectionSubscription != null) {
      unawaited(connectionSubscription.cancel());
    }
    if (tokenSubscription != null) unawaited(tokenSubscription.cancel());
    if (diaryProjectionSubscription != null) {
      unawaited(diaryProjectionSubscription.cancel());
    }
    _contentChanges.dispose();
    super.dispose();
  }
}

double _cleanZero(double value) => value.abs() < 0.000001 ? 0 : value;

int _asInt(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse('$value') ?? 0;
}
