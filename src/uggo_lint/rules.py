from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(slots=True)
class Finding:
    rule_id: str
    message: str
    path: str
    line: int = 1
    column: int = 1
    severity: str = "error"


def _line_column(source: str, offset: int) -> tuple[int, int]:
    line = source.count("\n", 0, offset) + 1
    line_start = source.rfind("\n", 0, offset) + 1
    column = offset - line_start + 1
    return line, column


def _finding(
    *,
    rule_id: str,
    message: str,
    path: str,
    source: str,
    offset: int,
    severity: str = "error",
) -> Finding:
    line, column = _line_column(source, offset)
    return Finding(
        rule_id=rule_id,
        message=message,
        path=path,
        line=line,
        column=column,
        severity=severity,
    )


def detect_forbidden_init(path: str, source: str) -> list[Finding]:
    match = re.search(r"func\s+init\s*\(\s*\)", source)
    if not match:
        return []
    return [
        _finding(
            rule_id="no-init",
            message="Avoid init(); prefer explicit setup.",
            path=path,
            source=source,
            offset=match.start(),
            severity="error",
        )
    ]


def detect_panic_outside_tests(path: str, source: str) -> list[Finding]:
    match = re.search(r"\bpanic\s*\(", source)
    if path.endswith("_test.go") or not match:
        return []
    return [
        _finding(
            rule_id="no-panic-outside-tests",
            message="Avoid panic() outside tests; return errors instead.",
            path=path,
            source=source,
            offset=match.start(),
            severity="error",
        )
    ]


def detect_fire_and_forget_go(path: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    offset = 0
    for line in source.splitlines(keepends=True):
        if line.strip().startswith("go "):
            findings.append(
                _finding(
                    rule_id="no-fire-and-forget-go",
                    message="Review fire-and-forget goroutine usage carefully.",
                    path=path,
                    source=source,
                    offset=offset + line.index("go"),
                    severity="warning",
                )
            )
            break
        offset += len(line)
    return findings


def detect_context_first(path: str, source: str) -> list[Finding]:
    if path.endswith("_test.go") or "context.Context" not in source:
        return []

    findings: list[Finding] = []
    for match in re.finditer(r"func\s+\w+\((?P<params>[^)]*)\)", source):
        params = match.group("params")
        if "context.Context" not in params:
            continue
        parts = [part.strip() for part in params.split(",") if part.strip()]
        for index, part in enumerate(parts):
            if "context.Context" in part and index != 0:
                findings.append(
                    _finding(
                        rule_id="context-first",
                        message="Place context.Context as the first function parameter.",
                        path=path,
                        source=source,
                        offset=match.start("params") + params.index("context.Context"),
                        severity="warning",
                    )
                )
                return findings
    return findings


def detect_error_string_style(path: str, source: str) -> list[Finding]:
    if path.endswith("_test.go"):
        return []

    findings: list[Finding] = []
    for match in re.finditer(r'errors\.New\("([^"]+)"\)', source):
        message = match.group(1)
        if not message:
            continue
        if message[0].isupper() or message.endswith((".", "!", ":")):
            findings.append(
                _finding(
                    rule_id="error-string-style",
                    message="Error strings should start lowercase and avoid trailing punctuation.",
                    path=path,
                    source=source,
                    offset=match.start(1),
                    severity="warning",
                )
            )
            break
    return findings


def detect_receiver_name_consistency(path: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    receiver_names: dict[str, str] = {}
    for match in re.finditer(
        r"func\s+\(\s*(?P<name>\w+)\s+\*?(?P<type>\w+)\s*\)\s+\w+\(",
        source,
    ):
        receiver_name = match.group("name")
        receiver_type = match.group("type")
        existing = receiver_names.get(receiver_type)
        if existing is None:
            receiver_names[receiver_type] = receiver_name
            continue
        if existing != receiver_name:
            findings.append(
                _finding(
                    rule_id="receiver-name-consistency",
                    message="Keep receiver names consistent for the same type.",
                    path=path,
                    source=source,
                    offset=match.start("name"),
                    severity="warning",
                )
            )
            break
    return findings


def run_custom_rules(path: Path) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    path_text = str(path)
    findings: list[Finding] = []
    findings.extend(detect_forbidden_init(path_text, source))
    findings.extend(detect_panic_outside_tests(path_text, source))
    findings.extend(detect_fire_and_forget_go(path_text, source))
    findings.extend(detect_context_first(path_text, source))
    findings.extend(detect_error_string_style(path_text, source))
    findings.extend(detect_receiver_name_consistency(path_text, source))
    return findings
