"""Hash-based and LLM-assisted deduplication."""

from venice_kb.utils.hashing import compute_hash
from venice_kb.utils.logging import logger


def deduplicate_content(contents: dict[str, str], use_llm: bool = False) -> dict[str, str]:
    """Deduplicate content from multiple sources.

    Args:
        contents: Dictionary mapping source IDs to content
        use_llm: Whether to use LLM for smart dedup

    Returns:
        Deduplicated dictionary
    """
    # Hash-based deduplication
    seen_hashes = {}
    deduplicated = {}

    for source_id, content in contents.items():
        content_hash = compute_hash(content)

        if content_hash not in seen_hashes:
            seen_hashes[content_hash] = source_id
            deduplicated[source_id] = content
        else:
            logger.debug(f"Duplicate content: {source_id} matches {seen_hashes[content_hash]}")

    logger.info(f"Deduplicated {len(contents)} items to {len(deduplicated)}")

    return deduplicated
