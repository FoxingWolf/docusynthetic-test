"""Tests for configuration."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from docusynthetic.utils import Config


def test_default_config() -> None:
    """Test default configuration."""
    config = Config()

    assert config.github_repo_owner == "veniceai"
    assert config.github_repo_name == "api-docs"
    assert config.github_branch == "main"
    assert config.fetch_github is True
    assert config.fetch_openapi is True
    assert config.fetch_live_site is True


def test_config_save_and_load() -> None:
    """Test saving and loading configuration."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        # Create and save config
        config = Config(
            github_repo_owner="testorg",
            github_repo_name="test-repo",
            fetch_live_site=False,
        )
        config.save(config_path)

        # Load config
        loaded_config = Config.load(config_path)

        assert loaded_config.github_repo_owner == "testorg"
        assert loaded_config.github_repo_name == "test-repo"
        assert loaded_config.fetch_live_site is False


def test_config_load_nonexistent() -> None:
    """Test loading non-existent config returns defaults."""
    config = Config.load(Path("/nonexistent/config.json"))
    assert config.github_repo_owner == "veniceai"
