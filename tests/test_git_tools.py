from pathlib import Path

from uggo_lint.git_tools import build_pre_commit_hook_script, filter_go_files


def test_filter_go_files_keeps_only_go_files():
    files = ["a.go", "README.md", "cmd/main.go", "script.py"]
    assert filter_go_files(files) == ["a.go", "cmd/main.go"]


def test_build_pre_commit_hook_script_references_uggo_lint():
    script = build_pre_commit_hook_script(Path("/repo"))
    assert "uggo-lint run" in script
