"""Multi-source merge logic with priority rules."""

from venice_kb.utils.logging import logger

# Merge priority rules (higher number = higher priority)
MERGE_PRIORITY = {
    "swagger": 100,  # OpenAPI spec for endpoints/schemas
    "github": 80,  # GitHub MDX for prose/guides
    "web": 60,  # Live site scrape for dynamic content
    "api": 40,  # Live API probe
}


def merge_sources(sources: dict[str, dict[str, str]]) -> dict[str, str]:
    """Merge content from multiple sources based on priority rules.

    Args:
        sources: Dict like {"github": {path: content}, "swagger": {...}}

    Returns:
        Merged dictionary mapping paths to content
    """
    merged = {}

    # Get all unique paths
    all_paths = set()
    for source_content in sources.values():
        all_paths.update(source_content.keys())

    # For each path, select content from highest priority source
    for path in all_paths:
        selected_source = None
        highest_priority = -1

        for source_name, source_content in sources.items():
            if path in source_content:
                priority = MERGE_PRIORITY.get(source_name, 0)
                if priority > highest_priority:
                    highest_priority = priority
                    selected_source = source_name

        if selected_source:
            merged[path] = sources[selected_source][path]
            logger.debug(f"Merged {path} from {selected_source} (priority {highest_priority})")

    logger.info(f"Merged {len(merged)} pages from {len(sources)} sources")

    return merged
