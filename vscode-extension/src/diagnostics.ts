import * as path from 'node:path';
import * as vscode from 'vscode';
import { UggoLintFinding } from './types';

export function makeDiagnosticRange(line: number, column: number): vscode.Range {
  const startLine = Math.max(line - 1, 0);
  const startColumn = Math.max(column - 1, 0);
  return new vscode.Range(startLine, startColumn, startLine, startColumn + 1);
}

export function findingToDiagnostic(finding: UggoLintFinding): vscode.Diagnostic {
  const range = makeDiagnosticRange(finding.line, finding.column);
  const diagnostic = new vscode.Diagnostic(
    range,
    finding.message,
    finding.severity === 'error'
      ? vscode.DiagnosticSeverity.Error
      : vscode.DiagnosticSeverity.Warning,
  );
  diagnostic.source = finding.source || 'uggo-lint';
  diagnostic.code = finding.rule_id;
  return diagnostic;
}

export function diagnosticMetadata(
  finding: UggoLintFinding,
): { severity: string; source: string; code: string | undefined; line: number; column: number } {
  return {
    severity: finding.severity,
    source: finding.source || 'uggo-lint',
    code: finding.rule_id,
    line: finding.line,
    column: finding.column,
  };
}

export function findingsToDiagnostics(
  findings: UggoLintFinding[],
  workspaceRoot: string,
): Map<string, vscode.Diagnostic[]> {
  const grouped = new Map<string, vscode.Diagnostic[]>();
  for (const finding of findings) {
    const filePath = path.isAbsolute(finding.path)
      ? finding.path
      : path.join(workspaceRoot, finding.path);
    const diagnostics = grouped.get(filePath) ?? [];
    diagnostics.push(findingToDiagnostic(finding));
    grouped.set(filePath, diagnostics);
  }
  return grouped;
}
