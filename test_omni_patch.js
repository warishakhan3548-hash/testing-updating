const assert = require('node:assert/strict');

let selectedMonth = 7;
let selectedYear = 2026;

function filterByMonth(records) {
  if (!Array.isArray(records)) return [];
  const targetPrefix = String(selectedYear) + '-' + String(selectedMonth + 1).padStart(2, '0');
  return records.filter(r => {
    const value = r && r.date;
    if (typeof value === 'string' && value.length >= 7 && value[4] === '-') {
      return value.startsWith(targetPrefix);
    }
    const p = global.window && global.window.aarishV98DateParts ? global.window.aarishV98DateParts(value) : null;
    return !!p && p.month === selectedMonth && p.year === selectedYear;
  });
}

const records = [
  { date: '2026-08-01' },
  { date: '2026-08-31T23:59:59Z' },
  { date: '2026-07-31' },
  { date: '2026-8-05' },
  { date: '05/08/2026' },
  { date: null },
  {},
];
global.window = {
  aarishV98DateParts(value) {
    if (value === '05/08/2026') return { month: 7, year: 2026 };
    return null;
  },
};
assert.deepEqual(filterByMonth(records).map(r => r.date), ['2026-08-01', '2026-08-31T23:59:59Z', '05/08/2026']);
assert.deepEqual(filterByMonth(null), []);

let animationFrames = 0;
let renderCalls = 0;
global.window = { requestAnimationFrame(callback) { animationFrames += 1; callback(); } };

function __omniDebounce(fn, delay = 150) {
  let timer = null;
  return function(...args) {
    const context = this;
    clearTimeout(timer);
    timer = setTimeout(() => {
      const run = () => fn.apply(context, args);
      if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
        window.requestAnimationFrame(run);
      } else {
        run();
      }
    }, delay);
  };
}

const debouncedRender = __omniDebounce(() => { renderCalls += 1; }, 10);
debouncedRender();
debouncedRender();
setTimeout(() => {
  assert.equal(renderCalls, 1);
  assert.equal(animationFrames, 1);
  console.log('PASS: optimized month filter and shared debounce behavior');
}, 30);
