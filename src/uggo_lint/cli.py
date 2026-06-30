from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from uggo_lint.config import UggoLintConfig, load_config
from uggo_lint.git_tools import (
    build_pre_commit_hook_script,
    detect_precommit_config,
    filter_go_files,
    get_staged_files,
)
from uggo_lint.rules import Finding, run_custom_rules
from uggo_lint.output import render_error_result, render_json_result
from uggo_lint.runtime import (
    find_missing_tools,
    format_missing_tools,
    format_process_failure,
)


@dataclass(slots=True)
class RunPlan:
    should_skip: bool
    reason: str = ""
    go_files: list[str] = field(default_factory=list)
    lint_targets: list[str] = field(default_factory=list)
    commands: list[list[str]] = field(default_factory=list)
    step_names: list[str] = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uggo-lint")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--format", choices=("text", "json"), default="text")
    run_parser.add_argument("--check-only", action="store_true")
    run_parser.add_argument(
        "--all",
        action="store_true",
        help="check all Go files instead of only staged Go files",
    )

    check_file_parser = subparsers.add_parser("check-file")
    check_file_parser.add_argument("path")
    check_file_parser.add_argument("--format", choices=("text", "json"), default="text")

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

    lint_targets = sorted(
        {
            f"./{directory.as_posix()}/..." if directory.as_posix() != "." else "./..."
            for directory in (Path(go_file).parent for go_file in go_files)
        }
    )
    commands = [["golangci-lint", "run", "--new", *lint_targets]]
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
        lint_targets=lint_targets,
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
        print(
            f"[{finding.severity}] {finding.rule_id}: "
            f"{rel_path}:{finding.line}:{finding.column} - {finding.message}"
        )


def collect_go_files(repo_root: Path, *, all_files: bool) -> list[str]:
    if not all_files:
        return filter_go_files(get_staged_files(repo_root))
    return sorted(
        path.relative_to(repo_root).as_posix()
        for path in repo_root.rglob("*.go")
        if ".git" not in path.relative_to(repo_root).parts
    )


def run_process(command: list[str], repo_root: Path, step_name: str) -> int:
    try:
        subprocess.run(command, cwd=repo_root, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        print(format_process_failure(step_name, exc))
        return exc.returncode
    return 0


def run_command(
    repo_root: Path,
    config: UggoLintConfig,
    *,
    output_format: str = "text",
    check_only: bool = False,
    all_files: bool = False,
) -> int:
    if check_only or all_files:
        config = UggoLintConfig(
            runner=config.runner,
            mode=config.mode,
            only_staged=False if all_files else config.only_staged,
            check_only=True if check_only else config.check_only,
            hook_backend=config.hook_backend,
            ignore_paths=config.ignore_paths,
            ignore_rules=config.ignore_rules,
            required_tools=config.required_tools,
            default_linters=config.default_linters,
        )

    go_files = collect_go_files(repo_root, all_files=all_files)
    plan = build_run_plan(repo_root, go_files, config)
    if plan.should_skip:
        if output_format == "json":
            print(render_json_result(True, [], repo_root, summary=plan.reason))
        else:
            print(plan.reason)
        return 0

    missing = find_missing_tools(config.required_tools)
    if missing:
        message = format_missing_tools(missing)
        if output_format == "json":
            print(render_error_result(message, repo_root))
        else:
            print(message)
        return 1

    findings: list[Finding] = []
    for go_file in plan.go_files:
        file_path = repo_root / go_file
        if file_path.exists():
            findings.extend(run_custom_rules(file_path))

    if findings:
        if output_format == "json":
            ok = not any(f.severity == "error" for f in findings)
            print(render_json_result(ok, findings, repo_root))
        else:
            print_findings(findings, repo_root)
        if any(f.severity == "error" for f in findings):
            return 1

    for step_name, command in zip(plan.step_names, plan.commands):
        exit_code = run_process(command, repo_root, step_name)
        if exit_code != 0:
            if output_format == "json":
                print(render_error_result(f"uggo-lint step failed: {step_name}", repo_root))
            return exit_code

    if output_format == "json":
        print(render_json_result(True, findings, repo_root))
    else:
        print("uggo-lint checks passed.")
    return 0


def check_file_command(repo_root: Path, path: Path, output_format: str = "text") -> int:
    file_path = path if path.is_absolute() else repo_root / path
    if not file_path.exists():
        message = f"File does not exist: {path}"
        if output_format == "json":
            print(render_error_result(message, repo_root))
        else:
            print(message)
        return 1
    if file_path.suffix != ".go":
        message = f"Not a Go file: {path}"
        if output_format == "json":
            print(render_error_result(message, repo_root))
        else:
            print(message)
        return 1

    findings = run_custom_rules(file_path)
    ok = not any(finding.severity == "error" for finding in findings)
    if output_format == "json":
        print(render_json_result(ok, findings, repo_root))
    elif findings:
        print_findings(findings, repo_root)
    else:
        print("uggo-lint checks passed.")
    return 0 if ok else 1


def doctor_command(config: UggoLintConfig) -> int:
    missing = find_missing_tools(config.required_tools)
    if missing:
        print(format_missing_tools(missing))
        return 1
    print("All required tools are available.")
    return 0


def install_hooks_command(repo_root: Path, config: UggoLintConfig) -> int:
    if config.hook_backend == "pre-commit":
        print(
            "Configured hook backend is not 'native'. "
            "Use 'uggo-lint print-precommit-config' for pre-commit integration."
        )
        return 0

    if config.hook_backend == "auto" and detect_precommit_config(repo_root):
        print(
            "Detected pre-commit configuration. "
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
        return run_command(
            repo_root,
            config,
            output_format=args.format,
            check_only=args.check_only,
            all_files=args.all,
        )
    if args.command == "check-file":
        return check_file_command(repo_root, Path(args.path), args.format)
    if args.command == "doctor":
        return doctor_command(config)
    if args.command == "install-hooks":
        return install_hooks_command(repo_root, config)
    if args.command == "print-precommit-config":
        print(render_precommit_config())
        return 0

    parser.print_help()
    return 0
