from __future__ import annotations

import subprocess
from pathlib import Path


def filter_go_files(files: list[str]) -> list[str]:
    return [path for path in files if path.endswith(".go")]


def get_staged_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def build_pre_commit_hook_script(repo_root: Path) -> str:
    return f"""#!/bin/sh
set -eu

cd "{repo_root}"
# uggo-lint run
uggo-lint run
"""
