'use strict';

const {initializeApp} = require('firebase-admin/app');
const {getDatabase, ServerValue} = require('firebase-admin/database');
const {HttpsError, onCall} = require('firebase-functions/v2/https');
const {onValueWritten} = require('firebase-functions/v2/database');
const {
  SCHEMA_VERSION,
  forceProjectedEntry,
  projectionTask,
  projectionMatchesSourceMetadata,
  sameSourceVersion,
  sourceVersion,
  taskKey,
  updatePeriodIndex,
} = require('./diary_projection');

initializeApp();

const REGION = 'us-central1';
// The lease outlives the 540-second function timeout, so a replacement worker
// can never overlap a still-running projection at the timeout boundary.
const LOCK_MILLIS = 11 * 60 * 1000;
const MAX_REBUILD_ATTEMPTS = 3;
const MAX_QUEUE_PASSES = 100;

function userRoot(uid) {
  return getDatabase().ref(`users/${uid}`);
}

async function projectEntryValue(root, entryId, sourceValue) {
  const projectedRef = root.child(`ledgerV2/diaryEntries/${entryId}`);
  const transaction = await projectedRef.transaction(
    (current) => forceProjectedEntry(current, sourceValue, entryId),
    undefined,
    false,
  );
  if (!transaction.committed) {
    throw new Error(`Diary projection transaction aborted for ${entryId}`);
  }
  const projected = transaction.snapshot.val();
  const periodRef = root.child(`ledgerV2/diaryPeriods/${entryId}`);
  if (!projected) {
    await periodRef.remove();
    return;
  }
  const periodTransaction = await periodRef.transaction(
    (current) => updatePeriodIndex(current, projected),
    undefined,
    false,
  );
  if (!periodTransaction.committed) {
    throw new Error(`Diary period transaction aborted for ${entryId}`);
  }
  if (projected._deleted === true) {
    // The transaction version-orders the delete against older projection work;
    // once accepted, no persistent tombstone is needed in either read index.
    await root.child('ledgerV2').update({
      [`diaryEntries/${entryId}`]: null,
      [`diaryPeriods/${entryId}`]: null,
    });
  }
}

async function projectEntry(root, entryId) {
  const sourceSnapshot = await root.child(`appData/diaryDB/${entryId}`).get();
  await projectEntryValue(root, entryId, sourceSnapshot.val());
}

async function projectEntryIds(root, ids, sourceValues) {
  const hasSourceSnapshot = sourceValues !== undefined;
  for (let offset = 0; offset < ids.length; offset += 20) {
    await Promise.all(ids.slice(offset, offset + 20).map(
      (entryId) => hasSourceSnapshot
        ? projectEntryValue(root, entryId, sourceValues[entryId])
        : projectEntry(root, entryId),
    ));
  }
}

async function removeProjectedEntryIds(root, ids) {
  for (let offset = 0; offset < ids.length; offset += 200) {
    const updates = {};
    for (const entryId of ids.slice(offset, offset + 200)) {
      updates[`diaryEntries/${entryId}`] = null;
      updates[`diaryPeriods/${entryId}`] = null;
    }
    await root.child('ledgerV2').update(updates);
  }
}

