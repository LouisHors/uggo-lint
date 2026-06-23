from pathlib import Path

from uggo_lint.cli import render_precommit_config


def test_render_precommit_config_mentions_entry():
    text = render_precommit_config()
    assert "uggo-lint run" in text
    assert "language: system" in text
    assert "repo: local" in text


def test_repository_precommit_hook_metadata_exists():
    hook_file = Path(__file__).resolve().parents[1] / ".pre-commit-hooks.yaml"

    assert hook_file.exists()
    content = hook_file.read_text(encoding="utf-8")
    assert "id: uggo-lint" in content
    assert "entry: uggo-lint run" in content
