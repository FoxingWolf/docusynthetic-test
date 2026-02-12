"""Write _index.json master catalog."""

import json
from pathlib import Path

from venice_kb.diffing.models import PageMetadata
from venice_kb.utils.logging import logger


def write_index(
    output_dir: Path,
    page_manifest: dict[str, PageMetadata],
    source_versions: dict,
) -> Path:
    """Write _index.json master catalog.

    Args:
        output_dir: Output directory
        page_manifest: Dictionary of page metadata
        source_versions: Source version information

    Returns:
        Path to written index file
    """
    index_data = {
        "version": "1.0",
        "generated_at": source_versions.get("generated_at", ""),
        "sources": source_versions,
        "pages": {
            path: metadata.model_dump(mode="json") for path, metadata in page_manifest.items()
        },
        "stats": {
            "total_pages": len(page_manifest),
            "total_tokens": sum(m.token_count for m in page_manifest.values()),
        },
    }

    index_path = output_dir / "_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2)

    logger.info(f"Wrote index: {index_path}")
    return index_path
