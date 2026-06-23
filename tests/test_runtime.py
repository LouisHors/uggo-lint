import subprocess

from uggo_lint.runtime import format_missing_tools, format_process_failure


def test_format_missing_tools_includes_tool_names():
    message = format_missing_tools(["golangci-lint", "goimports"])
    assert "golangci-lint" in message
    assert "goimports" in message


def test_format_process_failure_includes_step_command_exit_code_and_stderr():
    error = subprocess.CalledProcessError(
        3,
        ["golangci-lint", "run", "--new", "./cmd/api/..."],
        stderr="lint exploded",
    )

    message = format_process_failure("lint", error)

    assert "uggo-lint step failed: lint" in message
    assert "Exit code: 3" in message
    assert "lint exploded" in message
