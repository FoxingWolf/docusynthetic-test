"""Tests for MDX converter."""

from venice_kb.processing.mdx_converter import convert_mdx_to_markdown


def test_frontmatter_extraction(sample_mdx):
    """Test that frontmatter is extracted and title becomes H1."""
    result = convert_mdx_to_markdown(sample_mdx)
    assert "# Chat Completions" in result
    assert "<!--" in result  # Frontmatter should be in comment


def test_note_conversion(sample_mdx):
    """Test Note component conversion."""
    result = convert_mdx_to_markdown(sample_mdx)
    assert "> **Note:**" in result


def test_codegroup_removal(sample_mdx):
    """Test CodeGroup wrapper is removed."""
    result = convert_mdx_to_markdown(sample_mdx)
    assert "<CodeGroup>" not in result
    assert "```python" in result
    assert "```javascript" in result
