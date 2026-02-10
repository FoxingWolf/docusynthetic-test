"""Test CLI commands."""

import pytest
from typer.testing import CliRunner

from venice_kb.cli import app

runner = CliRunner()


def test_cli_help():
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Venice AI API documentation" in result.stdout


def test_status_command():
    """Test status command."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0


def test_build_command_help():
    """Test build command help."""
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "--verbose" in result.stdout


def test_changelog_command():
    """Test changelog command with no snapshots."""
    result = runner.invoke(app, ["changelog"])
    # Should handle gracefully with no snapshots
    assert result.exit_code in [0, 1]
