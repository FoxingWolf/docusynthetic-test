"""Fetch documentation files from Venice AI GitHub repository."""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import aiofiles
import httpx

logger = logging.getLogger(__name__)


class GitHubFetcher:
    """Fetches .mdx files and other resources from veniceai/api-docs repository."""

    def __init__(
        self,
        repo_owner: str = "veniceai",
        repo_name: str = "api-docs",
        branch: str = "main",
        cache_dir: Path | None = None,
        github_token: str | None = None,
    ):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.cache_dir = cache_dir or Path(".cache/github")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.github_token = github_token
        self.base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}"
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    def _get_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    async def fetch_file(
        self, path: str, use_cache: bool = True
    ) -> tuple[str, dict[str, Any]]:
        """
        Fetch a single file from GitHub.

        Returns:
            Tuple of (content, metadata)
        """
        cache_path = self.cache_dir / path.lstrip("/")
        cache_meta_path = cache_path.with_suffix(cache_path.suffix + ".meta")

        # Check cache
        if use_cache and cache_path.exists():
            async with aiofiles.open(cache_path, "r", encoding="utf-8") as f:
                content = await f.read()
            metadata = {}
            if cache_meta_path.exists():
                async with aiofiles.open(cache_meta_path, "r") as f:
                    metadata = json.loads(await f.read())
            logger.debug(f"Using cached file: {path}")
            return content, metadata

        # Fetch from GitHub with retry and backoff
        url = f"{self.base_url}/{path}"
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=self._get_headers())
                    if response.status_code == 200:
                        content = response.text
                        metadata = {
                            "etag": response.headers.get("etag"),
                            "last_modified": response.headers.get("last-modified"),
                            "url": url,
                        }

                        # Cache the result
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        async with aiofiles.open(cache_path, "w", encoding="utf-8") as f:
                            await f.write(content)
                        async with aiofiles.open(cache_meta_path, "w") as f:
                            await f.write(json.dumps(metadata, indent=2))

                        logger.info(f"Fetched: {path}")
                        return content, metadata
                    elif response.status_code == 404:
                        logger.warning(f"File not found: {path}")
                        return "", {}
                    elif response.status_code == 403:
                        logger.warning(f"Rate limited on {path}, attempt {attempt + 1}")
                        await asyncio.sleep(retry_delay * (2**attempt))
                    else:
                        response.raise_for_status()
            except Exception as e:
                logger.error(f"Error fetching {path} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))
                else:
                    return "", {}

        return "", {}

    async def fetch_docs_json(self, use_cache: bool = True) -> dict[str, Any]:
        """Fetch and parse docs.json navigation manifest."""
        content, _ = await self.fetch_file("docs.json", use_cache)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse docs.json: {e}")
                return {}
        return {}

    async def fetch_llms_txt(self, use_cache: bool = True) -> str:
        """Fetch llms.txt file."""
        content, _ = await self.fetch_file("llms.txt", use_cache)
        return content

    async def fetch_swagger_yaml(self, use_cache: bool = True) -> str:
        """Fetch swagger.yaml OpenAPI specification."""
        content, _ = await self.fetch_file("swagger.yaml", use_cache)
        return content

    def extract_page_paths_from_docs_json(self, docs_json: dict[str, Any]) -> list[str]:
        """Extract all page paths from docs.json navigation structure."""
        paths = []

        def extract_recursive(obj: Any, current_path: str = "") -> None:
            if isinstance(obj, dict):
                # Check for page path
                if "page" in obj:
                    page_path = obj["page"]
                    if not page_path.endswith(".mdx"):
                        page_path += ".mdx"
                    paths.append(page_path)
                # Recurse into all dict values
                for value in obj.values():
                    extract_recursive(value, current_path)
            elif isinstance(obj, list):
                # Recurse into list items
                for item in obj:
                    extract_recursive(item, current_path)

        extract_recursive(docs_json)
        return list(set(paths))  # Remove duplicates

    async def fetch_all_pages(
        self, page_paths: list[str], use_cache: bool = True
    ) -> dict[str, str]:
        """
        Fetch all page files concurrently.

        Returns:
            Dict mapping page path to content
        """
        tasks = [self.fetch_file(path, use_cache) for path in page_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        pages = {}
        for path, result in zip(page_paths, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {path}: {result}")
                continue
            content, _ = result
            if content:
                pages[path] = content

        return pages

    async def fetch_all(self, use_cache: bool = True) -> dict[str, Any]:
        """
        Fetch all documentation resources.

        Returns:
            Dict with keys: docs_json, llms_txt, swagger_yaml, pages
        """
        # Fetch manifest files first
        docs_json_task = self.fetch_docs_json(use_cache)
        llms_txt_task = self.fetch_llms_txt(use_cache)
        swagger_task = self.fetch_swagger_yaml(use_cache)

        docs_json, llms_txt, swagger_yaml = await asyncio.gather(
            docs_json_task, llms_txt_task, swagger_task
        )

        # Extract page paths
        page_paths = self.extract_page_paths_from_docs_json(docs_json)
        logger.info(f"Found {len(page_paths)} pages in docs.json")

        # Fetch all pages
        pages = await self.fetch_all_pages(page_paths, use_cache)

        return {
            "docs_json": docs_json,
            "llms_txt": llms_txt,
            "swagger_yaml": swagger_yaml,
            "pages": pages,
            "page_paths": page_paths,
        }
