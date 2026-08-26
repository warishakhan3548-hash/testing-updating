const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync('/home/ubuntu/testing-updating/index.html', 'utf8');
const start = html.indexOf('window.handleAIPaste = async function() {');
const end = html.indexOf('\n};\n</script>\n<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_END -->', start);
assert(start >= 0 && end > start, 'handler boundaries missing');

const textarea = { value: '' };
const state = {
  expenseDB: [], udharDB: [], diaryDB: [],
  milkDB: { Alice: { records: [] } }, salaryDB: {}, projectDB: {}
};
const batches = [];

function setPath(path, value) {
  const parts = path.split('/');
  const root = parts.shift();
  if (['expenseDB', 'udharDB', 'diaryDB'].includes(root)) {
    const id = parts.shift();
    const list = state[root];
    const index = list.findIndex(item => String(item.id) === id);
    if (index >= 0) value === null ? list.splice(index, 1) : (list[index] = value);
    else if (value !== null) list.unshift(value);
    return;
  }
  const profile = parts.shift();
  if (!state[root][profile]) state[root][profile] = { records: [] };
  if (parts[0] !== 'records') {
    state[root][profile][parts[0]] = value;
    return;
  }
  const id = parts[1];
  const records = state[root][profile].records;
  const index = records.findIndex(item => String(item.id) === id);
  if (index >= 0) value === null ? records.splice(index, 1) : (records[index] = value);
  else if (value !== null) records.unshift(value);
}

const context = {
  console, Date, JSON, Math, Set, Number, String, Object, Array, Promise,
  window: {},
  document: { getElementById: id => id === 'ai-json-paste' ? textarea : {} },
  getTodayISO: () => '2026-08-26',
  showLoader: () => {}, hideLoader: () => {}, closeModal: () => {}, haptic: () => {},
  showToast: () => {}, updateDashboard: () => {}, updateActiveScreen: () => {},
  renderExpenseList: () => {}, renderMilkList: () => {}, renderUdharList: () => {},
  renderDiaryList: () => {}, renderSalaryList: () => {}, renderProjectsList: () => {},
  aarishCostCleanPathV1: path => String(path).replace(/^\/+|\/+$/g, ''),
  aarishCostIsLocalOnlyPathCoreV10: () => false,
  aarishCostApplyMegaToStateCoreV3: payload => {
    for (const [path, value] of Object.entries(payload)) setPath(path, value);
  },
  saveCacheNowCostV81: async () => {},
  milkDB: state.milkDB, salaryDB: state.salaryDB, projectDB: state.projectDB,
  expenseDB: state.expenseDB, udharDB: state.udharDB, diaryDB: state.diaryDB
};
context.window = context;
context.window.aarishFirebaseBatchLaterV87 = async payload => {
  batches.push(payload);
  return { queued: true, writes: Object.keys(payload).length };
};
vm.createContext(context);
vm.runInContext(html.slice(start, end + 3), context);

(async () => {
  textarea.value = JSON.stringify([
    { path: 'expenseDB/ai-expense', data: { id: 'ai-expense', date: '2026-08-26', category: 'Fuel', amount: 120 } },
    { path: 'milkDB/Alice/records/ai-milk', data: { id: 'ai-milk', date: '2026-08-26', morning: 3, evening: 2 } },
    { path: 'expenseDB/ai-expense', data: null },
    { path: 'milkDB/Alice', data: { records: [] } },
    { path: 'expenseDB/_syncMeta', data: { bad: true } }
  ]);
  await context.window.handleAIPaste();

  assert.strictEqual(batches.length, 1, 'one batch should be queued');
  assert.strictEqual(batches[0]['expenseDB/ai-expense'], null, 'last valid delta should delete the expense');
  assert(batches[0]['milkDB/Alice/records/ai-milk'], 'grouped record delta was not queued');
  assert(!Object.prototype.hasOwnProperty.call(batches[0], 'milkDB/Alice'), 'profile parent write was accepted');
  assert(!Object.keys(batches[0]).some(path => path.includes('_syncMeta')), 'sync metadata path was accepted');
  assert(!state.expenseDB.some(item => item.id === 'ai-expense'), 'deleted expense remains locally');
  assert(state.milkDB.Alice.records.some(item => item.id === 'ai-milk'), 'grouped record was not applied locally');
  console.log('PASS: direct path/data deltas support safe add/edit/delete without destructive parent writes');
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});

