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
hook_backend: native
ignore_paths:
  - vendor/
ignore_rules:
  - no-fire-and-forget-go
```

## License

MIT
