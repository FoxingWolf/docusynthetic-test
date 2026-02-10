"""Deduplicate pages with identical or near-identical content."""

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Deduplicator:
    """Deduplicate pages based on content hash and similarity."""

    def __init__(self, pages: dict[str, str]):
        self.pages = pages

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Lowercase
        text = text.lower()
        return text

    def _content_hash(self, content: str) -> str:
        """Calculate SHA256 hash of normalized content."""
        normalized = self._normalize_text(content)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def deduplicate_exact(self) -> dict[str, str]:
        """
        Remove exact duplicates based on content hash.

        Returns:
            Dict of deduplicated pages (keeps first occurrence)
        """
        seen_hashes: dict[str, str] = {}  # hash -> first path
        unique_pages: dict[str, str] = {}

        for path, content in self.pages.items():
            content_hash = self._content_hash(content)

            if content_hash in seen_hashes:
                first_path = seen_hashes[content_hash]
                logger.info(f"Duplicate content found: {path} is identical to {first_path}")
            else:
                seen_hashes[content_hash] = path
                unique_pages[path] = content

        logger.info(
            f"Deduplication: {len(self.pages)} pages -> {len(unique_pages)} unique pages"
        )
        return unique_pages

    def deduplicate_similar(
        self, threshold: float = 0.8, use_llm: bool = False
    ) -> dict[str, str]:
        """
        Detect and merge near-duplicate pages.

        Args:
            threshold: Similarity threshold (0-1) for considering pages similar
            use_llm: Whether to use LLM for merging (not implemented in this version)

        Returns:
            Dict of deduplicated pages
        """
        # First pass: exact deduplication
        unique_pages = self.deduplicate_exact()

        # Second pass: similarity detection (simplified version)
        # For a full implementation, you'd use tiktoken to count tokens
        # and calculate token overlap

        # For now, just use a simple heuristic:
        # If two pages have very similar length and share many words,
        # keep the longer one

        paths_to_check = list(unique_pages.keys())
        pages_to_remove = set()

        for i, path1 in enumerate(paths_to_check):
            if path1 in pages_to_remove:
                continue

            content1 = unique_pages[path1]
            words1 = set(self._normalize_text(content1).split())

            for path2 in paths_to_check[i + 1 :]:
                if path2 in pages_to_remove:
                    continue

                content2 = unique_pages[path2]
                words2 = set(self._normalize_text(content2).split())

                # Calculate Jaccard similarity
                if not words1 or not words2:
                    continue

                intersection = len(words1 & words2)
                union = len(words1 | words2)
                similarity = intersection / union if union > 0 else 0

                if similarity >= threshold:
                    # Keep the longer page
                    if len(content1) >= len(content2):
                        logger.info(
                            f"Similar pages detected: keeping {path1}, "
                            f"removing {path2} (similarity: {similarity:.2f})"
                        )
                        pages_to_remove.add(path2)
                    else:
                        logger.info(
                            f"Similar pages detected: keeping {path2}, "
                            f"removing {path1} (similarity: {similarity:.2f})"
                        )
                        pages_to_remove.add(path1)
                        break

        # Remove similar duplicates
        for path in pages_to_remove:
            unique_pages.pop(path, None)

        logger.info(f"After similarity dedup: {len(unique_pages)} pages remain")
        return unique_pages
