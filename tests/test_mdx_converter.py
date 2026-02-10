"""Test MDX converter."""

from pathlib import Path

import pytest

from venice_kb.processing.mdx_converter import MDXConverter


@pytest.fixture
def sample_mdx():
    """Load sample MDX fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample.mdx"
    return fixture_path.read_text()


def test_extract_frontmatter(sample_mdx):
    """Test frontmatter extraction."""
    converter = MDXConverter(sample_mdx)
    assert converter.frontmatter["title"] == "Getting Started with Venice AI"
    assert "description" in converter.frontmatter


def test_convert_note(sample_mdx):
    """Test Note component conversion."""
    converter = MDXConverter(sample_mdx)
    result = converter.convert()
    assert "> **Note:**" in result


def test_convert_warning(sample_mdx):
    """Test Warning component conversion."""
    converter = MDXConverter(sample_mdx)
    result = converter.convert()
    assert "> ⚠️ **Warning:**" in result


def test_convert_steps(sample_mdx):
    """Test Steps component conversion."""
    converter = MDXConverter(sample_mdx)
    result = converter.convert()
    assert "### Step 1:" in result
    assert "### Step 2:" in result


def test_convert_code_group(sample_mdx):
    """Test CodeGroup component conversion."""
    converter = MDXConverter(sample_mdx)
    result = converter.convert()
    # CodeGroup wrapper should be removed but code blocks remain
    assert "```python" in result
    assert "```javascript" in result


def test_convert_cards(sample_mdx):
    """Test Card component conversion."""
    converter = MDXConverter(sample_mdx)
    result = converter.convert()
    assert "[API Reference]" in result
    assert "[Models]" in result


def test_title_from_frontmatter(sample_mdx):
    """Test title is extracted from frontmatter."""
    converter = MDXConverter(sample_mdx)
    result = converter.convert()
    assert result.startswith("# Getting Started with Venice AI")


def test_empty_mdx():
    """Test handling of empty MDX."""
    converter = MDXConverter("")
    result = converter.convert()
    assert result == ""


def test_mdx_without_frontmatter():
    """Test MDX without frontmatter."""
    mdx = "# Test\n\nSome content"
    converter = MDXConverter(mdx)
    result = converter.convert()
    assert "# Test" in result