async function stableFullRebuild(root) {
  // Never advertise an old projection version while its rows are being
  // rewritten. Clients use `ready` as the read barrier.
  await root.child('ledgerV2/meta/diary').update({
    ready: false,
    schemaVersion: SCHEMA_VERSION,
    updatedAt: ServerValue.TIMESTAMP,
  });
  for (let attempt = 0; attempt < MAX_REBUILD_ATTEMPTS; attempt += 1) {
    const beforeMeta = await root.child('appData/_syncMeta').get();
    const sourceVersionBefore = sourceVersion(beforeMeta.val());
    const [sourceSnapshot, projectedSnapshot] = await Promise.all([
      root.child('appData/diaryDB').get(),
      root.child('ledgerV2/diaryEntries').get(),
    ]);
    const source = sourceSnapshot.val() || {};
    const projected = projectedSnapshot.val() || {};
    const sourceIds = Object.keys(source).sort();
    const sourceIdSet = new Set(sourceIds);
    const deletedIds = Object.keys(projected)
      .filter((entryId) => !sourceIdSet.has(entryId))
      .sort();
    // Reuse the authoritative snapshot already fetched above. Reading every
    // source entry again would turn a full rebuild into N+1 RTDB reads.
    await projectEntryIds(root, sourceIds, source);
    await removeProjectedEntryIds(root, deletedIds);
    const afterMeta = await root.child('appData/_syncMeta').get();
    const confirmed = sourceVersion(afterMeta.val());
    if (!sameSourceVersion(confirmed, sourceVersionBefore)) continue;
    await root.child('ledgerV2/meta/diary').update({
      ready: true,
      schemaVersion: SCHEMA_VERSION,
      sourceRevision: sourceVersionBefore.revision,
      sourceClockHash: sourceVersionBefore.clockHash,
      updatedAt: ServerValue.TIMESTAMP,
    });
    return sourceVersionBefore;
  }
  await root.child('ledgerV2/meta/diary').update({
    ready: false,
    schemaVersion: SCHEMA_VERSION,
    updatedAt: ServerValue.TIMESTAMP,
  });
  throw new Error('Diary changed repeatedly during projection rebuild');
}

async function acquireLock(root, owner) {
  const lockRef = root.child('ledgerV2/_projectionLock/diary');
  const now = Date.now();
  const result = await lockRef.transaction((current) => {
    if (current && current.expiresAt > now && current.owner !== owner) {
      return undefined;
    }
    return {owner, expiresAt: now + LOCK_MILLIS};
  }, undefined, false);
  return result.committed ? lockRef : null;
}

async function releaseLock(lockRef, owner) {
  await lockRef.transaction((current) =>
    current && current.owner === owner ? null : current,
  undefined, false);
}

async function clearQueuedTasks(root, keys) {
  if (keys.length === 0) return;
  const updates = {};
  for (const key of keys) updates[key] = null;
  await root.child('ledgerV2/_projectionQueue/diary').update(updates);
}

async function drainQueue(uid, owner) {
  const root = userRoot(uid);
  const lockRef = await acquireLock(root, owner);
  if (lockRef === null) return false;
  try {
    for (let pass = 0; pass < MAX_QUEUE_PASSES; pass += 1) {
      const [queueSnapshot, projectionMetaSnapshot] = await Promise.all([
        root.child('ledgerV2/_projectionQueue/diary').get(),
        root.child('ledgerV2/meta/diary').get(),
      ]);
      const tasks = [];
      queueSnapshot.forEach((child) => {
        tasks.push({key: child.key, ...(child.val() || {})});
      });
      tasks.sort((left, right) =>
        Number(left.revision) - Number(right.revision) ||
        left.key.localeCompare(right.key),
      );
      if (tasks.length === 0) return true;

      const projectionMeta = projectionMetaSnapshot.val() || {};
      const sourceRevision = Number(projectionMeta.sourceRevision) || 0;
      const sourceClockHash = typeof projectionMeta.sourceClockHash === 'string'
        ? projectionMeta.sourceClockHash
        : '';
      const ready = projectionMeta.ready === true &&
        projectionMeta.schemaVersion === SCHEMA_VERSION &&
        /^[a-f0-9]{64}$/.test(sourceClockHash);
      const next = ready
        ? tasks.find((task) =>
          Number(task.previousRevision) === sourceRevision &&
          task.previousClockHash === sourceClockHash,
        )
        : null;

      if (!next) {
        const sourceMetadataSnapshot = await root.child(
          'appData/_syncMeta',
        ).get();
        if (projectionMatchesSourceMetadata(
          projectionMeta,
          sourceMetadataSnapshot.val(),
        )) {
          await clearQueuedTasks(root, tasks.map((task) => task.key));
          continue;
        }
      }

      if (!next || next.full === true || !Array.isArray(next.paths)) {
        await stableFullRebuild(root);
        await clearQueuedTasks(root, tasks.map((task) => task.key));
        continue;
      }

      const taskSource = {
        revision: Number(next.revision),
        clockHash: String(next.clockHash || ''),
      };
      const sourceBeforeSnapshot = await root.child(
        'appData/_syncMeta',
      ).get();
      const sourceBefore = sourceVersion(sourceBeforeSnapshot.val());

      // projectEntryIds reads live source rows. Do not publish an older queue
      // version if the source has already advanced.
      if (!sameSourceVersion(sourceBefore, taskSource)) {
        await stableFullRebuild(root);
        await clearQueuedTasks(root, tasks.map((task) => task.key));
        continue;
      }

      await root.child('ledgerV2/meta/diary').update({
        ready: false,
        schemaVersion: SCHEMA_VERSION,
        updatedAt: ServerValue.TIMESTAMP,
      });

      const ids = next.paths.map((path) => path.split('/')[1]);
      await projectEntryIds(root, Array.from(new Set(ids)).sort());

      // Fence the live row reads against a concurrent source write.
      const sourceAfterSnapshot = await root.child(
        'appData/_syncMeta',
      ).get();
      const sourceAfter = sourceVersion(sourceAfterSnapshot.val());
      if (!sameSourceVersion(sourceAfter, taskSource)) {
        await stableFullRebuild(root);
        await clearQueuedTasks(root, tasks.map((task) => task.key));
        continue;
      }

      await root.child('ledgerV2').update({
        [`_projectionQueue/diary/${next.key}`]: null,
        'meta/diary/ready': true,
        'meta/diary/schemaVersion': SCHEMA_VERSION,
        'meta/diary/sourceRevision': taskSource.revision,
        'meta/diary/sourceClockHash': taskSource.clockHash,
        'meta/diary/updatedAt': ServerValue.TIMESTAMP,
      });
    }
    const remaining = await root.child(
      'ledgerV2/_projectionQueue/diary',
    ).get();
    if (!remaining.exists()) return true;
    throw new Error('Diary projection queue exceeded its safe drain limit');
  } finally {
    await releaseLock(lockRef, owner);
  }
}

