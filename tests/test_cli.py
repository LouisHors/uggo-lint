from uggo_lint import main


def test_main_without_args_prints_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "uggo-lint" in captured.out
    assert "install-hooks" in captured.out
    assert "run" in captured.out
