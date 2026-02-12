"""Parse llms.txt and docs.json manifest files."""

import json

import httpx

from venice_kb.config import CACHE_DIR, DOCS_JSON_URL, LLMS_TXT_URL
from venice_kb.utils.logging import logger


async def fetch_llms_txt(use_cache: bool = True) -> str | None:
    """Fetch llms.txt manifest.

    Args:
        use_cache: Whether to use cached content

    Returns:
        llms.txt content or None
    """
    cache_file = CACHE_DIR / "manifests" / "llms.txt"

    if use_cache and cache_file.exists():
        logger.debug("Using cached llms.txt")
        return cache_file.read_text()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(LLMS_TXT_URL, timeout=30.0)
            response.raise_for_status()
            content = response.text

            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content)

            logger.info("Fetched llms.txt")
            return content

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch llms.txt: {e}")
        return None


async def fetch_docs_json(use_cache: bool = True) -> dict | None:
    """Fetch docs.json navigation manifest.

    Args:
        use_cache: Whether to use cached content

    Returns:
        Parsed docs.json dict or None
    """
    cache_file = CACHE_DIR / "manifests" / "docs.json"

    if use_cache and cache_file.exists():
        logger.debug("Using cached docs.json")
        with open(cache_file) as f:
            return json.load(f)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(DOCS_JSON_URL, timeout=30.0)
            response.raise_for_status()
            content = response.text

            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content)

            logger.info("Fetched docs.json")
            return json.loads(content)

    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.error(f"Failed to fetch/parse docs.json: {e}")
        return None


def parse_llms_txt(content: str) -> list[str]:
    """Parse llms.txt to extract page paths.

    Args:
        content: llms.txt content

    Returns:
        List of page paths
    """
    paths = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # Extract path from URL or direct path
            if "https://" in line or "http://" in line:
                # Extract path from URL
                parts = line.split("/")
                if len(parts) > 3:
                    path = "/".join(parts[3:])
                    paths.append(path)
            else:
                paths.append(line)

    return paths
