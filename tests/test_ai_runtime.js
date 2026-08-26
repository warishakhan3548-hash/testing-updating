const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync('/home/ubuntu/testing-updating/index.html', 'utf8');
const start = html.indexOf('window.handleAIPaste = async function() {');
const end = html.indexOf('\n};\n</script>\n<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_END -->', start);
assert(start >= 0 && end > start, 'handler boundaries missing');
const handlerSource = html.slice(start, end + 3);

const textarea = { value: '' };
const sentBatches = [];
const cacheReasons = [];
const state = {
  expenseDB: [{ id: 'old-expense', date: '2026-08-20', category: 'Existing', amount: 10 }],
  udharDB: [], diaryDB: [],
  milkDB: { Alice: { rate: 50, type: 'lene_wala', records: [{ id: 'old-milk', date: '2026-08-20', morning: 2, evening: 1 }] } },
  salaryDB: {}, projectDB: {}
};

function setPath(path, value) {
  const parts = path.split('/');
  const root = parts.shift();
  if (['expenseDB', 'udharDB', 'diaryDB'].includes(root)) {
    const id = parts.shift();
    const list = state[root];
    const index = list.findIndex(item => String(item.id) === id);
    if (index >= 0) {
      if (value === null) list.splice(index, 1);
      else list[index] = value;
    } else if (value !== null) list.unshift(value);
    return;
  }
  const profile = parts.shift();
  if (!state[root][profile]) state[root][profile] = { records: [] };
  if (parts[0] === 'records') {
    const id = parts[1];
    const records = state[root][profile].records || (state[root][profile].records = []);
    const index = records.findIndex(item => String(item.id) === id);
    if (index >= 0) {
      if (value === null) records.splice(index, 1);
      else records[index] = value;
    } else if (value !== null) records.unshift(value);
    return;
  }
  let target = state[root][profile];
  while (parts.length > 1) target = target[parts.shift()] || (target[parts[0]] = {});
  target[parts[0]] = value;
}

const context = {
  console,
  Date,
  Math,
  JSON,
  Set,
  Number,
  String,
  Object,
  Array,
  Promise,
  window: {},
  document: { getElementById: id => id === 'ai-json-paste' ? textarea : { classList: { contains: () => false } } },
  showLoader: () => {},
  hideLoader: () => {},
  closeModal: () => {},
  haptic: () => {},
  showToast: () => {},
  updateDashboard: () => {},
  updateActiveScreen: () => {},
  renderExpenseList: () => {},
  renderUdharList: () => {},
  renderMilkList: () => {},
  renderSalaryList: () => {},
  renderDiaryList: () => {},
  renderProjectsList: () => {},
  getTodayISO: () => '2026-08-26',
  aarishMilkNameKeyCore: name => name.toLowerCase(),
  aarishCostCleanPathV1: path => String(path).replace(/^\/+|\/+$/g, ''),
  aarishCostIsLocalOnlyPathCoreV10: () => false,
  aarishCostApplyMegaToStateCoreV3: payload => {
    for (const [path, value] of Object.entries(payload)) {
      if (!path.startsWith('_syncMeta/')) setPath(path, value);
    }
    return true;
  },
  saveCacheNowCostV81: async reason => { cacheReasons.push(reason); },
  milkDB: state.milkDB,
  salaryDB: state.salaryDB,
  projectDB: state.projectDB,
  expenseDB: state.expenseDB,
  udharDB: state.udharDB,
  diaryDB: state.diaryDB
};
context.window = context;
context.window.aarishFirebaseBatchLaterV87 = async payload => {
  sentBatches.push(payload);
  return { queued: true, writes: Object.keys(payload).length };
};
vm.createContext(context);
vm.runInContext(handlerSource, context);

(async () => {
  const fullState = {
    expenseDB: [
      { id: 'old-expense', date: '2026-08-20', category: 'Existing', amount: 10 },
      { id: 'new-expense', date: '2026-08-26', category: 'Fuel', amount: 120 }
    ],
    milkDB: {
      Alice: {
        rate: 55,
        type: 'lene_wala',
        records: [
          { id: 'old-milk', date: '2026-08-20', morning: 2, evening: 1 },
          { id: 'new-milk', date: '2026-08-26', morning: 3, evening: 2 }
        ]
      }
    }
  };
  textarea.value = '```json\n' + JSON.stringify(fullState) + '\n```';
  await context.window.handleAIPaste();

  assert.strictEqual(state.expenseDB.length, 2, 'existing expense was lost');
  assert(state.expenseDB.some(item => item.id === 'new-expense'), 'new expense was not applied locally');
  assert.strictEqual(state.milkDB.Alice.records.length, 2, 'existing milk record was lost');
  assert(state.milkDB.Alice.records.some(item => item.id === 'new-milk'), 'new milk record was not applied locally');
  const fullBatch = sentBatches[0];
  assert(fullBatch['expenseDB/new-expense'], 'record-level expense write missing');
  assert(!fullBatch.expenseDB, 'destructive expenseDB parent write created');
  assert(fullBatch['milkDB/Alice/records/new-milk'], 'record-level milk write missing');
  assert(!fullBatch['milkDB/Alice'], 'destructive profile parent write created');
  assert(cacheReasons.length > 0, 'local cache was not saved');

  textarea.value = JSON.stringify({ commands: [
    { type: 'expense', date: '2026-08-26', category: 'Taxi', amount: 40 },
    { type: 'expense', date: '2026-08-26', category: 'Taxi', amount: 40 }
  ] });
  await context.window.handleAIPaste();
  const commandBatch = sentBatches[1];
  const commandExpensePaths = Object.keys(commandBatch).filter(path => path.startsWith('expenseDB/'));
  assert.strictEqual(commandExpensePaths.length, 2, 'identical commands collided into one ID');
  assert.notStrictEqual(commandExpensePaths[0], commandExpensePaths[1], 'command IDs are not unique');

  textarea.value = JSON.stringify({ commands: [
    { operation: 'delete', module: 'expense', id: 'new-expense' },
    { operation: 'delete', module: 'milk', name: 'Alice', recordId: 'new-milk' }
  ] });
  await context.window.handleAIPaste();
  const deleteBatch = sentBatches[2];
  assert.strictEqual(deleteBatch['expenseDB/new-expense'], null, 'explicit expense delete was not emitted');
  assert.strictEqual(deleteBatch['milkDB/Alice/records/new-milk'], null, 'explicit grouped-record delete was not emitted');
  assert(!state.expenseDB.some(item => item.id === 'new-expense'), 'deleted expense remains locally');
  assert(!state.milkDB.Alice.records.some(item => item.id === 'new-milk'), 'deleted milk record remains locally');
  assert(state.milkDB.Alice.records.some(item => item.id === 'old-milk'), 'unrelated milk record was deleted');

  console.log('PASS: runtime full-state import preserves old records and adds new records');
  console.log('PASS: runtime command batch gives identical commands distinct IDs');
  console.log('PASS: runtime explicit delete deltas remove only the requested IDs');
  console.log(`PASS: ${sentBatches.length} safe batches queued and ${cacheReasons.length} cache saves completed`);
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
