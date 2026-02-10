"""Parse and cross-reference llms.txt and docs.json manifests."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ManifestLoader:
    """Load and parse documentation manifests."""

    def __init__(self, docs_json: dict[str, Any], llms_txt: str):
        self.docs_json = docs_json
        self.llms_txt = llms_txt

    def parse_llms_txt(self) -> list[dict[str, str]]:
        """
        Parse llms.txt into list of pages.

        Returns:
            List of dicts with 'url' and 'description'
        """
        pages = []
        lines = self.llms_txt.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # llms.txt format: URL: Description
            if ":" in line:
                parts = line.split(":", 1)
                url = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                pages.append({"url": url, "description": description})

        return pages

    def parse_docs_json(self) -> dict[str, Any]:
        """
        Parse docs.json navigation structure.

        Returns:
            Dict with 'tabs', 'pages', 'hierarchy'
        """
        result = {"tabs": [], "pages": [], "hierarchy": {}}

        def extract_pages(obj: Any, breadcrumb: list[str]) -> None:
            if isinstance(obj, dict):
                # Extract page info
                if "page" in obj:
                    page_path = obj["page"]
                    if not page_path.endswith(".mdx"):
                        page_path += ".mdx"
                    title = obj.get("title", obj.get("name", ""))
                    result["pages"].append(
                        {"path": page_path, "title": title, "breadcrumb": breadcrumb.copy()}
                    )
                    result["hierarchy"][page_path] = breadcrumb.copy()

                # Extract tab info
                if "tab" in obj:
                    tab_name = obj["tab"]
                    result["tabs"].append(tab_name)
                    breadcrumb = [tab_name]

                # Extract group info
                if "group" in obj:
                    group_name = obj["group"]
                    breadcrumb = breadcrumb + [group_name]

                # Recurse
                for key, value in obj.items():
                    if key not in ["page", "tab", "group", "title", "name"]:
                        extract_pages(value, breadcrumb)

            elif isinstance(obj, list):
                for item in obj:
                    extract_pages(item, breadcrumb)

        extract_pages(self.docs_json, [])
        return result

    def get_canonical_page_list(self) -> list[dict[str, Any]]:
        """
        Build canonical list of all documentation pages.

        Cross-references docs.json and llms.txt.

        Returns:
            List of dicts with 'path', 'title', 'url', 'description', 'breadcrumb'
        """
        docs_info = self.parse_docs_json()
        llms_pages = self.parse_llms_txt()

        # Create URL to description map from llms.txt
        url_to_desc = {page["url"]: page["description"] for page in llms_pages}

        canonical_pages = []
        for page in docs_info["pages"]:
            # Try to match with llms.txt entry
            page_url = f"https://docs.venice.ai/{page['path'].replace('.mdx', '')}"
            description = url_to_desc.get(page_url, "")

            canonical_pages.append(
                {
                    "path": page["path"],
                    "title": page["title"],
                    "url": page_url,
                    "description": description,
                    "breadcrumb": page["breadcrumb"],
                }
            )

        # Find pages in llms.txt but not in docs.json (newer pages)
        docs_urls = {page["url"] for page in canonical_pages}
        for llms_page in llms_pages:
            if llms_page["url"] not in docs_urls:
                # Extract path from URL
                path = llms_page["url"].replace("https://docs.venice.ai/", "") + ".mdx"
                logger.info(f"Found page in llms.txt not in docs.json: {path}")
                canonical_pages.append(
                    {
                        "path": path,
                        "title": llms_page["description"],
                        "url": llms_page["url"],
                        "description": llms_page["description"],
                        "breadcrumb": [],
                    }
                )

        return canonical_pages
