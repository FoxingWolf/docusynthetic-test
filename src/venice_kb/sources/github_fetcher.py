"""Fetch raw MDX files from veniceai/api-docs GitHub repository."""

import httpx
from pathlib import Path
from venice_kb.config import GITHUB_RAW_BASE, GITHUB_TOKEN, CACHE_DIR
from venice_kb.utils.logging import logger
from venice_kb.utils.hashing import compute_hash


async def fetch_mdx_file(page_path: str, use_cache: bool = True) -> str | None:
    """Fetch a single MDX file from GitHub.
    
    Args:
        page_path: Path like "overview/about-venice"
        use_cache: Whether to use cached content
        
    Returns:
        MDX content or None if not found
    """
    # Ensure .mdx extension
    if not page_path.endswith(".mdx"):
        page_path = f"{page_path}.mdx"
    
    url = f"{GITHUB_RAW_BASE}/{page_path}"
    
    # Check cache
    if use_cache:
        cache_file = CACHE_DIR / "github" / page_path
        if cache_file.exists():
            logger.debug(f"Using cached: {page_path}")
            return cache_file.read_text()
    
    # Fetch from GitHub
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            content = response.text
            
            # Cache the content
            cache_file = CACHE_DIR / "github" / page_path
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content)
            
            logger.info(f"Fetched: {page_path}")
            return content
    
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch {page_path}: {e}")
        return None


async def fetch_all_mdx_files(page_paths: list[str], use_cache: bool = True) -> dict[str, str]:
    """Fetch multiple MDX files concurrently.
    
    Args:
        page_paths: List of page paths
        use_cache: Whether to use cached content
        
    Returns:
        Dictionary mapping paths to content
    """
    results = {}
    for path in page_paths:
        content = await fetch_mdx_file(path, use_cache)
        if content:
            results[path] = content
    
    return results
