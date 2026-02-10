"""Split large pages into logical chunks."""

import logging
import re
from typing import Any

try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)


class Chunker:
    """Split pages into logical chunks based on token count."""

    def __init__(self, max_tokens: int = 3500):
        self.max_tokens = max_tokens
        if tiktoken:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            logger.warning("tiktoken not available, using approximate token counting")
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Approximate: ~4 characters per token
            return len(text) // 4

    def split_on_headings(self, content: str) -> list[dict[str, Any]]:
        """
        Split content on heading boundaries.

        Returns:
            List of dicts with 'heading', 'level', 'content', 'tokens'
        """
        # Split on markdown headings
        heading_pattern = r"^(#{1,6})\s+(.+)$"
        lines = content.split("\n")

        sections = []
        current_section: dict[str, Any] = {
            "heading": "",
            "level": 0,
            "content": "",
            "heading_path": [],
        }
        heading_stack: list[tuple[int, str]] = []

        for line in lines:
            match = re.match(heading_pattern, line)
            if match:
                # Save previous section
                if current_section["content"]:
                    current_section["tokens"] = self.count_tokens(current_section["content"])
                    sections.append(current_section)

                # Start new section
                level = len(match.group(1))
                heading = match.group(2)

                # Update heading stack
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading))

                heading_path = [h for _, h in heading_stack]

                current_section = {
                    "heading": heading,
                    "level": level,
                    "content": line + "\n",
                    "heading_path": heading_path,
                }
            else:
                current_section["content"] += line + "\n"

        # Save final section
        if current_section["content"]:
            current_section["tokens"] = self.count_tokens(current_section["content"])
            sections.append(current_section)

        return sections

    def chunk_page(self, path: str, content: str) -> list[dict[str, Any]]:
        """
        Chunk a single page if it exceeds max_tokens.

        Args:
            path: Page path
            content: Page content

        Returns:
            List of chunks (may be single chunk if page is small)
        """
        total_tokens = self.count_tokens(content)

        if total_tokens <= self.max_tokens:
            # Page is small enough, don't chunk
            return [
                {
                    "path": path,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "heading_path": [],
                    "content": content,
                    "tokens": total_tokens,
                }
            ]

        logger.info(f"Chunking {path} ({total_tokens} tokens > {self.max_tokens})")

        # Split on headings
        sections = self.split_on_headings(content)

        # Combine sections into chunks
        chunks = []
        current_chunk = ""
        current_tokens = 0
        current_heading_path: list[str] = []

        for section in sections:
            section_tokens = section["tokens"]

            # If single section exceeds max, we have to include it anyway
            # (otherwise we'd lose content)
            if current_tokens + section_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunks.append(
                    {
                        "content": current_chunk,
                        "tokens": current_tokens,
                        "heading_path": current_heading_path.copy(),
                    }
                )
                current_chunk = ""
                current_tokens = 0

            current_chunk += section["content"]
            current_tokens += section_tokens
            if section.get("heading_path"):
                current_heading_path = section["heading_path"]

        # Save final chunk
        if current_chunk:
            chunks.append(
                {
                    "content": current_chunk,
                    "tokens": current_tokens,
                    "heading_path": current_heading_path.copy(),
                }
            )

        # Add metadata
        total_chunks = len(chunks)
        result = []
        for i, chunk in enumerate(chunks):
            result.append(
                {
                    "path": path,
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "heading_path": chunk["heading_path"],
                    "content": chunk["content"],
                    "tokens": chunk["tokens"],
                }
            )

        logger.info(f"Split {path} into {total_chunks} chunks")
        return result

    def chunk_all(self, pages: dict[str, str]) -> list[dict[str, Any]]:
        """
        Chunk all pages.

        Returns:
            List of all chunks from all pages
        """
        all_chunks = []

        for path, content in pages.items():
            chunks = self.chunk_page(path, content)
            all_chunks.extend(chunks)

        return all_chunks
