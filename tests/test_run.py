from pathlib import Path

from uggo_lint.cli import build_run_plan


def test_build_run_plan_skips_when_no_go_files(tmp_path: Path):
    plan = build_run_plan(tmp_path, [], only_staged=True)
    assert plan.should_skip is True
    assert "No staged Go files" in plan.reason
