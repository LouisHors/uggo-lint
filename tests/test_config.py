from pathlib import Path

from uggo_lint.config import load_config


def test_load_config_returns_defaults_when_file_missing(tmp_path: Path):
    config = load_config(tmp_path)
    assert config.runner == "golangci-lint"
    assert "goimports" in config.required_tools
    assert config.only_staged is True
    assert config.mode == "default"
    assert config.check_only is False
    assert config.ignore_paths == []
    assert config.ignore_rules == []
    assert config.hook_backend == "native"


def test_load_config_reads_extended_fields_from_yaml(tmp_path: Path):
    config_path = tmp_path / ".uggo-lint.yaml"
    config_path.write_text(
        "\n".join(
            [
                "mode: strict",
                "check_only: true",
                "ignore_paths:",
                "  - vendor/",
                "  - generated/",
                "ignore_rules:",
                "  - no-fire-and-forget-go",
                "hook_backend: pre-commit",
                "required_tools:",
                "  - go",
                "  - golangci-lint",
                "  - goimports",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.mode == "strict"
    assert config.check_only is True
    assert config.ignore_paths == ["vendor/", "generated/"]
    assert config.ignore_rules == ["no-fire-and-forget-go"]
    assert config.hook_backend == "pre-commit"


def test_load_config_strict_mode_extends_default_linters(tmp_path: Path):
    config_path = tmp_path / ".uggo-lint.yaml"
    config_path.write_text("mode: strict\n", encoding="utf-8")

    config = load_config(tmp_path)

    assert "gocritic" in config.default_linters
    assert "revive" in config.default_linters
