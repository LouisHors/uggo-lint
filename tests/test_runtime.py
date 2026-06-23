from uggo_lint.runtime import format_missing_tools


def test_format_missing_tools_includes_tool_names():
    message = format_missing_tools(["golangci-lint", "goimports"])
    assert "golangci-lint" in message
    assert "goimports" in message
