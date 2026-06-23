from uggo_lint.rules import (
    detect_context_first,
    detect_error_string_style,
    detect_forbidden_init,
    detect_receiver_name_consistency,
)


def test_detect_forbidden_init_flags_init_function():
    source = "package main\n\nfunc init() {}\n"
    findings = detect_forbidden_init("main.go", source)
    assert findings
    assert findings[0].rule_id == "no-init"


def test_detect_context_first_flags_non_leading_context_argument():
    source = (
        "package service\n\n"
        "import \"context\"\n\n"
        "func Run(name string, ctx context.Context) error {\n"
        "    return nil\n"
        "}\n"
    )

    findings = detect_context_first("service.go", source)

    assert findings
    assert findings[0].rule_id == "context-first"


def test_detect_error_string_style_flags_capitalized_or_punctuated_errors():
    source = (
        "package service\n\n"
        "import \"errors\"\n\n"
        "func Run() error {\n"
        "    return errors.New(\"Bad Request.\")\n"
        "}\n"
    )

    findings = detect_error_string_style("service.go", source)

    assert findings
    assert findings[0].rule_id == "error-string-style"


def test_detect_receiver_name_consistency_flags_mixed_receivers():
    source = (
        "package service\n\n"
        "type Worker struct{}\n\n"
        "func (w *Worker) Start() {}\n"
        "func (worker *Worker) Stop() {}\n"
    )

    findings = detect_receiver_name_consistency("service.go", source)

    assert findings
    assert findings[0].rule_id == "receiver-name-consistency"


def test_context_and_error_rules_skip_test_files():
    source = (
        "package service\n\n"
        "import (\n"
        "    \"context\"\n"
        "    \"errors\"\n"
        ")\n\n"
        "func TestRun(name string, ctx context.Context) error {\n"
        "    return errors.New(\"Bad Request.\")\n"
        "}\n"
    )

    assert detect_context_first("service_test.go", source) == []
    assert detect_error_string_style("service_test.go", source) == []