exports.projectDiaryV2 = onValueWritten({
  ref: 'users/{uid}/appData/_syncMeta',
  region: REGION,
  timeoutSeconds: 540,
  memory: '512MiB',
  retry: true,
}, async (event) => {
  const before = event.data.before.val() || {};
  const after = event.data.after.val() || {};
  const task = projectionTask(before, after, event.id, Date.now());
  if (task === null) return;
  const uid = event.params.uid;
  const root = userRoot(uid);
  await root.child(
    `ledgerV2/_projectionQueue/diary/${taskKey(task)}`,
  ).set(task);
  let drained = await drainQueue(uid, event.id);
  if (!drained) {
    await new Promise((resolve) => setTimeout(resolve, 250));
    drained = await drainQueue(uid, `${event.id}:retry`);
  }
  if (!drained) {
    throw new Error('Diary projection lock is busy; retrying queued task.');
  }
});

exports.backfillDiaryV2 = onCall({
  region: REGION,
  timeoutSeconds: 540,
  memory: '512MiB',
}, async (request) => {
  if (!request.auth || request.auth.token.admin !== true) {
    throw new HttpsError('permission-denied', 'Admin claim required.');
  }
  const uid = String(request.data && request.data.uid || '').trim();
  if (!/^[A-Za-z0-9:_-]{1,128}$/.test(uid)) {
    throw new HttpsError('invalid-argument', 'A valid uid is required.');
  }
  const root = userRoot(uid);
  const lockRef = await acquireLock(root, `backfill:${request.auth.uid}`);
  if (lockRef === null) {
    throw new HttpsError('aborted', 'Projection is already running.');
  }
  try {
    const queuedBefore = await root
      .child('ledgerV2/_projectionQueue/diary')
      .get();
    const queuedKeys = [];
    queuedBefore.forEach((child) => queuedKeys.push(child.key));
    const source = await stableFullRebuild(root);
    await clearQueuedTasks(root, queuedKeys);
    return {
      schemaVersion: SCHEMA_VERSION,
      sourceRevision: source.revision,
      sourceClockHash: source.clockHash,
    };
  } finally {
    await releaseLock(lockRef, `backfill:${request.auth.uid}`);
  }
});
