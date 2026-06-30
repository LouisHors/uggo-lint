import json
from pathlib import Path

from uggo_lint import main
from uggo_lint.cli import build_run_plan, check_file_command, install_hooks_command
from uggo_lint.config import UggoLintConfig


def test_main_without_args_prints_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "uggo-lint" in captured.out
    assert "install-hooks" in captured.out
    assert "run" in captured.out
    assert "check-file" in captured.out


def test_build_run_plan_honors_check_only_mode(tmp_path: Path):
    config = UggoLintConfig(check_only=True)

    plan = build_run_plan(tmp_path, ["main.go"], config)

    assert plan.commands == [["golangci-lint", "run", "--new", "./..."]]
    assert plan.step_names == ["lint"]


def test_install_hooks_command_skips_native_write_for_precommit_backend(
    tmp_path: Path, capsys
):
    exit_code = install_hooks_command(tmp_path, UggoLintConfig(hook_backend="pre-commit"))

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "pre-commit integration" in captured.out
    assert not (tmp_path / ".git" / "hooks" / "pre-commit").exists()


def test_install_hooks_command_auto_detects_precommit_repo(tmp_path: Path, capsys):
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

    exit_code = install_hooks_command(tmp_path, UggoLintConfig(hook_backend="auto"))

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Detected pre-commit configuration" in captured.out
    assert not (tmp_path / ".git" / "hooks" / "pre-commit").exists()


def test_check_file_command_outputs_json_for_single_file(tmp_path: Path, capsys):
    go_file = tmp_path / "main.go"
    go_file.write_text(
        "package main\n\nfunc main() {\n    panic(\"boom\")\n}\n",
        encoding="utf-8",
    )

    exit_code = check_file_command(tmp_path, go_file, "json")

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["findings"][0]["rule_id"] == "no-panic-outside-tests"
    assert payload["findings"][0]["path"] == "main.go"
    assert payload["findings"][0]["line"] == 4
    assert payload["findings"][0]["column"] > 0
    assert payload["findings"][0]["source"] == "uggo-lint"


def test_check_file_command_returns_success_for_warning_only(tmp_path: Path, capsys):
    go_file = tmp_path / "main.go"
    go_file.write_text(
        "package main\n\nfunc main() {\n    go work()\n}\n\nfunc work() {}\n",
        encoding="utf-8",
    )

    exit_code = check_file_command(tmp_path, go_file, "json")

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["findings"][0]["severity"] == "warning"


def test_check_file_command_reports_missing_file_as_json(tmp_path: Path, capsys):
    exit_code = check_file_command(tmp_path, Path("missing.go"), "json")

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["findings"] == []
    assert "File does not exist" in payload["summary"]


def test_main_check_file_accepts_json_format(tmp_path: Path, capsys, monkeypatch):
    go_file = tmp_path / "main.go"
    go_file.write_text("package main\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check-file", "main.go", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
