from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from uggo_lint.config import UggoLintConfig, load_config
from uggo_lint.git_tools import (
    build_pre_commit_hook_script,
    filter_go_files,
    get_staged_files,
)
from uggo_lint.rules import Finding, run_custom_rules
from uggo_lint.runtime import find_missing_tools, format_missing_tools


@dataclass(slots=True)
class RunPlan:
    should_skip: bool
    reason: str = ""
    go_files: list[str] = field(default_factory=list)
    commands: list[list[str]] = field(default_factory=list)
    step_names: list[str] = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uggo-lint")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run")
    subparsers.add_parser("install-hooks")
    subparsers.add_parser("print-precommit-config")
    subparsers.add_parser("doctor")
    return parser


def build_run_plan(
    repo_root: Path,
    go_files: list[str],
    config: UggoLintConfig | bool | None = None,
    *,
    only_staged: bool | None = None,
) -> RunPlan:
    if isinstance(config, UggoLintConfig):
        config_obj = config
    else:
        config_obj = UggoLintConfig(
            only_staged=only_staged if only_staged is not None else bool(config),
        )

    only_staged_value = config_obj.only_staged
    check_only = config_obj.check_only
    if only_staged_value and not go_files:
        return RunPlan(should_skip=True, reason="No staged Go files. Skipping lint run.")

    commands = [["golangci-lint", "run", "--new", "./..."]]
    step_names = ["lint"]
    if not check_only:
        commands = [
            ["goimports", "-w", *go_files],
            ["git", "add", "--", *go_files],
            *commands,
        ]
        step_names = ["format", "restage", *step_names]

    return RunPlan(
        should_skip=False,
        go_files=go_files,
        commands=commands,
        step_names=step_names,
    )


def render_precommit_config() -> str:
    return """repos:
- repo: local
  hooks:
  - id: uggo-lint
    name: uggo-lint
    entry: uggo-lint run
    language: system
    pass_filenames: false
"""


def print_findings(findings: list[Finding], repo_root: Path) -> None:
    for finding in findings:
        try:
            rel_path = Path(finding.path).resolve().relative_to(repo_root.resolve())
        except ValueError:
            rel_path = Path(finding.path)
        print(f"[{finding.severity}] {finding.rule_id}: {rel_path} - {finding.message}")


def run_process(command: list[str], repo_root: Path, step_name: str) -> int:
    try:
        subprocess.run(command, cwd=repo_root, check=True)
    except subprocess.CalledProcessError as exc:
        rendered = " ".join(command)
        print(f"uggo-lint step failed: {step_name}")
        print(f"Command: {rendered}")
        print(f"Exit code: {exc.returncode}")
        return exc.returncode
    return 0


def run_command(repo_root: Path, config: UggoLintConfig) -> int:
    staged_files = get_staged_files(repo_root)
    go_files = filter_go_files(staged_files)
    plan = build_run_plan(repo_root, go_files, config)
    if plan.should_skip:
        print(plan.reason)
        return 0

    missing = find_missing_tools(config.required_tools)
    if missing:
        print(format_missing_tools(missing))
        return 1

    findings: list[Finding] = []
    for go_file in plan.go_files:
        file_path = repo_root / go_file
        if file_path.exists():
            findings.extend(run_custom_rules(file_path))

    if findings:
        print_findings(findings, repo_root)
        if any(f.severity == "error" for f in findings):
            return 1

    for step_name, command in zip(plan.step_names, plan.commands):
        exit_code = run_process(command, repo_root, step_name)
        if exit_code != 0:
            return exit_code

    print("uggo-lint checks passed.")
    return 0


def doctor_command(config: UggoLintConfig) -> int:
    missing = find_missing_tools(config.required_tools)
    if missing:
        print(format_missing_tools(missing))
        return 1
    print("All required tools are available.")
    return 0


def install_hooks_command(repo_root: Path, config: UggoLintConfig) -> int:
    if config.hook_backend != "native":
        print(
            "Configured hook backend is not 'native'. "
            "Use 'uggo-lint print-precommit-config' for pre-commit integration."
        )
        return 0

    hook_path = repo_root / ".git" / "hooks" / "pre-commit"
    backup_path = repo_root / ".git" / "hooks" / "pre-commit.uggo-lint.bak"
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    if hook_path.exists():
        backup_path.write_text(hook_path.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        hook_path.write_text(build_pre_commit_hook_script(repo_root), encoding="utf-8")
        hook_path.chmod(0o755)
    except PermissionError:
        print(
            "Permission denied while writing .git/hooks/pre-commit. "
            "Install the hook in a writable repository or adjust permissions."
        )
        return 1

    print(f"Installed pre-commit hook at {hook_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    repo_root = Path.cwd()
    config = load_config(repo_root)

    if args.command == "run":
        return run_command(repo_root, config)
    if args.command == "doctor":
        return doctor_command(config)
    if args.command == "install-hooks":
        return install_hooks_command(repo_root, config)
    if args.command == "print-precommit-config":
        print(render_precommit_config())
        return 0

    parser.print_help()
    return 0
