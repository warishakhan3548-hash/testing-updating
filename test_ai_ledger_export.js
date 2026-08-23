const fs = require('fs');
const assert = require('assert/strict');

const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const startMarker = '/* AARISH_AI_MASTER_LEDGER_TEXT_CORE_V1_START */';
const endMarker = '/* AARISH_AI_MASTER_LEDGER_TEXT_CORE_V1_END */';
const start = html.indexOf(startMarker);
const end = html.indexOf(endMarker, start);
assert(start >= 0 && end > start, 'AI Master Ledger block must exist');
const source = html.slice(start, end + endMarker.length);
assert.match(html, /data-format="ai-text"/);
assert.match(html, /aarishExportAiMasterLedgerCoreV1\(safeType, dataset\)/);
assert.match(html, /\[\+ IN\]/);
assert.match(html, /\[- OUT\]/);
assert.match(html, /\[0 NEUTRAL\]/);

const buildLedger = new Function(
  'aarishBuildUnifiedLedgerCoreV2',
  'aarishExportSmartNumberCoreV2',
  'aarishExportMetaCoreV1',
  `${source}; return aarishBuildAiMasterLedgerCoreV1;`
)(
  () => [
    {
      source_module: 'Test Income', source_id: 'test', record_id: 'income-1', record_type: 'BUSINESS_INCOME',
      date_iso: '2026-08-23', date_display: '23/08/2026', counterparty: 'Customer', account: 'Sales',
      owner_action: 'BUSINESS_INCOME', financial_direction: 'INFLOW', amount: 344, signed_amount: 344,
      status: 'RECORDED', description: 'Sale received', ai_interpretation: 'Money inflow', source_key: 'test/income-1'
    },
    {
      source_module: 'Test Expense', source_id: 'test', record_id: 'expense-1', record_type: 'EXPENSE',
      date_iso: '2026-08-23', date_display: '23/08/2026', counterparty: 'Supplier', account: 'Expense',
      owner_action: 'EXPENSE_PAID', financial_direction: 'OUTFLOW', amount: 100, signed_amount: -100,
      status: 'RECORDED', description: 'Bought stock\nwith note', ai_interpretation: 'Money outflow', source_key: 'test/expense-1'
    },
    {
      source_module: 'Personal Diary', source_id: 'diary', record_id: 'diary-1', record_type: 'DIARY_NOTE',
      date_iso: '2026-08-23', date_display: '23/08/2026', counterparty: '', account: 'Personal Diary',
      owner_action: 'NOTE', financial_direction: 'NOT_APPLICABLE', amount: 0, signed_amount: 0,
      status: 'INFORMATIONAL', description: 'Diary first line\nDiary second line',
      ai_interpretation: 'Do not count', source_key: 'diary/diary-1'
    }
  ],
  value => {
    const n = Number(String(value == null ? '' : value).replace(/[₹,\s]/g, ''));
    return Number.isFinite(n) ? n : 0;
  },
  () => ({ title: 'Test Report' })
);

const output = buildLedger('all', { type: 'all', meta: { title: 'Test Report' } });
assert.equal((output.match(/ENTRY #[0-9]+ START/g) || []).length, 3);
assert.equal((output.match(/ENTRY #[0-9]+ END/g) || []).length, 3);
assert.match(output, /IMPACT   :: \[\+ IN\]/);
assert.match(output, /IMPACT   :: \[- OUT\]/);
assert.match(output, /IMPACT   :: \[0 NEUTRAL\]/);
assert.match(output, /TOTAL TO RECEIVE \/ INFLOW\s+: ₹344/);
assert.match(output, /TOTAL TO PAY \/ OUTFLOW\s+: ₹100/);
assert.match(output, /NET SIGNED TOTAL\s+: ₹244/);
assert.match(output, /NEUTRAL \/ NON-FINANCIAL ENTRIES\s+: 1/);
assert.match(output, /Diary first line \/ Diary second line/);
assert.doesNotMatch(output, /Diary first line\nDiary second line/);
console.log('PASS: AI Master Ledger text export boundaries and sign tags');
console.log('PASS: signed totals are 344 inflow, 100 outflow, 244 net');
console.log('PASS: neutral diary entry is excluded from financial totals and newlines are normalized');
