"""Tests for deduplicator."""

from venice_kb.processing.deduplicator import deduplicate_content


def test_deduplication():
    """Test basic deduplication."""
    contents = {
        "source1": "Same content",
        "source2": "Same content",
        "source3": "Different content",
    }

    result = deduplicate_content(contents, use_llm=False)

    assert len(result) == 2  # Should dedupe to 2 unique items
    assert "Different content" in result.values()
