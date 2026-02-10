"""Write knowledge base files with frontmatter."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from venice_kb.processing.chunker import Chunker

logger = logging.getLogger(__name__)


class KBWriter:
    """Write knowledge base files to disk."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("knowledge_base")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunker = Chunker()

    def write_page(
        self,
        path: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Write a single page with frontmatter.

        Args:
            path: Relative path within knowledge base
            content: Markdown content
            metadata: Additional metadata for frontmatter

        Returns:
            Path to written file
        """
        # Prepare output path
        output_path = self.output_dir / path.replace(".mdx", ".md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate metadata
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        token_count = self.chunker.count_tokens(content)

        # Extract title
        title = self._extract_title(content)

        # Build frontmatter
        frontmatter = {
            "title": title,
            "source": "venice-kb-collector",
            "last_updated": datetime.now().isoformat(),
            "content_hash": content_hash,
            "token_count": token_count,
            "tags": metadata.get("tags", []) if metadata else [],
        }

        # Add any additional metadata
        if metadata:
            for key, value in metadata.items():
                if key not in frontmatter and key != "tags":
                    frontmatter[key] = value

        # Write file with frontmatter
        full_content = self._format_with_frontmatter(frontmatter, content)
        output_path.write_text(full_content, encoding="utf-8")

        logger.debug(f"Wrote {output_path}")
        return output_path

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"

    def _format_with_frontmatter(self, frontmatter: dict[str, Any], content: str) -> str:
        """Format content with YAML frontmatter."""
        # Remove existing frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].lstrip()

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n\n{content}"

    def write_all(
        self, pages: dict[str, str], metadata: dict[str, dict[str, Any]] | None = None
    ) -> list[Path]:
        """
        Write all pages.

        Args:
            pages: Dict mapping path to content
            metadata: Optional dict mapping path to metadata

        Returns:
            List of written file paths
        """
        written_paths = []

        for path, content in pages.items():
            page_metadata = metadata.get(path) if metadata else None
            output_path = self.write_page(path, content, page_metadata)
            written_paths.append(output_path)

        logger.info(f"Wrote {len(written_paths)} pages to {self.output_dir}")
        return written_paths

    def write_swagger(self, swagger_content: str) -> Path:
        """Write swagger.yaml to knowledge base."""
        swagger_path = self.output_dir / "swagger.yaml"
        swagger_path.write_text(swagger_content)
        logger.info(f"Wrote swagger.yaml to {swagger_path}")
        return swagger_path

    def create_directory_structure(self) -> None:
        """Create standard directory structure."""
        directories = [
            "overview",
            "guides",
            "models",
            "api-reference/endpoints",
            "meta",
        ]

        for dir_path in directories:
            (self.output_dir / dir_path).mkdir(parents=True, exist_ok=True)

        logger.info("Created knowledge base directory structure")
