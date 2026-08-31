'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  extractDiaryPaths,
  forceProjectedEntry,
  projectionTask,
  sourceHash,
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
  assert.equal(task.full, false);
  assert.deepEqual(task.paths, ['diaryDB/dia_1']);
  assert.match(taskKey(task), /^0+42_[a-f0-9]{16}$/);
  assert.equal(projectionTask(
    {tables: {diaryDB: 42}},
    {tables: {diaryDB: 42}},
    'same',
    1,
  ), null);
});
