from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

DEFAULT_REQUIRED_TOOLS = ["go", "golangci-lint", "goimports"]
DEFAULT_LINTERS = ["govet", "errcheck", "staticcheck"]
STRICT_LINTERS = ["govet", "errcheck", "staticcheck", "gocritic", "revive"]


@dataclass(slots=True)
class UggoLintConfig:
    runner: str = "golangci-lint"
    mode: str = "default"
    only_staged: bool = True
    check_only: bool = False
    hook_backend: str = "native"
    ignore_paths: list[str] = field(default_factory=list)
    ignore_rules: list[str] = field(default_factory=list)
    required_tools: list[str] = field(
        default_factory=lambda: DEFAULT_REQUIRED_TOOLS.copy()
    )
    default_linters: list[str] = field(
        default_factory=lambda: DEFAULT_LINTERS.copy()
    )


def _list_value(raw: object, key: str, default: list[str]) -> list[str]:
    value = raw.get(key, default) if isinstance(raw, dict) else default
    if isinstance(value, list):
        return [str(item) for item in value]
    return default.copy()


def load_config(repo_root: Path) -> UggoLintConfig:
    config_path = repo_root / ".uggo-lint.yaml"
    if not config_path.exists() or yaml is None:
        return UggoLintConfig()

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    mode = raw.get("mode", "default")
    default_linters = (
        STRICT_LINTERS.copy() if mode == "strict" else DEFAULT_LINTERS.copy()
    )
    return UggoLintConfig(
        runner=raw.get("runner", "golangci-lint"),
        mode=mode,
        only_staged=raw.get("only_staged", True),
        check_only=raw.get("check_only", False),
        hook_backend=raw.get("hook_backend", "native"),
        ignore_paths=_list_value(raw, "ignore_paths", []),
        ignore_rules=_list_value(raw, "ignore_rules", []),
        required_tools=_list_value(raw, "required_tools", DEFAULT_REQUIRED_TOOLS),
        default_linters=_list_value(raw, "default_linters", default_linters),
    )
