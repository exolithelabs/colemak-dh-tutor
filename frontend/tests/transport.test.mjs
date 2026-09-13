import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createApiFetch } from '../src/transport.ts';
import { calculateAccuracy } from '../src/metrics.ts';

test('accuracy preserves zero and handles empty, partial and correct input', () => {
  assert.equal(calculateAccuracy('xxx', 'abc'), 0);
  assert.equal(calculateAccuracy('', 'abc'), 100);
  assert.equal(calculateAccuracy('abx', 'abc'), 67);
  assert.equal(calculateAccuracy('ab', 'abc'), 100);
});

const connection = async () => ({ baseUrl: 'http://127.0.0.1:12345', token: 'test-token' });
const noPause = async () => {};

test('waits for readiness and includes authentication without allowing redirects', async () => {
  let checks = 0;
  const api = createApiFetch(connection, async (url, init) => {
    assert.equal(init.headers.get('X-App-Token'), 'test-token');
    assert.equal(init.redirect, 'error');
    assert.equal(init.cache, 'no-store');
    if (url.endsWith('/health') && ++checks < 3) throw new TypeError('Starting');
    return new Response('{}');
  }, noPause);
  assert.equal((await api('/api/lessons')).status, 200);
  assert.equal(checks, 3);
});

test('a lost POST response is never retried', async () => {
  let writes = 0;
  const api = createApiFetch(connection, async (url) => {
    if (url.endsWith('/health')) return new Response('{}');
    writes += 1;
    throw new TypeError('Connection lost after commit');
  }, noPause);
  await assert.rejects(api('/api/user/progress', { method: 'POST' }));
  assert.equal(writes, 1);
});

test('failed startup can be retried and concurrent callers share readiness', async () => {
  let connections = 0;
  const api = createApiFetch(async () => {
    connections += 1;
    if (connections === 1) throw new Error('Not ready');
    return connection();
  }, async () => new Response('{}'), noPause);
  await assert.rejects(api('/api/lessons'));
  await Promise.all([api('/api/lessons'), api('/api/user/progress/User1')]);
  assert.equal(connections, 2);
});

test('rejects paths outside the local API and stops on authentication failure', async () => {
  let requests = 0;
  const api = createApiFetch(connection, async () => {
    requests += 1;
    return new Response('{}', { status: 401 });
  }, noPause);
  await assert.rejects(api('https://example.com'));
  assert.equal(requests, 0);
  await assert.rejects(api('/api/lessons'), /authenticate/);
  assert.equal(requests, 1);
});

test('propagates caller cancellation to the request', async () => {
  const api = createApiFetch(connection, async (url, init) => {
    if (url.endsWith('/health')) return new Response('{}');
    assert.equal(init.signal.aborted, true);
    throw new DOMException('Aborted', 'AbortError');
  }, noPause);
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(api('/api/lessons', { signal: controller.signal }), { name: 'AbortError' });
});
