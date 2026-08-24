import assert from 'node:assert/strict';
import worker from './aaris-ai-agent-worker.js';

const calls = [];
globalThis.fetch = async (input, init = {}) => {
  calls.push({ url: String(input), init });
  if (String(input).includes('/ai_agent_links/')) {
    return new Response(JSON.stringify({ uid: 'user-123', status: 'connected' }), { status: 200 });
  }
  return new Response(JSON.stringify({ ok: true }), { status: 200 });
};

const post = await worker.fetch(new Request('https://worker.example/action', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    code: 'AAR-TEST',
    action_type: 'ADD_EXPENSE',
    payload: { category: 'Sugar', amount: '100', date: '2026-08-24' }
  })
}), { FIREBASE_SECRET: 'test-secret' });

assert.equal(post.status, 200);
assert.deepEqual(await post.json(), { success: true, message: '✅ ADD_EXPENSE added securely!' });
assert.equal(calls.length, 2);
assert.match(calls[1].url, /\/users\/user-123\/appData\/expenseDB\/exp_/);
assert.equal(JSON.parse(calls[1].init.body).amount, 100);

const preflight = await worker.fetch(new Request('https://worker.example/action', { method: 'OPTIONS' }), { FIREBASE_SECRET: 'test-secret' });
assert.equal(preflight.status, 204);
assert.equal(preflight.headers.get('Access-Control-Allow-Methods'), 'POST, OPTIONS');

const unknown = await worker.fetch(new Request('https://worker.example/action', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code: 'AAR-TEST', action_type: 'DELETE_ALL', payload: {} })
}), { FIREBASE_SECRET: 'test-secret' });
assert.equal(unknown.status, 400);

console.log('PASS: action router authentication, strict routing, safe write path, and CORS preflight');
