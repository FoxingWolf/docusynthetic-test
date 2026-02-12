"""Hit Venice API /models endpoint for live data."""

import httpx

from venice_kb.config import VENICE_API_BASE, VENICE_API_KEY
from venice_kb.utils.logging import logger


async def fetch_models_list(api_key: str | None = None) -> dict | None:
    """Fetch live models list from Venice API.

    Args:
        api_key: Venice API key (uses VENICE_API_KEY from config if not provided)

    Returns:
        Models list response dict or None
    """
    key = api_key or VENICE_API_KEY
    if not key:
        logger.warning("No API key provided, skipping live API probe")
        return None

    url = f"{VENICE_API_BASE}/models"
    headers = {"Authorization": f"Bearer {key}"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Fetched {len(data.get('data', []))} models from API")
            return data

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch models from API: {e}")
        return None
