"""MDX/Mintlify to clean Markdown converter."""

import re
from bs4 import BeautifulSoup
from venice_kb.utils.logging import logger


def convert_mdx_to_markdown(mdx_content: str) -> str:
    """Convert MDX/Mintlify components to clean Markdown.
    
    Args:
        mdx_content: Raw MDX content
        
    Returns:
        Clean Markdown
    """
    # Extract frontmatter and convert to comment
    markdown = _extract_frontmatter(mdx_content)
    
    # Convert Mintlify components
    markdown = _convert_codegroup(markdown)
    markdown = _convert_steps(markdown)
    markdown = _convert_notes_warnings(markdown)
    markdown = _convert_cards(markdown)
    markdown = _convert_tabs(markdown)
    markdown = _convert_accordion(markdown)
    markdown = _strip_simple_tags(markdown)
    
    return markdown


def _extract_frontmatter(content: str) -> str:
    """Extract YAML frontmatter and convert to HTML comment.
    
    Args:
        content: MDX content with frontmatter
        
    Returns:
        Content with frontmatter as comment
    """
    pattern = r'^---\n(.*?)\n---\n'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        frontmatter = match.group(1)
        # Extract title if present
        title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
        title = title_match.group(1) if title_match else ""
        
        # Convert to comment and prepend title as H1
        rest = content[match.end():]
        result = ""
        if title:
            result = f"# {title}\n\n"
        result += f"<!-- Metadata:\n{frontmatter}\n-->\n\n{rest}"
        return result
    
    return content


def _convert_codegroup(content: str) -> str:
    """Strip <CodeGroup> wrapper, keep code blocks."""
    content = re.sub(r'<CodeGroup[^>]*>', '', content)
    content = re.sub(r'</CodeGroup>', '', content)
    return content


def _convert_steps(content: str) -> str:
    """Convert <Steps><Step> to numbered headings."""
    # Simple regex-based conversion
    step_num = 1
    
    def replace_step(match):
        nonlocal step_num
        title = match.group(1)
        result = f"### Step {step_num}: {title}\n"
        step_num += 1
        return result
    
    content = re.sub(r'<Step[^>]*title=["\'](.*?)["\'][^>]*>', replace_step, content)
    content = re.sub(r'</Step>', '', content)
    content = re.sub(r'<Steps[^>]*>', '', content)
    content = re.sub(r'</Steps>', '', content)
    
    return content


def _convert_notes_warnings(content: str) -> str:
    """Convert <Note> and <Warning> to blockquotes."""
    # Note
    content = re.sub(
        r'<Note>(.*?)</Note>',
        r'> **Note:** \1',
        content,
        flags=re.DOTALL
    )
    
    # Warning
    content = re.sub(
        r'<Warning>(.*?)</Warning>',
        r'> ⚠️ **Warning:** \1',
        content,
        flags=re.DOTALL
    )
    
    return content


def _convert_cards(content: str) -> str:
    """Convert <Card> to markdown links."""
    pattern = r'<Card[^>]*title=["\'](.*?)["\'][^>]*href=["\'](.*?)["\'][^>]*>(.*?)</Card>'
    content = re.sub(
        pattern,
        r'- **[\1](\2)** — \3',
        content,
        flags=re.DOTALL
    )
    
    # Strip CardGroup wrapper
    content = re.sub(r'<CardGroup[^>]*>', '', content)
    content = re.sub(r'</CardGroup>', '', content)
    
    return content


def _convert_tabs(content: str) -> str:
    """Convert <Tabs><Tab> to subsections."""
    pattern = r'<Tab[^>]*title=["\'](.*?)["\'][^>]*>'
    content = re.sub(pattern, r'#### \1\n', content)
    content = re.sub(r'</Tab>', '\n', content)
    content = re.sub(r'<Tabs[^>]*>', '', content)
    content = re.sub(r'</Tabs>', '', content)
    
    return content


def _convert_accordion(content: str) -> str:
    """Convert <Accordion> to details/summary."""
    pattern = r'<Accordion[^>]*title=["\'](.*?)["\'][^>]*>(.*?)</Accordion>'
    content = re.sub(
        pattern,
        r'<details><summary>\1</summary>\n\2\n</details>',
        content,
        flags=re.DOTALL
    )
    
    return content


def _strip_simple_tags(content: str) -> str:
    """Strip simple wrapper tags, keep inner text."""
    tags_to_strip = ['Tooltip', 'Frame', 'Info', 'Check']
    
    for tag in tags_to_strip:
        content = re.sub(f'<{tag}[^>]*>', '', content)
        content = re.sub(f'</{tag}>', '', content)
    
    # Handle placeholder divs
    content = re.sub(
        r'<div[^>]*id=["\'][^"\']*-placeholder["\'][^>]*>.*?</div>',
        '[Dynamic content — see live docs]',
        content,
        flags=re.DOTALL
    )
    
    return content
