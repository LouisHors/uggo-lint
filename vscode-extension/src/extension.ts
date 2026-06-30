import * as path from 'node:path';
import * as vscode from 'vscode';
import { getUggoLintConfig } from './config';
import { findingsToDiagnostics } from './diagnostics';
import { runUggoLintJson, runUggoLintText, UggoLintRunnerError } from './runner';

let collection: vscode.DiagnosticCollection;
let output: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
  collection = vscode.languages.createDiagnosticCollection('uggo-lint');
  output = vscode.window.createOutputChannel('uggo-lint');

  context.subscriptions.push(
    collection,
    output,
    vscode.commands.registerCommand('uggoLint.checkCurrentFile', checkCurrentFile),
    vscode.commands.registerCommand('uggoLint.checkWorkspace', checkWorkspace),
    vscode.commands.registerCommand('uggoLint.doctor', doctor),
    vscode.commands.registerCommand('uggoLint.clearDiagnostics', () => collection.clear()),
    vscode.workspace.onDidSaveTextDocument((document) => {
      const config = getUggoLintConfig();
      if (config.checkOnSave && document.languageId === 'go') {
        void checkDocument(document);
      }
    }),
  );
}

export function deactivate() {
  collection?.dispose();
  output?.dispose();
}

async function checkCurrentFile() {
  const document = vscode.window.activeTextEditor?.document;
  if (!document) {
    vscode.window.showInformationMessage('No active editor to check.');
    return;
  }
  if (document.languageId !== 'go') {
    vscode.window.showInformationMessage('The active file is not a Go file.');
    return;
  }
  await checkDocument(document);
}

async function checkDocument(document: vscode.TextDocument) {
  const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
  if (!workspaceFolder) {
    vscode.window.showWarningMessage('uggo-lint requires a workspace folder.');
    return;
  }
  const config = getUggoLintConfig();
  await runAndApplyDiagnostics({
    args: ['check-file', document.uri.fsPath, '--format', 'json'],
    cwd: workspaceFolder.uri.fsPath,
    targetOnly: document.uri.fsPath,
    executablePath: config.executablePath,
    timeoutMs: config.timeoutMs,
  });
}

async function checkWorkspace() {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    vscode.window.showWarningMessage('uggo-lint requires a workspace folder.');
    return;
  }
  const config = getUggoLintConfig();
  await runAndApplyDiagnostics({
    args: ['run', '--format', 'json', '--check-only', '--all'],
    cwd: workspaceFolder.uri.fsPath,
    executablePath: config.executablePath,
    timeoutMs: config.timeoutMs,
  });
}

async function doctor() {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    vscode.window.showWarningMessage('uggo-lint requires a workspace folder.');
    return;
  }
  const config = getUggoLintConfig();
  try {
    const result = await runUggoLintText({
      executablePath: config.executablePath,
      args: ['doctor'],
      cwd: workspaceFolder.uri.fsPath,
      timeoutMs: config.timeoutMs,
    });
    output.clear();
    output.append(result.stdout);
    output.append(result.stderr);
    output.show(true);
  } catch (error) {
    showRunnerError(error);
  }
}

async function runAndApplyDiagnostics(options: {
  executablePath: string;
  args: string[];
  cwd: string;
  timeoutMs: number;
  targetOnly?: string;
}) {
  try {
    const result = await runUggoLintJson(options);
    if (options.targetOnly) {
      collection.delete(vscode.Uri.file(options.targetOnly));
    } else {
      collection.clear();
    }
    const grouped = findingsToDiagnostics(result.findings, options.cwd);
    for (const [filePath, diagnostics] of grouped) {
      collection.set(vscode.Uri.file(path.resolve(filePath)), diagnostics);
    }
    if (!result.ok || result.findings.length > 0) {
      output.appendLine(result.summary);
    }
  } catch (error) {
    showRunnerError(error);
  }
}

function showRunnerError(error: unknown) {
  const runnerError = error as UggoLintRunnerError;
  output.appendLine(runnerError.message ?? String(error));
  if (runnerError.stdout) {
    output.appendLine(runnerError.stdout);
  }
  if (runnerError.stderr) {
    output.appendLine(runnerError.stderr);
  }
  output.show(true);
  vscode.window.showWarningMessage('uggo-lint failed. See the uggo-lint output channel.');
}
