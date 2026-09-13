import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createNativeApi } from '../src/native-api.ts';
import { calculateAccuracy } from '../src/metrics.ts';

test('native commands receive structured payloads and return typed data directly', async () => {
  const calls = [];
  const api = createNativeApi(async (command, args) => { calls.push([command, args]); return []; });
  assert.deepEqual(await api.getLessons(), []);
  await api.getProgress('Name / with spaces');
  await api.getProgress('User1', 42);
  const input = { username: 'User1', lesson_id: 999, wpm: 42, accuracy: 0 };
  await api.saveProgress(input);
  await api.stopApplication();
  await api.restartApplication();
  assert.deepEqual(calls, [
    ['get_lessons', undefined],
    ['get_progress', { username: 'Name / with spaces', limit: 100, before: null }],
    ['get_progress', { username: 'User1', limit: 100, before: 42 }],
    ['save_progress', { input }], ['stop_application', undefined], ['restart_application', undefined],
  ]);
});

test('a failed native save propagates without automatic duplicate writes', async () => {
  let writes = 0;
  const api = createNativeApi(async () => { writes += 1; throw new Error('Storage unavailable'); });
  await assert.rejects(api.saveProgress({ username: 'User1', lesson_id: 1, wpm: 42, accuracy: 98 }));
  assert.equal(writes, 1);
});

test('accuracy handles zero, empty and partial input', () => {
  assert.equal(calculateAccuracy('xxx', 'abc'), 0);
  assert.equal(calculateAccuracy('', 'abc'), 100);
  assert.equal(calculateAccuracy('abx', 'abc'), 67);
});
