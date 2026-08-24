const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('index.html', 'utf8');

function extractFunction(name) {
  const start = source.indexOf(`function ${name}(`);
  assert(start >= 0, `missing function ${name}`);
  const open = source.indexOf('{', start);
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let i = open; i < source.length; i += 1) {
    const ch = source[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      quote = ch;
      continue;
    }
    if (ch === '{') depth += 1;
    if (ch === '}' && --depth === 0) return source.slice(start, i + 1);
  }
  throw new Error(`unterminated function ${name}`);
}

const context = {
  window: {},
  Date,
  Math,
  Number,
  Object,
  String,
  Array,
  JSON,
  console,
  aarishCostCleanPathV1: (value) => String(value || '').replace(/^\/+|\/+$/g, ''),
  aarishCostIsLocalOnlyPathCoreV10: () => false,
  aarishCostServerTimeV1: () => 123,
};
vm.createContext(context);
[
  'aarishCostSetDeepV1',
  'aarishCostPutCoalescedV1',
  'aarishCostNextRevCoreV8',
  'aarishCostSealMegaCoreV8',
  'aarishCostUpdateLocalTableRevsV1',
].forEach((name) => vm.runInContext(extractFunction(name), context));

const mega = {
  'milkDB/January/records/r1': { id: 'r1' },
  'expenseDB/e1': { id: 'e1' },
};
const rev = context.aarishCostSealMegaCoreV8(mega);
assert(Number.isFinite(rev) && rev > 0);
assert.strictEqual(mega['_syncMeta/tables/milkDB'], rev);
assert.strictEqual(mega['_syncMeta/tables/expenseDB'], rev);
assert.strictEqual(mega['_syncMeta/tables/udharDB'], undefined);

context.aarishCostUpdateLocalTableRevsV1(mega, rev);
assert.strictEqual(Number(context.window.__aarishLocalTableRevs.milkDB), rev);
assert.strictEqual(Number(context.window.__aarishLocalTableRevs.expenseDB), rev);
assert.strictEqual(Object.keys(context.window.__aarishLocalTableRevs).length, 2);

assert(source.includes('async function fullFirebaseSyncCostV81(reason, tablesToFetch)'));
assert(source.includes('ref.child("_syncMeta").once("value")'));
assert(source.includes('await fullFirebaseSyncCostV81("auto-pull-newer-cloud", tablesToFetch)'));
assert(source.includes('tableRevs: tableRevs'));

console.log('PASS: smart-sync table metadata and delta-fetch wiring');
