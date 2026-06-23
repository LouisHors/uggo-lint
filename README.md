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

## License

MIT
