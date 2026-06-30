import json
from pathlib import Path

from uggo_lint.cli import RunPlan, build_run_plan, run_command
from uggo_lint.config import UggoLintConfig


def test_build_run_plan_skips_when_no_go_files(tmp_path: Path):
    plan = build_run_plan(tmp_path, [], only_staged=True)
    assert plan.should_skip is True
    assert "No staged Go files" in plan.reason


def test_build_run_plan_uses_incremental_golangci_lint(tmp_path: Path):
    plan = build_run_plan(tmp_path, ["main.go"], only_staged=True)
    assert plan.should_skip is False
    assert plan.commands[0] == ["goimports", "-w", "main.go"]
    assert plan.commands[1] == ["git", "add", "--", "main.go"]
    assert "--new" in plan.commands[2]


def test_run_plan_builds_named_steps(tmp_path: Path):
    plan = build_run_plan(tmp_path, ["main.go"], only_staged=True)
    assert isinstance(plan, RunPlan)
    assert plan.step_names == ["format", "restage", "lint"]


def test_build_run_plan_targets_unique_go_directories(tmp_path: Path):
    plan = build_run_plan(
        tmp_path,
        ["cmd/api/main.go", "internal/app/service.go", "cmd/api/http.go"],
        UggoLintConfig(),
    )

    assert plan.commands[-1] == [
        "golangci-lint",
        "run",
        "--new",
        "./cmd/api/...",
        "./internal/app/...",
    ]


def test_build_run_plan_check_only_skips_format_and_restage(tmp_path: Path):
    plan = build_run_plan(
        tmp_path,
        ["cmd/api/main.go"],
        UggoLintConfig(check_only=True),
    )

    assert plan.commands == [["golangci-lint", "run", "--new", "./cmd/api/..."]]
    assert plan.step_names == ["lint"]


def test_run_command_json_skip_output_for_no_staged_files(
    tmp_path: Path, capsys, monkeypatch
):
    monkeypatch.setattr("uggo_lint.cli.get_staged_files", lambda repo_root: [])

    exit_code = run_command(tmp_path, UggoLintConfig(), output_format="json")

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["findings"] == []
    assert "No staged Go files" in payload["summary"]


def test_run_command_json_all_files_reports_custom_rule_findings(
    tmp_path: Path, capsys, monkeypatch
):
    go_file = tmp_path / "main.go"
    go_file.write_text(
        "package main\n\nfunc main() {\n    panic(\"boom\")\n}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("uggo_lint.cli.find_missing_tools", lambda tools: [])

    exit_code = run_command(
        tmp_path,
        UggoLintConfig(required_tools=[]),
        output_format="json",
        check_only=True,
        all_files=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["findings"][0]["path"] == "main.go"
    assert payload["findings"][0]["rule_id"] == "no-panic-outside-tests"
