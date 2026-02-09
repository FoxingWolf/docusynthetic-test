"""GitHub MDX files fetcher."""

import hashlib
from datetime import datetime
from typing import List

import frontmatter
import httpx

from docusynthetic.models import DocumentContent, DocumentMetadata, SourceType

from .base import BaseFetcher


class GitHubMDXFetcher(BaseFetcher):
    """Fetches MDX documentation files from GitHub repository."""

    def __init__(
        self,
        repo_owner: str = "veniceai",
        repo_name: str = "api-docs",
        branch: str = "main",
        docs_path: str = "",
    ):
        """Initialize GitHub MDX fetcher.

        Args:
            repo_owner: GitHub repository owner.
            repo_name: GitHub repository name.
            branch: Branch to fetch from.
            docs_path: Path to documentation files within the repo.
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.docs_path = docs_path
        self.api_base = "https://api.github.com"

    async def fetch(self) -> List[DocumentContent]:
        """Fetch all MDX files from the GitHub repository.

        Returns:
            List of DocumentContent objects.
        """
        documents = []
        async with httpx.AsyncClient() as client:
            # Get repository tree
            tree_url = (
                f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}"
                f"/git/trees/{self.branch}?recursive=1"
            )
            response = await client.get(tree_url)
            response.raise_for_status()
            tree = response.json()

            # Find all MDX files
            mdx_files = [
                item
                for item in tree.get("tree", [])
                if item["path"].endswith((".mdx", ".md"))
                and (not self.docs_path or item["path"].startswith(self.docs_path))
            ]

            # Fetch each MDX file
            for file_info in mdx_files:
                content_url = (
                    f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}"
                    f"/contents/{file_info['path']}?ref={self.branch}"
                )
                file_response = await client.get(content_url)
                file_response.raise_for_status()
                file_data = file_response.json()

                # Decode content (base64 encoded)
                import base64

                raw_content = base64.b64decode(file_data["content"]).decode("utf-8")

                # Parse frontmatter
                post = frontmatter.loads(raw_content)
                metadata_dict = post.metadata

                # Create metadata
                title = metadata_dict.get("title", file_info["path"])
                tags = metadata_dict.get("tags", [])
                category = metadata_dict.get("category")

                metadata = DocumentMetadata(
                    title=title,
                    source=SourceType.GITHUB_MDX,
                    source_url=f"https://github.com/{self.repo_owner}/{self.repo_name}/blob/{self.branch}/{file_info['path']}",
                    last_updated=datetime.now(),
                    tags=tags if isinstance(tags, list) else [],
                    category=category,
                )

                # Create content hash
                content_hash = hashlib.sha256(raw_content.encode()).hexdigest()

                # Create document
                doc = DocumentContent(
                    metadata=metadata,
                    content=post.content,
                    raw_content=raw_content,
                    content_hash=content_hash,
                )
                documents.append(doc)

        return documents
