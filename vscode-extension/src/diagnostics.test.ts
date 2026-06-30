import test from 'node:test';
import assert from 'node:assert/strict';
import { diagnosticMetadata, findingsToDiagnostics, makeDiagnosticRange } from './diagnostics';
import { UggoLintFinding } from './types';

const finding: UggoLintFinding = {
  rule_id: 'no-panic-outside-tests',
  message: 'Avoid panic() outside tests; return errors instead.',
  path: 'main.go',
  line: 4,
  column: 5,
  severity: 'error',
  source: 'uggo-lint',
};

test('makeDiagnosticRange converts 1-based positions to 0-based range', () => {
  const range = makeDiagnosticRange(4, 5);

  assert.equal(range.start.line, 3);
  assert.equal(range.start.character, 4);
});

test('diagnosticMetadata preserves key finding data', () => {
  const metadata = diagnosticMetadata(finding);

  assert.equal(metadata.severity, 'error');
  assert.equal(metadata.source, 'uggo-lint');
  assert.equal(metadata.code, 'no-panic-outside-tests');
  assert.equal(metadata.line, 4);
  assert.equal(metadata.column, 5);
});

test('findingsToDiagnostics groups diagnostics by file path', () => {
  const grouped = findingsToDiagnostics([finding], '/workspace/project');

  assert.equal(grouped.size, 1);
  assert.equal(grouped.get('/workspace/project/main.go')?.length, 1);
});
