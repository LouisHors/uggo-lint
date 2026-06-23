from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Finding:
    rule_id: str
    message: str
    path: str
    severity: str = "error"


def detect_forbidden_init(path: str, source: str) -> list[Finding]:
    if "func init()" not in source:
        return []
    return [
        Finding(
            rule_id="no-init",
            message="Avoid init(); prefer explicit setup.",
            path=path,
            severity="error",
        )
    ]


def detect_panic_outside_tests(path: str, source: str) -> list[Finding]:
    if path.endswith("_test.go") or "panic(" not in source:
        return []
    return [
        Finding(
            rule_id="no-panic-outside-tests",
            message="Avoid panic() outside tests; return errors instead.",
            path=path,
            severity="error",
        )
    ]


def detect_fire_and_forget_go(path: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    for line in source.splitlines():
        if line.strip().startswith("go "):
            findings.append(
                Finding(
                    rule_id="no-fire-and-forget-go",
                    message="Review fire-and-forget goroutine usage carefully.",
                    path=path,
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
    return findings
