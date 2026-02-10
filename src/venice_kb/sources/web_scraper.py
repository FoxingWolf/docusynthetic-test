"""Web scraper for JavaScript-heavy Venice AI documentation pages."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)

# Pages that need web scraping
PAGES_TO_SCRAPE = [
    "https://docs.venice.ai/models/overview",
    "https://docs.venice.ai/models/text",
    "https://docs.venice.ai/models/image",
    "https://docs.venice.ai/models/audio",
    "https://docs.venice.ai/models/video",
    "https://docs.venice.ai/models/embeddings",
    "https://docs.venice.ai/overview/pricing",
    "https://docs.venice.ai/overview/beta-models",
]


class WebScraper:
    """Scrape JavaScript-rendered content from Venice AI docs."""

    def __init__(self, cache_dir: Path | None = None, skip_scraping: bool = False):
        self.cache_dir = cache_dir or Path(".cache/web")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.skip_scraping = skip_scraping
        self.playwright_available = False
        self.browser = None
        self.playwright = None

    async def _init_playwright(self) -> bool:
        """Initialize Playwright browser."""
        if self.skip_scraping:
            return False

        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.playwright_available = True
            logger.info("Playwright initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Playwright not available: {e}. Will use fallback.")
            self.playwright_available = False
            return False

    async def _close_playwright(self) -> None:
        """Close Playwright browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        # Use URL path as filename
        path_part = url.replace("https://docs.venice.ai/", "").replace("/", "_")
        return self.cache_dir / f"{path_part}.html"

    async def scrape_page(self, url: str, use_cache: bool = True) -> str:
        """
        Scrape a single page.

        Returns:
            Scraped HTML content or fallback message
        """
        cache_path = self._get_cache_path(url)

        # Check cache
        if use_cache and cache_path.exists():
            async with aiofiles.open(cache_path, "r", encoding="utf-8") as f:
                content = await f.read()
            logger.debug(f"Using cached scraped page: {url}")
            return content

        # Try to scrape with Playwright
        if not self.playwright_available:
            await self._init_playwright()

        if self.playwright_available and self.browser:
            try:
                page = await self.browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait for placeholder divs to be replaced
                # Try to wait for content to load, but don't fail if it doesn't
                try:
                    await page.wait_for_selector("table, .vpt-model-name", timeout=10000)
                except Exception:
                    logger.warning(f"Timeout waiting for dynamic content on {url}")

                # Get the rendered HTML
                content = await page.content()
                await page.close()

                # Cache the result
                async with aiofiles.open(cache_path, "w", encoding="utf-8") as f:
                    await f.write(content)

                logger.info(f"Scraped: {url}")
                return content
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")

        # Fallback: return placeholder message
        fallback = f'<div class="fallback">[Dynamic content — see {url}]</div>'
        async with aiofiles.open(cache_path, "w", encoding="utf-8") as f:
            await f.write(fallback)
        return fallback

    async def scrape_all(
        self, urls: list[str] | None = None, use_cache: bool = True
    ) -> dict[str, str]:
        """
        Scrape all specified pages.

        Args:
            urls: List of URLs to scrape, defaults to PAGES_TO_SCRAPE
            use_cache: Whether to use cached results

        Returns:
            Dict mapping URL to scraped HTML content
        """
        urls = urls or PAGES_TO_SCRAPE

        try:
            await self._init_playwright()
            tasks = [self.scrape_page(url, use_cache) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            scraped = {}
            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to scrape {url}: {result}")
                    fallback = f'<div class="fallback">[Dynamic content — see {url}]</div>'
                    scraped[url] = fallback
                else:
                    scraped[url] = result

            return scraped
        finally:
            await self._close_playwright()
