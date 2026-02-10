"""Write knowledge base index and manifest files."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IndexWriter:
    """Write index and manifest files for knowledge base."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("knowledge_base")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_index(
        self,
        pages: dict[str, dict[str, Any]],
        endpoints: list[dict[str, Any]] | None = None,
    ) -> Path:
        """
        Write _index.json master catalog.

        Args:
            pages: Dict mapping path to page metadata
            endpoints: List of API endpoints

        Returns:
            Path to index file
        """
        index_data: dict[str, Any] = {
            "generated": datetime.now().isoformat(),
            "sections": self._build_sections(pages),
            "pages": self._build_page_list(pages),
            "endpoints": endpoints or [],
            "stats": self._calculate_stats(pages, endpoints),
        }

        index_path = self.output_dir / "_index.json"
        index_path.write_text(json.dumps(index_data, indent=2))

        logger.info(f"Wrote index to {index_path}")
        return index_path

    def _build_sections(self, pages: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """Build sections from pages."""
        sections_dict: dict[str, list[str]] = {}

        for path in pages.keys():
            # Extract top-level section
            parts = path.split("/")
            if len(parts) > 1:
                section = parts[0].replace(".md", "")
            else:
                section = "root"

            if section not in sections_dict:
                sections_dict[section] = []
            sections_dict[section].append(path)

        sections = []
        for section_name, section_paths in sorted(sections_dict.items()):
            sections.append({"name": section_name, "page_count": len(section_paths)})

        return sections

    def _build_page_list(self, pages: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """Build page list with metadata."""
        page_list = []

        for path, metadata in pages.items():
            page_list.append(
                {
                    "path": path,
                    "title": metadata.get("title", "Untitled"),
                    "tags": metadata.get("tags", []),
                    "token_count": metadata.get("token_count", 0),
                    "content_hash": metadata.get("content_hash", ""),
                    "summary": metadata.get("summary", ""),
                }
            )

        return sorted(page_list, key=lambda p: p["path"])

    def _calculate_stats(
        self, pages: dict[str, dict[str, Any]], endpoints: list[dict[str, Any]] | None
    ) -> dict[str, Any]:
        """Calculate knowledge base statistics."""
        total_tokens = sum(p.get("token_count", 0) for p in pages.values())

        return {
            "total_pages": len(pages),
            "total_endpoints": len(endpoints) if endpoints else 0,
            "total_tokens": total_tokens,
        }

    def write_manifest(
        self,
        git_commit: str | None = None,
        swagger_hash: str | None = None,
        build_duration: float | None = None,
        page_count: int = 0,
    ) -> Path:
        """
        Write _manifest.json build metadata.

        Args:
            git_commit: Git commit SHA
            swagger_hash: Hash of swagger.yaml
            build_duration: Build duration in seconds
            page_count: Number of pages built

        Returns:
            Path to manifest file
        """
        manifest_data = {
            "timestamp": datetime.now().isoformat(),
            "git_commit": git_commit,
            "swagger_hash": swagger_hash,
            "build_duration_seconds": build_duration,
            "page_count": page_count,
            "collector_version": "0.1.0",
        }

        manifest_path = self.output_dir / "_manifest.json"
        manifest_path.write_text(json.dumps(manifest_data, indent=2))

        logger.info(f"Wrote manifest to {manifest_path}")
        return manifest_path
