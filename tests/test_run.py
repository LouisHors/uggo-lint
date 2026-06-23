from pathlib import Path

from uggo_lint.cli import RunPlan, build_run_plan


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
