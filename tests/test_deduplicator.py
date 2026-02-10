"""Test deduplicator."""

import pytest

from venice_kb.processing.deduplicator import Deduplicator


def test_exact_duplicates():
    """Test exact duplicate detection."""
    pages = {
        "page1.md": "# Test\n\nSome content",
        "page2.md": "# Test\n\nSome content",  # Exact duplicate
        "page3.md": "# Different\n\nOther content",
    }

    dedup = Deduplicator(pages)
    unique = dedup.deduplicate_exact()

    # Should keep only 2 unique pages
    assert len(unique) == 2
    assert "page3.md" in unique


def test_no_duplicates():
    """Test case with no duplicates."""
    pages = {
        "page1.md": "# First\n\nContent 1",
        "page2.md": "# Second\n\nContent 2",
        "page3.md": "# Third\n\nContent 3",
    }

    dedup = Deduplicator(pages)
    unique = dedup.deduplicate_exact()

    assert len(unique) == 3


def test_similar_detection():
    """Test similar page detection."""
    pages = {
        "page1.md": "# Test\n\nThis is a long document with many words that are the same",
        "page2.md": "# Test\n\nThis is a long document with many words that are the same and a bit more",
        "page3.md": "# Completely different content about something else entirely",
    }

    dedup = Deduplicator(pages)
    unique = dedup.deduplicate_similar(threshold=0.7)

    # Should detect page1 and page2 as similar
    assert len(unique) < 3


def test_empty_pages():
    """Test handling of empty pages."""
    pages = {}
    dedup = Deduplicator(pages)
    unique = dedup.deduplicate_exact()

    assert len(unique) == 0
