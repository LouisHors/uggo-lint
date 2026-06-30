from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uggo_lint.rules import Finding


def relative_path(path: str, repo_root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def finding_to_dict(finding: Finding, repo_root: Path) -> dict[str, Any]:
    return {
        "rule_id": finding.rule_id,
        "message": finding.message,
        "path": relative_path(finding.path, repo_root),
        "line": finding.line,
        "column": finding.column,
        "severity": finding.severity,
        "source": "uggo-lint",
    }


def render_json_result(
    ok: bool,
    findings: list[Finding],
    repo_root: Path,
    *,
    steps: list[dict[str, Any]] | None = None,
    summary: str = "",
) -> str:
    result = {
        "ok": ok,
        "findings": [finding_to_dict(finding, repo_root) for finding in findings],
        "steps": steps or [],
        "summary": summary or _default_summary(ok, findings),
    }
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


def render_error_result(message: str, repo_root: Path) -> str:
    return render_json_result(False, [], repo_root, summary=message)


def _default_summary(ok: bool, findings: list[Finding]) -> str:
    if findings:
        count = len(findings)
        return f"{count} finding" if count == 1 else f"{count} findings"
    return "uggo-lint checks passed." if ok else "uggo-lint checks failed."
