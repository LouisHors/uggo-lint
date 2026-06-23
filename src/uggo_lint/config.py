from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None


@dataclass(slots=True)
class UggoLintConfig:
    runner: str = "golangci-lint"
    only_staged: bool = True
    required_tools: list[str] = field(
        default_factory=lambda: ["go", "golangci-lint", "goimports"]
    )
    default_linters: list[str] = field(
        default_factory=lambda: ["govet", "errcheck", "staticcheck"]
    )


def load_config(repo_root: Path) -> UggoLintConfig:
    config_path = repo_root / ".uggo-lint.yaml"
    if not config_path.exists() or yaml is None:
        return UggoLintConfig()

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return UggoLintConfig(
        runner=raw.get("runner", "golangci-lint"),
        only_staged=raw.get("only_staged", True),
        required_tools=raw.get(
            "required_tools", ["go", "golangci-lint", "goimports"]
        ),
        default_linters=raw.get(
            "default_linters", ["govet", "errcheck", "staticcheck"]
        ),
    )
