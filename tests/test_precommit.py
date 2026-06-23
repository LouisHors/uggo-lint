from uggo_lint.cli import render_precommit_config


def test_render_precommit_config_mentions_entry():
    text = render_precommit_config()
    assert "uggo-lint run" in text
    assert "language: system" in text
