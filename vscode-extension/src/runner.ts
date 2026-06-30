import { spawn, type SpawnOptionsWithoutStdio } from 'node:child_process';
import { UggoLintResult } from './types';

export interface RunUggoLintOptions {
  executablePath: string;
  args: string[];
  cwd: string;
  timeoutMs: number;
}

export interface RunUggoLintTextResult {
  exitCode: number | null;
  stdout: string;
  stderr: string;
}

export class UggoLintRunnerError extends Error {
  constructor(
    message: string,
    readonly stdout: string = '',
    readonly stderr: string = '',
  ) {
    super(message);
    this.name = 'UggoLintRunnerError';
  }
}

export async function runUggoLintJson(
  options: RunUggoLintOptions,
): Promise<UggoLintResult> {
  const result = await runUggoLintText(options);
  const trimmed = result.stdout.trim();
  try {
    return JSON.parse(trimmed) as UggoLintResult;
  } catch (error) {
    throw new UggoLintRunnerError(
      `uggo-lint did not return valid JSON: ${(error as Error).message}`,
      result.stdout,
      result.stderr,
    );
  }
}

export function runUggoLintText(
  options: RunUggoLintOptions,
): Promise<RunUggoLintTextResult> {
  return new Promise((resolve, reject) => {
    const spawnOptions: SpawnOptionsWithoutStdio = { cwd: options.cwd };
    const child = spawn(options.executablePath, options.args, spawnOptions);
    let stdout = '';
    let stderr = '';
    let settled = false;

    const timeout = setTimeout(() => {
      child.kill();
      if (!settled) {
        settled = true;
        reject(
          new UggoLintRunnerError(
            `uggo-lint timed out after ${options.timeoutMs}ms`,
            stdout,
            stderr,
          ),
        );
      }
    }, options.timeoutMs);

    child.stdout.on('data', (chunk: Buffer) => {
      stdout += chunk.toString('utf8');
    });
    child.stderr.on('data', (chunk: Buffer) => {
      stderr += chunk.toString('utf8');
    });
    child.on('error', (error) => {
      clearTimeout(timeout);
      if (!settled) {
        settled = true;
        reject(new UggoLintRunnerError(error.message, stdout, stderr));
      }
    });
    child.on('close', (exitCode) => {
      clearTimeout(timeout);
      if (!settled) {
        settled = true;
        if (exitCode === null) {
          reject(new UggoLintRunnerError('uggo-lint exited unexpectedly', stdout, stderr));
          return;
        }
        resolve({ exitCode, stdout, stderr });
      }
    });
  });
}
