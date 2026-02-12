"""Scraped HTML to clean Markdown converter."""

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def convert_html_to_markdown(html_content: str) -> str:
    """Convert HTML to clean Markdown.

    Args:
        html_content: Raw HTML content

    Returns:
        Clean Markdown
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Extract main content (adjust selector based on actual site structure)
    main_content = soup.find("main") or soup.find("article") or soup

    # Convert to markdown
    markdown = md(str(main_content), heading_style="ATX")

    return markdown.strip()
