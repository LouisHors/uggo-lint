import * as vscode from 'vscode';

export interface UggoLintConfig {
  executablePath: string;
  checkOnSave: boolean;
  timeoutMs: number;
}

export function getUggoLintConfig(): UggoLintConfig {
  const config = vscode.workspace.getConfiguration('uggoLint');
  return {
    executablePath: config.get<string>('executablePath', 'uggo-lint'),
    checkOnSave: config.get<boolean>('checkOnSave', true),
    timeoutMs: config.get<number>('timeoutMs', 30000),
  };
}
