"""Live site scraper using Playwright."""

import hashlib
from datetime import datetime
from typing import List, Optional

from playwright.async_api import async_playwright

from docusynthetic.models import DocumentContent, DocumentMetadata, SourceType

from .base import BaseFetcher


class LiveSiteFetcher(BaseFetcher):
    """Fetches documentation from live website using Playwright."""

    def __init__(self, base_url: str = "https://docs.venice.ai", headless: bool = True):
        """Initialize live site fetcher.

        Args:
            base_url: Base URL of the documentation site.
            headless: Whether to run browser in headless mode.
        """
        self.base_url = base_url
        self.headless = headless

    async def fetch(self) -> List[DocumentContent]:
        """Fetch documentation from live site.

        Returns:
            List of DocumentContent objects.
        """
        documents = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                # Navigate to documentation home
                await page.goto(self.base_url, wait_until="networkidle")

                # Get all documentation links
                links = await self._get_documentation_links(page)

                # Visit each link and extract content
                for link in links:
                    try:
                        await page.goto(link, wait_until="networkidle")

                        # Extract page title
                        title_element = await page.query_selector("h1")
                        title = (
                            await title_element.inner_text()
                            if title_element
                            else link.split("/")[-1]
                        )

                        # Extract main content
                        content_element = await page.query_selector("main, article, .content")
                        if content_element:
                            content_html = await content_element.inner_html()
                            content_text = await content_element.inner_text()
                        else:
                            content_html = await page.content()
                            content_text = await page.inner_text("body")

                        # Create content hash
                        content_hash = hashlib.sha256(content_text.encode()).hexdigest()

                        # Extract tags/categories if available
                        tags = await self._extract_tags(page)
                        category = await self._extract_category(page)

                        # Create metadata
                        metadata = DocumentMetadata(
                            title=title.strip(),
                            source=SourceType.LIVE_SITE,
                            source_url=link,
                            last_updated=datetime.now(),
                            tags=tags,
                            category=category,
                        )

                        # Create document
                        doc = DocumentContent(
                            metadata=metadata,
                            content=content_text,
                            raw_content=content_html,
                            content_hash=content_hash,
                        )
                        documents.append(doc)

                    except Exception as e:
                        print(f"Error fetching {link}: {e}")
                        continue

            finally:
                await browser.close()

        return documents

    async def _get_documentation_links(self, page) -> List[str]:
        """Extract all documentation links from the page.

        Args:
            page: Playwright page object.

        Returns:
            List of documentation URLs.
        """
        # Try to find navigation links
        links = []

        # Common selectors for documentation navigation
        selectors = [
            "nav a[href]",
            ".sidebar a[href]",
            ".navigation a[href]",
            ".docs-nav a[href]",
        ]

        for selector in selectors:
            elements = await page.query_selector_all(selector)
            for element in elements:
                href = await element.get_attribute("href")
                if href:
                    # Resolve relative URLs
                    if href.startswith("/"):
                        full_url = self.base_url.rstrip("/") + href
                    elif href.startswith("http"):
                        full_url = href
                    else:
                        full_url = self.base_url.rstrip("/") + "/" + href

                    # Only include documentation URLs
                    if full_url.startswith(self.base_url) and full_url not in links:
                        links.append(full_url)

        # If no links found, at least return the base URL
        if not links:
            links = [self.base_url]

        return links

    async def _extract_tags(self, page) -> List[str]:
        """Extract tags from the page.

        Args:
            page: Playwright page object.

        Returns:
            List of tags.
        """
        tags = []
        tag_selectors = [".tags a", ".tag", "[data-tag]"]

        for selector in tag_selectors:
            elements = await page.query_selector_all(selector)
            for element in elements:
                tag_text = await element.inner_text()
                if tag_text:
                    tags.append(tag_text.strip())

        return list(set(tags))  # Remove duplicates

    async def _extract_category(self, page) -> Optional[str]:
        """Extract category from the page.

        Args:
            page: Playwright page object.

        Returns:
            Category name or None.
        """
        category_selectors = [".category", ".breadcrumb", "[data-category]"]

        for selector in category_selectors:
            element = await page.query_selector(selector)
            if element:
                category_text = await element.inner_text()
                if category_text:
                    return category_text.strip()

        return None
