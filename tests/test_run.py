from pathlib import Path

from uggo_lint.cli import RunPlan, build_run_plan
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
