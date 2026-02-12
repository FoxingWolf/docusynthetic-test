"""Semantic chunking with token limits."""

from pydantic import BaseModel

from venice_kb.config import CHUNK_MAX_TOKENS, CHUNK_TARGET_TOKENS
from venice_kb.utils.logging import logger
from venice_kb.utils.tokens import count_tokens


class Chunk(BaseModel):
    """A chunk of content with metadata."""

    content: str
    token_count: int
    chunk_index: int


def chunk_content(
    content: str, target_tokens: int | None = None, max_tokens: int | None = None
) -> list[Chunk]:
    """Chunk content into semantic pieces with token limits.

    Args:
        content: Content to chunk
        target_tokens: Target tokens per chunk (default: CHUNK_TARGET_TOKENS)
        max_tokens: Maximum tokens per chunk (default: CHUNK_MAX_TOKENS)

    Returns:
        List of Chunk objects
    """
    target = target_tokens or CHUNK_TARGET_TOKENS
    max_size = max_tokens or CHUNK_MAX_TOKENS

    # Simple paragraph-based chunking
    paragraphs = content.split("\n\n")
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_index = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens > max_size and current_chunk:
            # Finalize current chunk
            chunk_content = "\n\n".join(current_chunk)
            chunks.append(
                Chunk(content=chunk_content, token_count=current_tokens, chunk_index=chunk_index)
            )
            chunk_index += 1
            current_chunk = []
            current_tokens = 0

        current_chunk.append(para)
        current_tokens += para_tokens

        # If we've reached target and have content, finalize
        if current_tokens >= target and len(current_chunk) > 0:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append(
                Chunk(content=chunk_content, token_count=current_tokens, chunk_index=chunk_index)
            )
            chunk_index += 1
            current_chunk = []
            current_tokens = 0

    # Add remaining content
    if current_chunk:
        chunk_content = "\n\n".join(current_chunk)
        chunks.append(
            Chunk(
                content=chunk_content,
                token_count=count_tokens(chunk_content),
                chunk_index=chunk_index,
            )
        )

    logger.debug(f"Chunked content into {len(chunks)} chunks")

    return chunks
