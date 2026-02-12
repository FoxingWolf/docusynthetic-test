"""Diff two KB snapshots and generate change report."""

import difflib
from datetime import datetime

from venice_kb.diffing.models import (
    ChangeEntry,
    ChangeType,
    DiffReport,
    KBSnapshot,
    SeverityLevel,
)

# Severity classification rules based on path patterns
SEVERITY_RULES = {
    "api-reference/endpoint/": SeverityLevel.IMPORTANT,
    "api-reference/error-codes": SeverityLevel.IMPORTANT,
    "api-reference/rate-limiting": SeverityLevel.IMPORTANT,
    "overview/deprecations": SeverityLevel.BREAKING,
    "overview/beta-models": SeverityLevel.INFORMATIONAL,
    "overview/pricing": SeverityLevel.IMPORTANT,
    "models/": SeverityLevel.INFORMATIONAL,
    "guides/": SeverityLevel.INFORMATIONAL,
    "overview/privacy": SeverityLevel.INFORMATIONAL,
}

# Patterns that upgrade severity to BREAKING
BREAKING_SIGNALS = [
    "removed",
    "deprecated",
    "no longer",
    "breaking",
    "required parameter",
    "schema change",
    "endpoint removed",
    "status code changed",
    "authentication changed",
]


def classify_severity(path: str, change_type: ChangeType, diff_text: str = "") -> SeverityLevel:
    """Classify the severity of a change.

    Args:
        path: Page path
        change_type: Type of change
        diff_text: Diff text to analyze for breaking signals

    Returns:
        Severity level
    """
    # Check for breaking signals in diff
    diff_lower = diff_text.lower()
    if any(signal in diff_lower for signal in BREAKING_SIGNALS):
        return SeverityLevel.BREAKING

    # Apply path-based rules
    for pattern, severity in SEVERITY_RULES.items():
        if pattern in path:
            return severity

    # Default severity based on change type
    if change_type == ChangeType.REMOVED:
        return SeverityLevel.IMPORTANT
    elif change_type == ChangeType.ADDED:
        return SeverityLevel.INFORMATIONAL
    else:
        return SeverityLevel.COSMETIC


def generate_diff_preview(old_content: str, new_content: str, max_chars: int = 500) -> str:
    """Generate a unified diff preview.

    Args:
        old_content: Old version content
        new_content: New version content
        max_chars: Maximum characters to include

    Returns:
        Diff preview string
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm="",
        n=3,  # Context lines
    )

    diff_text = "".join(diff)
    if len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars] + "\n..."

    return diff_text


def diff_snapshots(
    old_snapshot: KBSnapshot,
    new_snapshot: KBSnapshot,
    kb_dir: str | None = None,
) -> DiffReport:
    """Generate a diff report between two snapshots.

    Args:
        old_snapshot: Previous snapshot
        new_snapshot: Current snapshot
        kb_dir: Optional path to KB directory for loading content

    Returns:
        DiffReport with all changes categorized by severity
    """
    old_paths = old_snapshot.get_page_paths()
    new_paths = new_snapshot.get_page_paths()

    added_paths = new_paths - old_paths
    removed_paths = old_paths - new_paths
    common_paths = old_paths & new_paths

    changes = []
    stats = {
        "added": len(added_paths),
        "removed": len(removed_paths),
        "modified": 0,
        "unchanged": 0,
    }

    # Process added pages
    for path in added_paths:
        metadata = new_snapshot.page_manifest[path]
        change = ChangeEntry(
            change_type=ChangeType.ADDED,
            severity=classify_severity(path, ChangeType.ADDED),
            path=path,
            section=_path_to_section(path),
            title=f"New {metadata.title}",
            details=f"Added new page: {metadata.title}",
            new_hash=metadata.hash,
            new_token_count=metadata.token_count,
        )
        changes.append(change)

    # Process removed pages
    for path in removed_paths:
        metadata = old_snapshot.page_manifest[path]
        change = ChangeEntry(
            change_type=ChangeType.REMOVED,
            severity=classify_severity(path, ChangeType.REMOVED),
            path=path,
            section=_path_to_section(path),
            title=f"Removed {metadata.title}",
            details=f"Removed page: {metadata.title}",
            old_hash=metadata.hash,
            old_token_count=metadata.token_count,
        )
        changes.append(change)

    # Process modified pages
    for path in common_paths:
        old_meta = old_snapshot.page_manifest[path]
        new_meta = new_snapshot.page_manifest[path]

        if old_meta.hash == new_meta.hash:
            stats["unchanged"] += 1
            continue

        stats["modified"] += 1

        # Generate diff preview if content is available
        diff_preview = ""
        # Note: In a full implementation, we'd load actual content here
        # For now, use token count change as a heuristic

        severity = classify_severity(path, ChangeType.MODIFIED, diff_preview)

        # Adjust severity based on token count change
        token_change_pct = abs(new_meta.token_count - old_meta.token_count) / max(
            old_meta.token_count, 1
        )
        if token_change_pct < 0.05 and severity == SeverityLevel.INFORMATIONAL:
            severity = SeverityLevel.COSMETIC

        change = ChangeEntry(
            change_type=ChangeType.MODIFIED,
            severity=severity,
            path=path,
            section=_path_to_section(path),
            title=f"Updated {new_meta.title}",
            details=f"Modified content in {new_meta.title}",
            old_hash=old_meta.hash,
            new_hash=new_meta.hash,
            old_token_count=old_meta.token_count,
            new_token_count=new_meta.token_count,
            diff_preview=diff_preview or None,
        )
        changes.append(change)

    # Categorize changes by severity
    breaking = [c for c in changes if c.severity == SeverityLevel.BREAKING]
    important = [c for c in changes if c.severity == SeverityLevel.IMPORTANT]
    informational = [c for c in changes if c.severity == SeverityLevel.INFORMATIONAL]
    cosmetic = [c for c in changes if c.severity == SeverityLevel.COSMETIC]

    # Generate summary
    summary_parts = []
    if breaking:
        summary_parts.append(f"{len(breaking)} breaking change(s)")
    if important:
        summary_parts.append(f"{len(important)} important change(s)")
    if added_paths:
        summary_parts.append(f"{len(added_paths)} new page(s)")
    if removed_paths:
        summary_parts.append(f"{len(removed_paths)} removed page(s)")

    summary = ", ".join(summary_parts) if summary_parts else "No significant changes"

    return DiffReport(
        generated_at=datetime.now(),
        previous_snapshot=old_snapshot.snapshot_id,
        current_snapshot=new_snapshot.snapshot_id,
        summary=summary,
        stats=stats,
        breaking_changes=breaking,
        important_changes=important,
        informational_changes=informational,
        cosmetic_changes=cosmetic,
    )


def _path_to_section(path: str) -> str:
    """Convert a file path to a readable section name.

    Args:
        path: File path like "api-reference/endpoint/chat/completions.md"

    Returns:
        Section name like "API Reference > Endpoint > Chat > Completions"
    """
    # Remove .md extension
    path = path.replace(".md", "")

    # Split by / and convert to title case
    parts = [p.replace("-", " ").replace("_", " ").title() for p in path.split("/")]

    return " > ".join(parts)
