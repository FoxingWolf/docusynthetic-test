"""Playwright-based web scraping for JS-rendered pages."""

from playwright.async_api import async_playwright
from venice_kb.config import LIVE_DOCS_BASE, DYNAMIC_PAGES
from venice_kb.utils.logging import logger


async def scrape_page(page_path: str) -> str | None:
    """Scrape a single page using Playwright.
    
    Args:
        page_path: Page path like "/models/overview"
        
    Returns:
        Rendered HTML content or None
    """
    url = f"{LIVE_DOCS_BASE}{page_path}"
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for dynamic content to render
            await page.wait_for_timeout(2000)
            
            # Get rendered HTML
            content = await page.content()
            
            await browser.close()
            
            logger.info(f"Scraped: {page_path}")
            return content
    
    except Exception as e:
        logger.error(f"Failed to scrape {page_path}: {e}")
        return None


async def scrape_dynamic_pages(use_cache: bool = True) -> dict[str, str]:
    """Scrape all dynamic pages that require JavaScript rendering.
    
    Args:
        use_cache: Whether to use cached content
        
    Returns:
        Dictionary mapping page paths to HTML content
    """
    results = {}
    
    for page_path in DYNAMIC_PAGES:
        content = await scrape_page(page_path)
        if content:
            results[page_path] = content
    
    return results
