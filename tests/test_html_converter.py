"""Test HTML converter."""

from pathlib import Path

import pytest

from venice_kb.processing.html_converter import HTMLConverter


@pytest.fixture
def sample_html():
    """Load sample HTML fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_html.html"
    return fixture_path.read_text()


def test_convert_html(sample_html):
    """Test basic HTML to Markdown conversion."""
    converter = HTMLConverter(sample_html)
    result = converter.convert()

    assert result is not None
    assert len(result) > 0


def test_extract_tables(sample_html):
    """Test table extraction."""
    converter = HTMLConverter(sample_html)
    tables = converter.extract_tables()

    assert len(tables) > 0
    assert "Model" in tables[0]
    assert "GPT-4" in tables[0]


def test_clean_html(sample_html):
    """Test HTML cleaning."""
    converter = HTMLConverter(sample_html)
    converter._clean_html()

    # Check that content is preserved
    assert converter.soup is not None


def test_extract_by_selector(sample_html):
    """Test extraction by CSS selector."""
    converter = HTMLConverter(sample_html)
    result = converter.extract_by_selector("table")

    assert "Model" in result


def test_empty_html():
    """Test handling of empty HTML."""
    converter = HTMLConverter("")
    result = converter.convert()
    assert result == ""
