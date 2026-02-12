"""Tests for CLI commands."""

from typer.testing import CliRunner

from venice_kb.cli import app

runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Venice KB Collector" in result.stdout


def test_status_no_snapshots(tmp_path):
    """Test status command with no snapshots."""
    result = runner.invoke(app, ["status", "--snapshot-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No snapshots found" in result.stdout


def test_changelog_insufficient_snapshots(tmp_path):
    """Test changelog with insufficient snapshots."""
    result = runner.invoke(app, ["changelog", "--snapshot-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Need at least 2 snapshots" in result.stdout
