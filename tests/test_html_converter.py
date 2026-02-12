"""Tests for HTML converter."""

from venice_kb.processing.html_converter import convert_html_to_markdown


def test_html_to_markdown(sample_html):
    """Test HTML to Markdown conversion."""
    result = convert_html_to_markdown(sample_html)
    
    assert "# Models Overview" in result
    assert "Venice AI supports" in result
    assert "Text models" in result
    assert "<script>" not in result  # Scripts should be removed
