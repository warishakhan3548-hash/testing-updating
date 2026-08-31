'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  canonicalDiaryClocks,
  diaryClockHash,
  extractDiaryPaths,
  forceProjectedEntry,
  normalizeSourceEntry,
  projectionTask,
  sourceHash,
  sourceVersion,
  strictPeriod,
  taskKey,
  updatePeriodIndex,
} = require('../diary_projection');

test('strictPeriod rejects normalized and malformed calendar dates', () => {
  assert.equal(strictPeriod('2026-08-31'), '2026-08');
  assert.equal(strictPeriod('2026-02-29'), null);
  assert.equal(strictPeriod('2024-02-29'), '2024-02');
  assert.equal(strictPeriod('2026-13-01'), null);
  assert.equal(strictPeriod('2026-08-01T00:00:00Z'), null);
});

test('projected entry is absolute, idempotent, and leaves a tombstone', () => {
  const first = forceProjectedEntry(null, {
    date: '2026-08-01',
    title: 'One',
    _period: 'forged',
  }, 'dia_1');
  assert.equal(first.id, 'dia_1');
  assert.equal(first._period, '2026-08');
  assert.equal(first._version, 1);
  assert.equal(first._deleted, false);
  assert.equal(first.title, 'One');

  const duplicate = forceProjectedEntry(first, {
    date: '2026-08-01',
    title: 'One',
    _period: 'forged',
  }, 'dia_1');
  assert.deepEqual(duplicate, first);

  const moved = forceProjectedEntry(first, {
    date: '2026-09-02',
    title: 'One',
  }, 'dia_1');
  assert.equal(moved._period, '2026-09');
  assert.equal(moved._version, 2);

  const invalid = forceProjectedEntry(moved, {
    date: '2026-02-29',
    title: 'Legacy invalid date',
  }, 'dia_1');
  assert.equal(invalid._period, '_invalid');

  const deleted = forceProjectedEntry(invalid, null, 'dia_1');
  assert.deepEqual(deleted, {
    _deleted: true,
    _period: null,
    _sourceHash: sourceHash(null),
    _version: 4,
  });
});

test('projection strips prototype-pollution field names', () => {
  const malicious = JSON.parse(
    '{"date":"2026-08-31","title":"Safe","__proto__":{"polluted":true},' +
    '"constructor":{"polluted":true},"prototype":{"polluted":true}}',
  );
  const normalized = normalizeSourceEntry(malicious, 'dia_safe');
  assert.equal(normalized.id, 'dia_safe');
  assert.equal(normalized.title, 'Safe');
  assert.equal(Object.hasOwn(normalized, '__proto__'), false);
  assert.equal(Object.hasOwn(normalized, 'constructor'), false);
  assert.equal(Object.hasOwn(normalized, 'prototype'), false);
  assert.equal({}.polluted, undefined);
});

test('period index cannot be rolled back by a late projection event', () => {
  assert.deepEqual(updatePeriodIndex({p: '2026-09', v: 8}, {
    _period: '2026-08',
    _version: 7,
  }), {p: '2026-09', v: 8});
  assert.deepEqual(updatePeriodIndex({p: '2026-08', v: 7}, {
    _period: null,
    _version: 8,
  }), {v: 8});
  assert.deepEqual(updatePeriodIndex({p: '2026-08', v: 8}, {
    _period: '_invalid',
    _version: 9,
  }), {v: 9});
});

test('delta metadata accepts only exact diary record paths', () => {
  assert.deepEqual(extractDiaryPaths({
    deltaWrites: JSON.stringify({
      'diaryDB/dia_1': {title: 'One'},
      'expenseDB/exp_1': {amount: 1},
    }),
  }), ['diaryDB/dia_1']);
  assert.equal(extractDiaryPaths({
    deltaPaths: JSON.stringify(['diaryDB']),
  }), null);
  assert.equal(extractDiaryPaths({
    deltaPaths: JSON.stringify(['diaryDB/bad.key']),
  }), null);
});

test('projection task chains on diary table revisions, not global revisions', () => {
  const task = projectionTask({
    rev: 900,
    tables: {diaryDB: 40},
  }, {
    rev: 999,
    changeToken: 'writer:999:token',
    tables: {diaryDB: 42},
    deltaPaths: JSON.stringify(['diaryDB/dia_1']),
  }, 'event-1', 1234);
  assert.equal(task.previousRevision, 40);
  assert.equal(task.revision, 42);
  assert.equal(task.previousClockHash, diaryClockHash({}));
  assert.equal(task.clockHash, diaryClockHash({}));
  assert.equal(task.full, false);
  assert.deepEqual(task.paths, ['diaryDB/dia_1']);
  assert.match(taskKey(task), /^0+42_[a-f0-9]{16}_[a-f0-9]{16}$/);
  assert.equal(projectionTask(
    {tables: {diaryDB: 42}},
    {tables: {diaryDB: 42}},
    'same',
    1,
  ), null);
});

test('same numeric revision still projects a concurrent writer clock change', () => {
  const before = {
    tables: {diaryDB: 42},
    tableClocks: {
      diaryDB: {writer_device_alpha: 'writer_device_alpha:42:a'},
    },
  };
  const after = {
    ...before,
    changeToken: 'writer_device_bravo:42:b',
    deltaPaths: JSON.stringify(['diaryDB/dia_2']),
    tableClocks: {
      diaryDB: {
        writer_device_alpha: 'writer_device_alpha:42:a',
        writer_device_bravo: 'writer_device_bravo:42:b',
      },
    },
  };

  const task = projectionTask(before, after, 'same-revision-event', 5000);
  assert.notEqual(task, null);
  assert.equal(task.previousRevision, 42);
  assert.equal(task.revision, 42);
  assert.notEqual(task.previousClockHash, task.clockHash);
  assert.deepEqual(task.paths, ['diaryDB/dia_2']);
  assert.deepEqual(sourceVersion(after), {
    revision: 42,
    clockHash: diaryClockHash(after),
  });
});

test('diary clock hash is deterministic and ignores malformed metadata', () => {
  const first = {
    tableClocks: {
      diaryDB: {
        writer_device_bravo: 'b1',
        invalid: 'ignored',
        writer_device_alpha: 'a1',
      },
    },
  };
  const second = {
    tableClocks: {
      diaryDB: {
        writer_device_alpha: 'a1',
        writer_device_bravo: 'b1',
      },
    },
  };
  assert.deepEqual(canonicalDiaryClocks(first), {
    writer_device_alpha: 'a1',
    writer_device_bravo: 'b1',
  });
  assert.equal(diaryClockHash(first), diaryClockHash(second));
  assert.equal(
    diaryClockHash(first),
    '7b9345b4738c69c4c378f449e654fb709886df64add20973866e6ad63d47abf0',
  );
});
