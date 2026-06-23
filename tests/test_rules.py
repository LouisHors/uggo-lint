from uggo_lint.rules import detect_forbidden_init


def test_detect_forbidden_init_flags_init_function():
    source = "package main\n\nfunc init() {}\n"
    findings = detect_forbidden_init("main.go", source)
    assert findings
    assert findings[0].rule_id == "no-init"
