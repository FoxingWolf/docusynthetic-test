"""Parse swagger.yaml OpenAPI spec into structured endpoint docs."""

import yaml
import httpx
from venice_kb.config import OPENAPI_URL, CACHE_DIR
from venice_kb.utils.logging import logger


async def fetch_openapi_spec(use_cache: bool = True) -> dict | None:
    """Fetch and parse OpenAPI specification.
    
    Args:
        use_cache: Whether to use cached spec
        
    Returns:
        Parsed OpenAPI spec dict or None
    """
    cache_file = CACHE_DIR / "openapi" / "swagger.yaml"
    
    # Check cache
    if use_cache and cache_file.exists():
        logger.debug("Using cached OpenAPI spec")
        with open(cache_file) as f:
            return yaml.safe_load(f)
    
    # Fetch from URL
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENAPI_URL, timeout=30.0)
            response.raise_for_status()
            content = response.text
            
            # Cache the spec
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content)
            
            logger.info("Fetched OpenAPI spec")
            return yaml.safe_load(content)
    
    except (httpx.HTTPError, yaml.YAMLError) as e:
        logger.error(f"Failed to fetch/parse OpenAPI spec: {e}")
        return None


def parse_endpoints(spec: dict) -> dict[str, dict]:
    """Parse endpoints from OpenAPI spec.
    
    Args:
        spec: OpenAPI specification dict
        
    Returns:
        Dictionary mapping endpoint paths to metadata
    """
    endpoints = {}
    
    if "paths" not in spec:
        return endpoints
    
    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                endpoint_id = f"{method.upper()} {path}"
                endpoints[endpoint_id] = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "parameters": details.get("parameters", []),
                    "requestBody": details.get("requestBody", {}),
                    "responses": details.get("responses", {}),
                }
    
    return endpoints
