from pathlib import Path


def test_example_config_exists():
    assert Path("examples/uggo-lint-config.example.yaml").exists()
