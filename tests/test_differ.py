"""Tests for differ."""

from datetime import datetime

from venice_kb.diffing.differ import diff_snapshots
from venice_kb.diffing.models import KBSnapshot, PageMetadata


def test_diff_added_pages():
    """Test detecting added pages."""
    old_snapshot = KBSnapshot(
        snapshot_id="2024-01-01",
        generated_at=datetime(2024, 1, 1),
        source_versions={},
        page_manifest={
            "page1.md": PageMetadata(hash="hash1", token_count=100, title="Page 1", tags=[])
        },
    )

    new_snapshot = KBSnapshot(
        snapshot_id="2024-01-02",
        generated_at=datetime(2024, 1, 2),
        source_versions={},
        page_manifest={
            "page1.md": PageMetadata(hash="hash1", token_count=100, title="Page 1", tags=[]),
            "page2.md": PageMetadata(hash="hash2", token_count=200, title="Page 2", tags=[]),
        },
    )

    report = diff_snapshots(old_snapshot, new_snapshot)

    assert report.stats["added"] == 1
    assert report.stats["unchanged"] == 1
    assert len(report.get_all_changes()) >= 1


def test_diff_removed_pages():
    """Test detecting removed pages."""
    old_snapshot = KBSnapshot(
        snapshot_id="2024-01-01",
        generated_at=datetime(2024, 1, 1),
        source_versions={},
        page_manifest={
            "page1.md": PageMetadata(hash="hash1", token_count=100, title="Page 1", tags=[]),
            "page2.md": PageMetadata(hash="hash2", token_count=200, title="Page 2", tags=[]),
        },
    )

    new_snapshot = KBSnapshot(
        snapshot_id="2024-01-02",
        generated_at=datetime(2024, 1, 2),
        source_versions={},
        page_manifest={
            "page1.md": PageMetadata(hash="hash1", token_count=100, title="Page 1", tags=[])
        },
    )

    report = diff_snapshots(old_snapshot, new_snapshot)

    assert report.stats["removed"] == 1
    assert report.stats["unchanged"] == 1


def test_diff_modified_pages():
    """Test detecting modified pages."""
    old_snapshot = KBSnapshot(
        snapshot_id="2024-01-01",
        generated_at=datetime(2024, 1, 1),
        source_versions={},
        page_manifest={
            "page1.md": PageMetadata(hash="hash1", token_count=100, title="Page 1", tags=[])
        },
    )

    new_snapshot = KBSnapshot(
        snapshot_id="2024-01-02",
        generated_at=datetime(2024, 1, 2),
        source_versions={},
        page_manifest={
            "page1.md": PageMetadata(hash="hash2", token_count=150, title="Page 1 Updated", tags=[])
        },
    )

    report = diff_snapshots(old_snapshot, new_snapshot)

    assert report.stats["modified"] == 1
    assert report.stats["unchanged"] == 0
