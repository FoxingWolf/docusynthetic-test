"""Test changelog writer."""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from venice_kb.diffing.changelog_writer import ChangelogWriter
from venice_kb.diffing.models import ChangeEntry, ChangeType, DiffReport, SeverityLevel


@pytest.fixture
def sample_report():
    """Create sample diff report."""
    changes = [
        ChangeEntry(
            change_type=ChangeType.ADDED,
            severity=SeverityLevel.INFORMATIONAL,
            path="new-page.md",
            title="New Page",
            description="Added new page",
        ),
        ChangeEntry(
            change_type=ChangeType.MODIFIED,
            severity=SeverityLevel.BREAKING,
            path="api/endpoint.md",
            title="API Endpoint",
            description="Breaking change to endpoint",
            diff_preview="Old -> New",
        ),
    ]

    return DiffReport(
        old_snapshot_time=datetime(2024, 1, 1),
        new_snapshot_time=datetime(2024, 1, 2),
        changes=changes,
        stats={"added": 1, "modified": 1, "removed": 0, "total_changes": 2},
    )


def test_write_changelog(sample_report):
    """Test changelog writing."""
    with TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        writer = ChangelogWriter(changelog_path)
        writer.write_changelog([sample_report])

        assert changelog_path.exists()
        content = changelog_path.read_text()

        assert "Venice AI Documentation Changelog" in content
        assert "Build 2024-01-02" in content


def test_changelog_sections(sample_report):
    """Test changelog sections."""
    with TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        writer = ChangelogWriter(changelog_path)
        writer.write_changelog([sample_report])

        content = changelog_path.read_text()

        assert "🚨 Breaking Changes" in content
        assert "ℹ️ Informational Changes" in content


def test_json_changelog(sample_report):
    """Test JSON changelog writing."""
    with TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        writer = ChangelogWriter(changelog_path)
        writer.write_changelog([sample_report])

        json_path = Path(tmpdir) / "CHANGELOG.json"
        assert json_path.exists()

        import json

        data = json.loads(json_path.read_text())
        assert len(data) == 1
        assert len(data[0]["changes"]) == 2


def test_multiple_reports():
    """Test writing multiple reports."""
    reports = [
        DiffReport(
            old_snapshot_time=datetime(2024, 1, i),
            new_snapshot_time=datetime(2024, 1, i + 1),
            changes=[],
            stats={
                "total_changes": 0,
                "added": 0,
                "modified": 0,
                "removed": 0,
                "breaking": 0,
                "important": 0,
            },
        )
        for i in range(1, 4)
    ]

    with TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        writer = ChangelogWriter(changelog_path)
        writer.write_changelog(reports)

        content = changelog_path.read_text()
        assert content.count("## Build") == 3
