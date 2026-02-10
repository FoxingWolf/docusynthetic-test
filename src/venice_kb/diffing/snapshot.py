"""Create and manage knowledge base snapshots."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from venice_kb.diffing.models import KBSnapshot, PageInfo
from venice_kb.processing.chunker import Chunker

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Create and load knowledge base snapshots."""

    def __init__(self, snapshot_dir: Path | None = None):
        self.snapshot_dir = snapshot_dir or Path("snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.chunker = Chunker()

    def create_snapshot(
        self, kb_path: Path, git_commit: str | None = None, swagger_hash: str | None = None
    ) -> KBSnapshot:
        """
        Create a snapshot of the knowledge base.

        Args:
            kb_path: Path to knowledge_base directory
            git_commit: Git commit SHA of source
            swagger_hash: Hash of swagger.yaml

        Returns:
            KBSnapshot object
        """
        pages: dict[str, PageInfo] = {}

        # Walk knowledge base directory
        for md_file in kb_path.rglob("*.md"):
            relative_path = str(md_file.relative_to(kb_path))

            # Skip special files
            if relative_path.startswith("_") or relative_path == "CHANGELOG.md":
                continue

            # Read file content
            content = md_file.read_text(encoding="utf-8")

            # Calculate hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Count tokens
            token_count = self.chunker.count_tokens(content)

            # Extract title (first H1)
            title = self._extract_title(content)

            # Extract tags from frontmatter if present
            tags = self._extract_tags(content)

            pages[relative_path] = PageInfo(
                path=relative_path,
                content_hash=content_hash,
                token_count=token_count,
                title=title,
                tags=tags,
            )

        snapshot = KBSnapshot(
            timestamp=datetime.now(), pages=pages, git_commit=git_commit, swagger_hash=swagger_hash
        )

        logger.info(f"Created snapshot with {len(pages)} pages")
        return snapshot

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"

    def _extract_tags(self, content: str) -> list[str]:
        """Extract tags from frontmatter."""
        # Look for tags in YAML frontmatter
        import re

        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                import yaml

                frontmatter = yaml.safe_load(match.group(1))
                if isinstance(frontmatter, dict) and "tags" in frontmatter:
                    tags = frontmatter["tags"]
                    if isinstance(tags, list):
                        return [str(t) for t in tags]
                    elif isinstance(tags, str):
                        return [t.strip() for t in tags.split(",")]
            except Exception:
                pass
        return []

    def save_snapshot(self, snapshot: KBSnapshot) -> Path:
        """
        Save snapshot to file.

        Args:
            snapshot: Snapshot to save

        Returns:
            Path to saved snapshot file
        """
        timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.snapshot_dir / f"snapshot_{timestamp_str}.json"

        snapshot_data = snapshot.model_dump(mode="json")
        snapshot_path.write_text(json.dumps(snapshot_data, indent=2, default=str))

        logger.info(f"Saved snapshot to {snapshot_path}")
        return snapshot_path

    def load_snapshot(self, path: Path) -> KBSnapshot:
        """Load snapshot from file."""
        data = json.loads(path.read_text())
        return KBSnapshot(**data)

    def load_latest_snapshot(self) -> KBSnapshot | None:
        """
        Load the most recent snapshot.

        Returns:
            Latest snapshot or None if no snapshots exist
        """
        snapshot_files = sorted(self.snapshot_dir.glob("snapshot_*.json"), reverse=True)

        if not snapshot_files:
            logger.info("No previous snapshots found")
            return None

        latest = snapshot_files[0]
        logger.info(f"Loading latest snapshot: {latest}")
        return self.load_snapshot(latest)

    def list_snapshots(self) -> list[Path]:
        """List all snapshot files."""
        return sorted(self.snapshot_dir.glob("snapshot_*.json"))
