# uggo-lint

`uggo-lint` is a reusable Git hook and `pre-commit` helper for Go repositories.

It combines:

- existing lint tools like `golangci-lint`, `goimports`, `go vet`
- lightweight custom rules inspired by the Uber Go Style Guide
- Git `pre-commit` installation
- `pre-commit` framework config output

## Commands

```bash
uggo-lint doctor
uggo-lint run
uggo-lint run --format json --check-only --all
uggo-lint check-file path/to/file.go --format json
uggo-lint install-hooks
uggo-lint print-precommit-config
```

## Requirements

- Python 3.11+
- Go
- `golangci-lint`
- `goimports`

## Configuration

`uggo-lint` reads repository-level settings from `.uggo-lint.yaml`.

Useful fields:

- `mode`: `default` or `strict`
- `only_staged`: only lint staged Go files when true
- `check_only`: skip formatting and only run lint checks
- `hook_backend`: `native`, `pre-commit`, or `auto`
- `ignore_paths`: directories or path prefixes reserved for future filtering
- `ignore_rules`: custom rules reserved for future filtering

## Run behavior

`uggo-lint run` follows this flow:

- collect staged `.go` files
- group them by directory to build focused `golangci-lint` targets
- run `goimports` and re-stage files unless `check_only: true`
- print grouped step failure output with command, exit code, and stderr details

## Editor integration

`uggo-lint` also exposes editor-friendly commands for tools like VS Code:

- `uggo-lint check-file <path> --format json` checks a single Go file and returns JSON findings.
- `uggo-lint run --format json --check-only --all` checks the whole workspace without formatting or re-staging.

The VS Code extension in `vscode-extension/` consumes these JSON commands and maps findings into the Problems panel.

### Packaging and releasing the VS Code extension

From the `vscode-extension` directory:

```bash
npm install
npm run vscode:package
npx @vscode/vsce package
```

Install the resulting `.vsix`:

```bash
code --install-extension uggo-lint-vscode-0.1.1.vsix --force
```

To publish to the Marketplace, create a `VSCE_PAT` secret and push a `vscode-v*` tag, or trigger the `publish-vscode-extension` workflow manually.

## Built-in custom rules

Current low-false-positive rules:

- `no-init`: flags `func init()` and prefers explicit setup
- `no-panic-outside-tests`: blocks `panic()` outside `*_test.go`
- `no-fire-and-forget-go`: warns on bare `go ...` calls for manual review
- `context-first`: warns when `context.Context` is not the first function parameter
- `error-string-style`: warns when `errors.New(...)` starts uppercase or ends with punctuation
- `receiver-name-consistency`: warns when methods of the same type use different receiver names

Notes:

- test files are intentionally exempt from the style-oriented `context-first` and `error-string-style` checks
- these rules use lightweight text matching, so they aim for clear, common violations instead of deep AST analysis

## Hook integration

`uggo-lint` supports three hook setup paths:

1. Native Git hook:

```bash
uggo-lint install-hooks
```

2. Existing local `pre-commit` config:

```bash
uggo-lint print-precommit-config
```

3. Reusable pre-commit repo metadata:

- `.pre-commit-hooks.yaml`

If `hook_backend: auto` and a repository already contains `.pre-commit-config.yaml`,
`uggo-lint install-hooks` will tell you to use the pre-commit path instead of writing
to `.git/hooks/pre-commit`.

## Team adoption

`uggo-lint` works best for Go repositories that:

- already use `golangci-lint` and want a lighter pre-commit entry point
- want a shared style baseline plus a few Uber Go Guide-inspired checks
- need consistent local and CI lint behavior without rewriting the whole toolchain

Recommended rollout:

1. Install required tools on developer machines:
   - Go
   - `golangci-lint`
   - `goimports`
   - Python 3.11+
2. Add `.uggo-lint.yaml` with your preferred `mode` and `hook_backend`
3. Pick either native Git hooks or `pre-commit`
4. Reuse the CI example from `examples/github-actions-go.yml`

To reduce “local passes, CI fails” drift:

- pin the same `golangci-lint` version in CI and developer setup docs
- run `uggo-lint doctor` in CI before `uggo-lint run`
- prefer `check_only: true` in CI-style invocations so formatting stays explicit

## Installation

Editable install for local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

With `pipx`:

```bash
pipx install .
```

After installation, verify the CLI entrypoint:

```bash
uggo-lint doctor
uggo-lint --help
```

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e . pytest
pytest -v
```

## Example config

See:

- `examples/uggo-lint-config.example.yaml`

Example:

```yaml
mode: strict
only_staged: true
check_only: false
hook_backend: auto
ignore_paths:
  - vendor/
ignore_rules:
  - no-fire-and-forget-go
```

## License

MIT
