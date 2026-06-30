import test from 'node:test';
import assert from 'node:assert/strict';
import { execPath } from 'node:process';
import { runUggoLintJson } from './runner';

test('runUggoLintJson parses valid JSON output', async () => {
  const result = await runUggoLintJson({
    executablePath: execPath,
    args: ['-e', 'console.log(JSON.stringify({ok:true,findings:[],steps:[],summary:"ok"}))'],
    cwd: process.cwd(),
    timeoutMs: 30000,
  });

  assert.equal(result.ok, true);
  assert.deepEqual(result.findings, []);
});

test('runUggoLintJson accepts non-zero exit when stdout is valid JSON', async () => {
  const result = await runUggoLintJson({
    executablePath: execPath,
    args: ['-e', 'console.log(JSON.stringify({ok:false,findings:[],steps:[],summary:"failed"})); process.exit(1)'],
    cwd: process.cwd(),
    timeoutMs: 30000,
  });

  assert.equal(result.ok, false);
  assert.equal(result.summary, 'failed');
});

test('runUggoLintJson rejects invalid JSON output', async () => {
  await assert.rejects(
    runUggoLintJson({
      executablePath: execPath,
      args: ['-e', 'console.log("not json")'],
      cwd: process.cwd(),
      timeoutMs: 30000,
    }),
    /valid JSON/,
  );
});
