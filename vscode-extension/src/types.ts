export type UggoLintSeverity = 'error' | 'warning';

export interface UggoLintFinding {
  rule_id: string;
  message: string;
  path: string;
  line: number;
  column: number;
  severity: UggoLintSeverity;
  source: string;
}

export interface UggoLintResult {
  ok: boolean;
  findings: UggoLintFinding[];
  steps: Array<Record<string, unknown>>;
  summary: string;
}
