from pathlib import Path

from uggo_lint.git_tools import (
    build_pre_commit_hook_script,
    detect_precommit_config,
    filter_go_files,
)


def test_filter_go_files_keeps_only_go_files():
    files = ["a.go", "README.md", "cmd/main.go", "script.py"]
    assert filter_go_files(files) == ["a.go", "cmd/main.go"]


def test_build_pre_commit_hook_script_references_uggo_lint():
    script = build_pre_commit_hook_script(Path("/repo"))
    assert "uggo-lint run" in script


def test_detect_precommit_config_finds_yaml_file(tmp_path: Path):
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

    assert detect_precommit_config(tmp_path) is True


def test_detect_precommit_config_returns_false_without_config(tmp_path: Path):
    assert detect_precommit_config(tmp_path) is False
