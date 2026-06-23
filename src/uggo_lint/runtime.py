from __future__ import annotations

import subprocess
import shutil


def find_missing_tools(names: list[str]) -> list[str]:
    return [name for name in names if shutil.which(name) is None]


def format_missing_tools(names: list[str]) -> str:
    if not names:
        return "All required tools are available."
    return f"Missing required tools: {', '.join(names)}"


def format_process_failure(
    step_name: str, error: subprocess.CalledProcessError
) -> str:
    command = " ".join(str(part) for part in error.cmd)
    lines = [
        f"uggo-lint step failed: {step_name}",
        f"Command: {command}",
        f"Exit code: {error.returncode}",
    ]
    if error.stderr:
        lines.append(f"stderr: {error.stderr.strip()}")
    if error.stdout:
        lines.append(f"stdout: {error.stdout.strip()}")
    return "\n".join(lines)
