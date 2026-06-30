# uggo-lint VS Code extension

This extension runs the `uggo-lint` CLI from VS Code and shows Go lint findings in the Problems panel.

## Installation

From the Marketplace:

```bash
code --install-extension HorsLouis.uggo-lint
```

From a local VSIX:

```bash
code --install-extension uggo-lint-vscode-0.1.1.vsix
```

## Requirements

Install `uggo-lint` and its Go tool dependencies in your shell environment:

```bash
pipx install uggo-lint
uggo-lint doctor
```

For local development from this repository, install the Python package in editable mode and point VS Code at that executable if needed.

## Features

- Checks the current Go file on save with `uggo-lint check-file <file> --format json`.
- Runs a full workspace check with `uggo-lint run --format json --check-only --all`.
- Shows findings as VS Code diagnostics.
- Provides a doctor command for dependency checks.

## Commands

- `Uggo Lint: Check Current File`
- `Uggo Lint: Check Workspace`
- `Uggo Lint: Doctor`
- `Uggo Lint: Clear Diagnostics`

## Settings

- `uggoLint.executablePath`: path to the `uggo-lint` executable. Defaults to `uggo-lint`.
- `uggoLint.checkOnSave`: run checks when Go files are saved. Defaults to `true`.
- `uggoLint.timeoutMs`: command timeout in milliseconds. Defaults to `30000`.

## Packaging and release

```bash
cd vscode-extension
npm install
npm run vscode:package
npx @vscode/vsce package
```

To publish, configure a Marketplace publisher and set `VSCE_PAT` in your release environment, then run:

```bash
npm run vscode:publish
```

## Local development

```bash
npm install
npm test
npm run compile
```

Open this folder in VS Code, run the `Extension: Start Debugging` workflow, and test the extension in the Extension Development Host.

## Troubleshooting

- If commands fail, run `Uggo Lint: Doctor` and check the `uggo-lint` output channel.
- If `uggo-lint` is not found, set `uggoLint.executablePath` to an absolute path.
- If save checks do not run, confirm the document language mode is Go and `uggoLint.checkOnSave` is enabled.
