"""Test differ."""

from datetime import datetime

import pytest

from venice_kb.diffing.differ import Differ
from venice_kb.diffing.models import ChangeType, KBSnapshot, PageInfo, SeverityLevel


@pytest.fixture
def old_snapshot():
    """Create old snapshot."""
    return KBSnapshot(
        timestamp=datetime(2024, 1, 1),
        pages={
            "page1.md": PageInfo(
                path="page1.md",
                content_hash="abc123",
                token_count=100,
                title="Page 1",
                tags=["test"],
            ),
            "page2.md": PageInfo(
                path="page2.md",
                content_hash="def456",
                token_count=200,
                title="Page 2",
                tags=[],
            ),
        },
    )


@pytest.fixture
def new_snapshot():
    """Create new snapshot."""
    return KBSnapshot(
        timestamp=datetime(2024, 1, 2),
        pages={
            "page1.md": PageInfo(
                path="page1.md",
                content_hash="xyz789",  # Modified
                token_count=110,
                title="Page 1",
                tags=["test"],
            ),
            "page3.md": PageInfo(
                path="page3.md",
                content_hash="new123",
                token_count=150,
                title="Page 3",
                tags=[],
            ),
        },
    )


def test_detect_added(old_snapshot, new_snapshot):
    """Test detection of added pages."""
    differ = Differ()
    report = differ.diff_snapshots(old_snapshot, new_snapshot)

    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].path == "page3.md"


def test_detect_removed(old_snapshot, new_snapshot):
    """Test detection of removed pages."""
    differ = Differ()
    report = differ.diff_snapshots(old_snapshot, new_snapshot)

    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].path == "page2.md"


def test_detect_modified(old_snapshot, new_snapshot):
    """Test detection of modified pages."""
    differ = Differ()
    report = differ.diff_snapshots(old_snapshot, new_snapshot)

    modified = [c for c in report.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].path == "page1.md"


def test_stats_calculation(old_snapshot, new_snapshot):
    """Test statistics calculation."""
    differ = Differ()
    report = differ.diff_snapshots(old_snapshot, new_snapshot)

    assert report.stats["added"] == 1
    assert report.stats["removed"] == 1
    assert report.stats["modified"] == 1
    assert report.stats["total_changes"] == 3


def test_severity_classification():
    """Test severity classification."""
    differ = Differ()

    # Breaking change for API endpoint removal
    severity = differ._classify_removal_severity("api-reference/endpoints/chat.md")
    assert severity == SeverityLevel.BREAKING

    # Informational for guide removal
    severity = differ._classify_removal_severity("guides/getting-started.md")
    assert severity == SeverityLevel.INFORMATIONAL


def test_empty_diff():
    """Test diff with no changes."""
    snapshot = KBSnapshot(
        timestamp=datetime(2024, 1, 1),
        pages={
            "page1.md": PageInfo(
                path="page1.md",
                content_hash="abc123",
                token_count=100,
                title="Page 1",
                tags=[],
            )
        },
    )

    differ = Differ()
    report = differ.diff_snapshots(snapshot, snapshot)

    assert len(report.changes) == 0
    assert report.stats["total_changes"] == 0
