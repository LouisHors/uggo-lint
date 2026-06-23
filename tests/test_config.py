from pathlib import Path

from uggo_lint.config import load_config


def test_load_config_returns_defaults_when_file_missing(tmp_path: Path):
    config = load_config(tmp_path)
    assert config.runner == "golangci-lint"
    assert "goimports" in config.required_tools
    assert config.only_staged is True
