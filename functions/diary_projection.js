'use strict';

const crypto = require('node:crypto');

const SCHEMA_VERSION = 1;
const RESERVED_FIELDS = new Set([
  '_deleted',
  '_period',
  '_sourceHash',
  '_version',
]);

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (!isPlainObject(value)) return value;
  const result = {};
  for (const key of Object.keys(value).sort()) {
    result[key] = stableValue(value[key]);
  }
  return result;
}

function stableStringify(value) {
  return JSON.stringify(stableValue(value));
}

function sourceHash(value) {
  return crypto.createHash('sha256').update(stableStringify(value)).digest('hex');
}

function normalizeSourceEntry(value, entryId) {
  if (!isPlainObject(value)) return null;
  const result = {};
  for (const [key, item] of Object.entries(value)) {
    if (!RESERVED_FIELDS.has(key)) result[key] = item;
  }
  result.id = entryId;
  return result;
}

function strictPeriod(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ''));
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1) return null;
  const maxDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
  if (day > maxDay) return null;
  return `${match[1]}-${match[2]}`;
}

function forceProjectedEntry(storedValue, sourceValue, entryId) {
  const source = normalizeSourceEntry(sourceValue, entryId);
  const nextHash = sourceHash(source);
  const stored = isPlainObject(storedValue) ? storedValue : {};
  const currentHash = typeof stored._sourceHash === 'string'
    ? stored._sourceHash
    : sourceHash(null);
  const currentVersion = Number.isSafeInteger(stored._version)
    ? stored._version
    : 0;
  if (currentHash === nextHash) return stored;
  const version = currentVersion + 1;
  if (source === null) {
    return {
      _deleted: true,
      _period: null,
      _sourceHash: nextHash,
      _version: version,
    };
  }
  return {
    ...source,
    _deleted: false,
    _period: strictPeriod(source.date) || '_invalid',
    _sourceHash: nextHash,
    _version: version,
  };
}

function updatePeriodIndex(storedValue, projectedValue) {
  const stored = isPlainObject(storedValue) ? storedValue : {};
  const projected = isPlainObject(projectedValue) ? projectedValue : {};
  const storedVersion = Number.isSafeInteger(stored.v) ? stored.v : 0;
  const projectedVersion = Number.isSafeInteger(projected._version)
    ? projected._version
    : 0;
  if (storedVersion > projectedVersion) return stored;
  const rawPeriod = typeof projected._period === 'string'
    ? projected._period
    : null;
  const period = /^\d{4}-(0[1-9]|1[0-2])$/.test(rawPeriod || '')
    ? rawPeriod
    : null;
  return period === null
    ? {v: projectedVersion}
    : {p: period, v: projectedVersion};
}

function safeDiaryPath(path) {
  if (typeof path !== 'string' || path.length > 400) return null;
  const parts = path.split('/');
  if (parts.length !== 2 || parts[0] !== 'diaryDB') return null;
  const id = parts[1];
  if (!id || id.length > 180 || /[.#$\[\]\u0000-\u001f\u007f]/.test(id)) {
    return null;
  }
  return path;
}

function parseJsonObject(value, maxLength) {
  if (typeof value !== 'string' || !value || value.length > maxLength) {
    return null;
  }
  try {
    const decoded = JSON.parse(value);
    return isPlainObject(decoded) ? decoded : null;
  } catch (_) {
    return null;
  }
}

function parseJsonPaths(value) {
  if (typeof value !== 'string' || !value || value.length > 1800) return null;
  try {
    const decoded = JSON.parse(value);
    if (!Array.isArray(decoded) || decoded.length < 1 || decoded.length > 24) {
      return null;
    }
    return decoded;
  } catch (_) {
    return null;
  }
}

function extractDiaryPaths(metadata) {
  const meta = isPlainObject(metadata) ? metadata : {};
  const deltaWrites = parseJsonObject(meta.deltaWrites, 2500);
  const candidates = deltaWrites === null
    ? parseJsonPaths(meta.deltaPaths)
    : Object.keys(deltaWrites);
  if (candidates === null) return null;
  const diaryCandidates = candidates.filter((path) =>
    typeof path === 'string' && path.startsWith('diaryDB'),
  );
  if (diaryCandidates.length === 0) return null;
  const result = [];
  for (const path of diaryCandidates) {
    const safe = safeDiaryPath(path);
    if (safe === null) return null;
    if (!result.includes(safe)) result.push(safe);
  }
  return result;
}

function revisionFrom(metadata) {
  const meta = isPlainObject(metadata) ? metadata : {};
  const tables = isPlainObject(meta.tables) ? meta.tables : {};
  const revision = Number(tables.diaryDB);
  return Number.isSafeInteger(revision) && revision >= 0 ? revision : 0;
}

function projectionTask(beforeMetadata, afterMetadata, eventId, now) {
  const previousRevision = revisionFrom(beforeMetadata);
  const revision = revisionFrom(afterMetadata);
  if (revision === previousRevision) return null;
  const token = String(afterMetadata && afterMetadata.changeToken || '');
  return {
    createdAt: now,
    eventId: String(eventId || ''),
    full: extractDiaryPaths(afterMetadata) === null,
    paths: extractDiaryPaths(afterMetadata) || [],
    previousRevision,
    revision,
    tokenHash: sourceHash(token).slice(0, 16),
  };
}

function taskKey(task) {
  return `${String(task.revision).padStart(16, '0')}_${task.tokenHash}`;
}

module.exports = {
  SCHEMA_VERSION,
  extractDiaryPaths,
  forceProjectedEntry,
  normalizeSourceEntry,
  projectionTask,
  revisionFrom,
  sourceHash,
  stableStringify,
  strictPeriod,
  taskKey,
  updatePeriodIndex,
};
