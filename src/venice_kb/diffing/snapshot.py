"""Create and load KB snapshots for comparison."""

import json
from pathlib import Path
from datetime import datetime
from venice_kb.diffing.models import KBSnapshot, PageMetadata
from venice_kb.utils.logging import logger


def create_snapshot(
    page_manifest: dict[str, dict],
    source_versions: dict,
    snapshot_dir: Path,
) -> KBSnapshot:
    """Create a new snapshot of the knowledge base.
    
    Args:
        page_manifest: Dictionary mapping paths to page metadata
        source_versions: Dictionary of source version info
        snapshot_dir: Directory to save snapshot
        
    Returns:
        Created KBSnapshot instance
    """
    snapshot_id = datetime.utcnow().isoformat()
    
    # Convert dict to PageMetadata objects
    manifest = {}
    for path, data in page_manifest.items():
        if isinstance(data, PageMetadata):
            manifest[path] = data
        else:
            manifest[path] = PageMetadata(**data)
    
    snapshot = KBSnapshot(
        snapshot_id=snapshot_id,
        generated_at=datetime.utcnow(),
        source_versions=source_versions,
        page_manifest=manifest,
    )
    
    # Save snapshot
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_file = snapshot_dir / f"{snapshot_id.replace(':', '-')}.json"
    
    with open(snapshot_file, "w") as f:
        json.dump(snapshot.model_dump(mode="json"), f, indent=2)
    
    logger.info(f"Created snapshot: {snapshot_file}")
    return snapshot


def load_snapshot(snapshot_path: Path) -> KBSnapshot:
    """Load a snapshot from file.
    
    Args:
        snapshot_path: Path to snapshot JSON file
        
    Returns:
        Loaded KBSnapshot instance
    """
    with open(snapshot_path) as f:
        data = json.load(f)
    
    # Convert page_manifest dicts to PageMetadata objects
    if "page_manifest" in data:
        manifest = {}
        for path, metadata in data["page_manifest"].items():
            manifest[path] = PageMetadata(**metadata)
        data["page_manifest"] = manifest
    
    return KBSnapshot(**data)


def get_latest_snapshot(snapshot_dir: Path) -> KBSnapshot | None:
    """Get the most recent snapshot from a directory.
    
    Args:
        snapshot_dir: Directory containing snapshots
        
    Returns:
        Latest KBSnapshot or None if no snapshots exist
    """
    if not snapshot_dir.exists():
        return None
    
    snapshot_files = list(snapshot_dir.glob("*.json"))
    if not snapshot_files:
        return None
    
    # Sort by modification time (latest first)
    latest_file = max(snapshot_files, key=lambda p: p.stat().st_mtime)
    return load_snapshot(latest_file)


def list_snapshots(snapshot_dir: Path) -> list[Path]:
    """List all snapshots in a directory, sorted by date (newest first).
    
    Args:
        snapshot_dir: Directory containing snapshots
        
    Returns:
        List of snapshot file paths
    """
    if not snapshot_dir.exists():
        return []
    
    snapshot_files = list(snapshot_dir.glob("*.json"))
    return sorted(snapshot_files, key=lambda p: p.stat().st_mtime, reverse=True)
