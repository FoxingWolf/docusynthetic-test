"""Convert scraped HTML to clean Markdown."""

import logging
import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md

logger = logging.getLogger(__name__)


class HTMLConverter:
    """Convert HTML fragments to Markdown."""

    def __init__(self, html_content: str):
        self.html_content = html_content
        self.soup = BeautifulSoup(html_content, "lxml")

    def convert(self) -> str:
        """Convert HTML to Markdown."""
        # Clean up the HTML first
        self._clean_html()

        # Convert to markdown
        markdown = md(str(self.soup), heading_style="ATX", bullets="-")

        # Clean up the markdown
        markdown = self._clean_markdown(markdown)

        return markdown

    def _clean_html(self) -> None:
        """Clean up HTML before conversion."""
        # Remove script and style tags
        for tag in self.soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Remove SVG icons
        for svg in self.soup("svg"):
            svg.decompose()

        # Extract semantic content from class-based styling
        # Venice uses classes like vpt-model-name, vpt-price-value, etc.
        for elem in self.soup.find_all(class_=re.compile(r"vpt-")):
            # Keep the element but it's already there
            pass

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up converted markdown."""
        # Remove excessive newlines
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        # Remove empty links
        markdown = re.sub(r"\[\s*\]\([^)]*\)", "", markdown)

        # Clean up table formatting
        markdown = self._fix_tables(markdown)

        return markdown.strip()

    def _fix_tables(self, markdown: str) -> str:
        """Fix markdown table formatting."""
        # This is a simple implementation
        # In production, you might want more sophisticated table handling
        return markdown

    def extract_tables(self) -> list[str]:
        """Extract HTML tables as Markdown."""
        tables = []
        for table in self.soup.find_all("table"):
            table_md = md(str(table), heading_style="ATX")
            tables.append(table_md)
        return tables

    def extract_by_selector(self, selector: str) -> str:
        """Extract content by CSS selector and convert to Markdown."""
        elements = self.soup.select(selector)
        if not elements:
            return ""

        combined_html = "".join(str(elem) for elem in elements)
        return md(combined_html, heading_style="ATX", bullets="-")
