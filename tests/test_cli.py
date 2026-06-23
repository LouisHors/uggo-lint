from pathlib import Path

from uggo_lint import main
from uggo_lint.cli import build_run_plan, install_hooks_command
from uggo_lint.config import UggoLintConfig


def test_main_without_args_prints_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "uggo-lint" in captured.out
    assert "install-hooks" in captured.out
    assert "run" in captured.out


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
