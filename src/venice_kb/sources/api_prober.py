"""Probe Venice AI API for live model catalog."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class APIProber:
    """Probe Venice AI API for live model data."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.venice.ai/api/v1"

    async def get_models(self) -> list[dict[str, Any]]:
        """
        Get live model catalog from Venice AI API.

        Returns:
            List of model dicts or empty list if API key not available
        """
        if not self.api_key:
            logger.warning("No API key provided, skipping API probe")
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(f"{self.base_url}/models", headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", []) if isinstance(data, dict) else data
                    logger.info(f"Retrieved {len(models)} models from API")
                    return models
                elif response.status_code == 401:
                    logger.error("Invalid API key")
                    return []
                else:
                    logger.error(f"API returned status {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error probing API: {e}")
            return []
