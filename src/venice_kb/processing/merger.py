"""Merge content from multiple sources into final pages."""

import logging
import re
from typing import Any

from venice_kb.processing.mdx_converter import MDXConverter
from venice_kb.processing.html_converter import HTMLConverter

logger = logging.getLogger(__name__)


class Merger:
    """Merge content from different sources into final documentation pages."""

    def __init__(
        self,
        pages: dict[str, str],
        canonical_pages: list[dict[str, Any]],
        openapi_endpoints: list[dict[str, Any]] | None = None,
        scraped_content: dict[str, str] | None = None,
    ):
        self.pages = pages  # MDX content from GitHub
        self.canonical_pages = canonical_pages
        self.openapi_endpoints = openapi_endpoints or []
        self.scraped_content = scraped_content or {}

    def merge_page(self, page_info: dict[str, Any]) -> str:
        """
        Merge a single page from all available sources.

        Args:
            page_info: Dict with 'path', 'title', 'url', 'breadcrumb', etc.

        Returns:
            Merged markdown content
        """
        path = page_info["path"]
        title = page_info["title"]
        breadcrumb = page_info.get("breadcrumb", [])

        # Start with MDX content from GitHub
        mdx_content = self.pages.get(path, "")

        if not mdx_content:
            logger.warning(f"No MDX content found for {path}")
            # Create minimal page
            return f"# {title}\n\n*Documentation for this page is not yet available.*\n"

        # Convert MDX to Markdown
        converter = MDXConverter(mdx_content)
        markdown = converter.convert()

        # Add breadcrumb navigation
        if breadcrumb:
            breadcrumb_text = " > ".join(breadcrumb)
            markdown = f"*{breadcrumb_text}*\n\n{markdown}"

        # Replace placeholders with scraped content
        markdown = self._inject_scraped_content(markdown, page_info)

        # Enrich endpoint pages with OpenAPI data
        markdown = self._enrich_with_openapi(markdown, page_info)

        return markdown

    def _inject_scraped_content(self, markdown: str, page_info: dict[str, Any]) -> str:
        """Inject scraped web content into placeholder locations."""
        url = page_info.get("url", "")

        if url not in self.scraped_content:
            return markdown

        scraped_html = self.scraped_content[url]

        # Convert scraped HTML to markdown
        html_converter = HTMLConverter(scraped_html)
        scraped_markdown = html_converter.convert()

        # Find placeholder comments and replace them
        # Format: <!-- PLACEHOLDER: some-id-placeholder -->
        placeholder_pattern = r"<!-- PLACEHOLDER: ([^>]+) -->"

        def replace_placeholder(match: re.Match[str]) -> str:
            placeholder_id = match.group(1)
            logger.info(f"Replacing placeholder {placeholder_id} with scraped content")
            return scraped_markdown

        markdown = re.sub(placeholder_pattern, replace_placeholder, markdown)

        return markdown

    def _enrich_with_openapi(self, markdown: str, page_info: dict[str, Any]) -> str:
        """Enrich endpoint pages with OpenAPI spec data."""
        path = page_info["path"]

        # Check if this is an API endpoint page
        # Typically under api-reference/endpoints/
        if "api-reference" not in path and "endpoints" not in path:
            return markdown

        # Try to find matching endpoint(s) by path
        # This is a simple heuristic - might need refinement
        page_path_part = path.replace(".mdx", "").split("/")[-1]

        for endpoint in self.openapi_endpoints:
            endpoint_path = endpoint["path"].lower().replace("/", "-").replace("_", "-")
            if page_path_part in endpoint_path or endpoint_path in page_path_part:
                logger.info(f"Enriching {path} with OpenAPI data for {endpoint['path']}")
                # Append or merge OpenAPI documentation
                # For now, append at the end
                openapi_section = self._format_openapi_endpoint(endpoint)
                markdown += f"\n\n---\n\n## API Specification\n\n{openapi_section}"
                break

        return markdown

    def _format_openapi_endpoint(self, endpoint: dict[str, Any]) -> str:
        """Format OpenAPI endpoint data as markdown."""
        lines = []

        # Parameters
        if endpoint.get("parameters"):
            lines.append("### Parameters\n")
            lines.append("| Name | Location | Type | Required | Description |")
            lines.append("|------|----------|------|----------|-------------|")
            for param in endpoint["parameters"]:
                name = param.get("name", "")
                location = param.get("in", "")
                param_type = param.get("type", "")
                required = "Yes" if param.get("required") else "No"
                description = param.get("description", "").replace("\n", " ")
                lines.append(
                    f"| `{name}` | {location} | {param_type} | {required} | {description} |"
                )
            lines.append("")

        # Response schemas
        if endpoint.get("responses"):
            lines.append("### Response Codes\n")
            for status_code, response in sorted(endpoint["responses"].items()):
                description = response.get("description", "")
                lines.append(f"- **{status_code}**: {description}")
            lines.append("")

        return "\n".join(lines)

    def merge_all(self) -> dict[str, str]:
        """
        Merge all pages.

        Returns:
            Dict mapping path to merged markdown content
        """
        merged_pages = {}

        for page_info in self.canonical_pages:
            path = page_info["path"]
            try:
                merged_content = self.merge_page(page_info)
                merged_pages[path] = merged_content
            except Exception as e:
                logger.error(f"Error merging {path}: {e}")
                # Create error page
                merged_pages[path] = f"# Error\n\nFailed to merge page: {e}\n"

        return merged_pages
