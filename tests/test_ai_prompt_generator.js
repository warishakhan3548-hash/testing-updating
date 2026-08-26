const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync('/home/ubuntu/testing-updating/index.html', 'utf8');
const start = html.indexOf('window.generateAndCopyAIPrompt = function() {');
const end = html.indexOf('\n};\n\n// ========================== OMNI-AI JSON EXECUTOR CORE ==========================', start);
assert(start >= 0 && end > start, 'prompt generator boundaries missing');
const source = html.slice(start, end + 3);

let downloaded = null;
let clipboardText = '';
let revoked = 0;
let pdfCalls = 0;
const anchor = {
  style: {},
  click() { downloaded = { href: this.href, name: this.download }; },
  remove() {}
};
const context = {
  console,
  Date,
  JSON,
  Math,
  Promise,
  Blob,
  Set,
  String,
  Object,
  window: {},
  navigator: { clipboard: { writeText: async value => { clipboardText = value; } } },
  URL: {
    createObjectURL: blob => { context.__downloadBlob = blob; return 'blob:test'; },
    revokeObjectURL: () => { revoked++; }
  },
  document: {
    createElement: tag => { assert.strictEqual(tag, 'a'); return anchor; },
    body: { appendChild: () => {} }
  },
  setTimeout: callback => { callback(); return 1; },
  showToast: () => {},
  aarishCostGetStateV1: () => ({
    _syncMeta: { rev: 123 },
    expenseDB: [{ id: 'exp_1', amount: 100 }],
    milkDB: { Alice: { records: [{ id: 'milk_1', morning: 2 }] } }
  })
};
context.window = context;
context.window.AarishTitaniumPDF = { renderDataset: () => {} };
context.window.aarishExportPremiumPdfCoreV1 = () => { pdfCalls++; return Promise.resolve(); };
vm.createContext(context);
vm.runInContext(source, context);

(async () => {
  context.window.generateAndCopyAIPrompt();
  await new Promise(resolve => setImmediate(resolve));

  assert(downloaded, 'TXT download was not initiated');
  assert(/^AarishAI_Database_State_\d{4}-\d{2}-\d{2}\.txt$/.test(downloaded.name), 'unexpected TXT filename');
  const exportedText = await context.__downloadBlob.text();
  const json = JSON.parse(exportedText.split('[CURRENT_DATA_JSON_START]\n')[1].split('\n[CURRENT_DATA_JSON_END]')[0]);
  assert(!Object.prototype.hasOwnProperty.call(json, '_syncMeta'), 'sync metadata leaked into AI file');
  assert(json.expenseDB[0].id === 'exp_1', 'record IDs were not retained in AI file');
  assert(clipboardText.includes('[NON-DESTRUCTIVE OUTPUT CONTRACT]'), 'delta contract missing from clipboard prompt');
  assert(clipboardText.includes(downloaded.name), 'clipboard prompt does not reference downloaded file');
  assert(clipboardText.includes('operation":"delete"'), 'delete delta contract missing');
  assert(pdfCalls === 1, 'visual all-PDF trigger did not run exactly once');
  assert(revoked === 1, 'download URL cleanup did not run');

  console.log('PASS: TXT export preserves machine-readable IDs and strips sync metadata');
  console.log('PASS: clipboard prompt references the file and enforces delta-only output');
  console.log('PASS: visual All-PDF trigger runs independently of TXT/clipboard flow');
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
