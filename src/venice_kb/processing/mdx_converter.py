"""Convert Mintlify MDX to clean standard Markdown."""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup
import yaml

logger = logging.getLogger(__name__)


class MDXConverter:
    """Convert Mintlify MDX components to standard Markdown."""

    def __init__(self, mdx_content: str):
        self.mdx_content = mdx_content
        self.frontmatter: dict[str, Any] = {}
        self.body = ""
        self._extract_frontmatter()

    def _extract_frontmatter(self) -> None:
        """Extract YAML frontmatter from MDX."""
        # Match frontmatter between --- delimiters
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", self.mdx_content, re.DOTALL)
        if match:
            frontmatter_text = match.group(1)
            self.body = match.group(2)
            try:
                self.frontmatter = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
                self.frontmatter = {}
        else:
            self.body = self.mdx_content

    def convert(self) -> str:
        """Convert MDX to Markdown."""
        content = self.body

        # Add title from frontmatter
        result_lines = []
        if "title" in self.frontmatter:
            result_lines.append(f"# {self.frontmatter['title']}\n")
        if "description" in self.frontmatter:
            result_lines.append(f"*{self.frontmatter['description']}*\n")

        # Convert components
        content = self._convert_code_groups(content)
        content = self._convert_steps(content)
        content = self._convert_notes_warnings(content)
        content = self._convert_cards(content)
        content = self._convert_tabs(content)
        content = self._convert_accordion(content)
        content = self._convert_placeholders(content)
        content = self._strip_simple_tags(content)

        result_lines.append(content)
        return "\n".join(result_lines)

    def _convert_code_groups(self, content: str) -> str:
        """Convert <CodeGroup> to plain code blocks."""
        # Remove <CodeGroup> wrapper but keep inner code blocks
        content = re.sub(r"<CodeGroup>\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*</CodeGroup>", "", content, flags=re.IGNORECASE)
        return content

    def _convert_steps(self, content: str) -> str:
        """Convert <Steps><Step> to numbered markdown headings."""
        # Find all <Steps> blocks
        steps_pattern = r"<Steps>(.*?)</Steps>"
        step_pattern = r'<Step\s+title="([^"]*)"[^>]*>(.*?)</Step>'

        def replace_steps(match: re.Match[str]) -> str:
            steps_content = match.group(1)
            step_matches = list(re.finditer(step_pattern, steps_content, re.DOTALL))
            if not step_matches:
                return steps_content

            result = []
            for i, step_match in enumerate(step_matches, 1):
                title = step_match.group(1)
                step_content = step_match.group(2).strip()
                result.append(f"### Step {i}: {title}\n\n{step_content}\n")

            return "\n".join(result)

        content = re.sub(steps_pattern, replace_steps, content, flags=re.DOTALL | re.IGNORECASE)
        return content

    def _convert_notes_warnings(self, content: str) -> str:
        """Convert <Note> and <Warning> to blockquotes."""
        # <Note>
        content = re.sub(
            r"<Note>(.*?)</Note>",
            r"> **Note:** \1",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # <Warning>
        content = re.sub(
            r"<Warning>(.*?)</Warning>",
            r"> ⚠️ **Warning:** \1",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # <Info>
        content = re.sub(
            r"<Info>(.*?)</Info>",
            r"> ℹ️ **Info:** \1",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # <Tip>
        content = re.sub(
            r"<Tip>(.*?)</Tip>", r"> 💡 **Tip:** \1", content, flags=re.DOTALL | re.IGNORECASE
        )

        return content

    def _convert_cards(self, content: str) -> str:
        """Convert <Card> and <CardGroup> to markdown lists."""
        # Remove <CardGroup> wrapper
        content = re.sub(r"<CardGroup[^>]*>\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*</CardGroup>", "", content, flags=re.IGNORECASE)

        # Convert <Card title="X" href="Y">Description</Card>
        def replace_card(match: re.Match[str]) -> str:
            attrs = match.group(1)
            card_content = match.group(2) if len(match.groups()) > 1 else ""

            # Extract title and href
            title_match = re.search(r'title="([^"]*)"', attrs)
            href_match = re.search(r'href="([^"]*)"', attrs)

            title = title_match.group(1) if title_match else "Link"
            href = href_match.group(1) if href_match else "#"

            description = card_content.strip() if card_content else ""

            if description:
                return f"- **[{title}]({href})** — {description}"
            else:
                return f"- **[{title}]({href})**"

        content = re.sub(
            r"<Card\s+([^>]*)>(.*?)</Card>",
            replace_card,
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Self-closing cards
        content = re.sub(
            r"<Card\s+([^/>]*)/?>",
            replace_card,
            content,
            flags=re.IGNORECASE,
        )

        return content

    def _convert_tabs(self, content: str) -> str:
        """Convert <Tabs><Tab> to markdown subsections."""
        tabs_pattern = r"<Tabs>(.*?)</Tabs>"
        tab_pattern = r'<Tab\s+title="([^"]*)"[^>]*>(.*?)</Tab>'

        def replace_tabs(match: re.Match[str]) -> str:
            tabs_content = match.group(1)
            tab_matches = list(re.finditer(tab_pattern, tabs_content, re.DOTALL))
            if not tab_matches:
                return tabs_content

            result = []
            for tab_match in tab_matches:
                title = tab_match.group(1)
                tab_content = tab_match.group(2).strip()
                result.append(f"#### {title}\n\n{tab_content}\n")

            return "\n".join(result)

        content = re.sub(tabs_pattern, replace_tabs, content, flags=re.DOTALL | re.IGNORECASE)
        return content

    def _convert_accordion(self, content: str) -> str:
        """Convert <Accordion> to HTML details/summary."""
        def replace_accordion(match: re.Match[str]) -> str:
            attrs = match.group(1)
            accordion_content = match.group(2)

            # Extract title
            title_match = re.search(r'title="([^"]*)"', attrs)
            title = title_match.group(1) if title_match else "Details"

            return f"<details>\n<summary>{title}</summary>\n\n{accordion_content}\n</details>"

        content = re.sub(
            r"<Accordion\s+([^>]*)>(.*?)</Accordion>",
            replace_accordion,
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        return content

    def _convert_placeholders(self, content: str) -> str:
        """Flag placeholder divs for merger to inject scraped content."""
        # Replace placeholder divs with a marker
        content = re.sub(
            r'<div\s+id="([^"]*-placeholder)"[^>]*>.*?</div>',
            r"<!-- PLACEHOLDER: \1 -->",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        return content

    def _strip_simple_tags(self, content: str) -> str:
        """Strip simple wrapper tags, keep inner content."""
        # Remove Tooltip, Frame, Icon - keep inner text
        tags_to_strip = ["Tooltip", "Frame", "Icon", "ParamField", "ResponseField"]

        for tag in tags_to_strip:
            # Remove opening tag
            content = re.sub(
                f"<{tag}[^>]*>", "", content, flags=re.IGNORECASE | re.DOTALL
            )
            # Remove closing tag
            content = re.sub(f"</{tag}>", "", content, flags=re.IGNORECASE)

        return content

    def get_frontmatter(self) -> dict[str, Any]:
        """Get extracted frontmatter."""
        return self.frontmatter
