"""Tests for changelog writer."""

from datetime import datetime
from pathlib import Path
from venice_kb.diffing.models import DiffReport, ChangeEntry, ChangeType, SeverityLevel
from venice_kb.diffing.changelog_writer import render_changelog_markdown


def test_render_changelog_markdown():
    """Test changelog markdown rendering."""
    report = DiffReport(
        generated_at=datetime(2024, 1, 2),
        previous_snapshot="2024-01-01",
        current_snapshot="2024-01-02",
        summary="Test changes",
        stats={"added": 1, "modified": 1, "removed": 0, "unchanged": 5},
        breaking_changes=[],
        important_changes=[
            ChangeEntry(
                change_type=ChangeType.ADDED,
                severity=SeverityLevel.IMPORTANT,
                path="api-reference/new-endpoint.md",
                section="API Reference > New Endpoint",
                title="New endpoint added",
                details="Added POST /new endpoint",
            )
        ],
        informational_changes=[],
        cosmetic_changes=[],
    )
    
    markdown = render_changelog_markdown([report])
    
    assert "# Venice API Docs Knowledge Base — Changelog" in markdown
    assert "2024-01-02" in markdown
    assert "Important Changes" in markdown
    assert "NEW" in markdown
    assert "api-reference/new-endpoint.md" in markdown
