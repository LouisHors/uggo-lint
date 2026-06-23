from __future__ import annotations

import shutil


def find_missing_tools(names: list[str]) -> list[str]:
    return [name for name in names if shutil.which(name) is None]


def format_missing_tools(names: list[str]) -> str:
    if not names:
        return "All required tools are available."
    return f"Missing required tools: {', '.join(names)}"
