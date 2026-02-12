"""Generate human and agent readable changelogs."""

from pathlib import Path

from venice_kb.diffing.models import ChangeEntry, ChangeType, DiffReport
from venice_kb.utils.logging import logger


def render_changelog_markdown(reports: list[DiffReport]) -> str:
    """Render changelog as Markdown.

    Args:
        reports: List of diff reports (newest first)

    Returns:
        Markdown formatted changelog
    """
    lines = ["# Venice API Docs Knowledge Base — Changelog\n"]

    for i, report in enumerate(reports):
        # Header
        is_latest = i == 0
        date_str = report.generated_at.strftime("%Y-%m-%d")
        header = f"## {date_str}"
        if is_latest:
            header += " (Latest Build)"
        lines.append(header)

        # Metadata
        prev_date = (
            report.previous_snapshot.split("T")[0]
            if "T" in report.previous_snapshot
            else report.previous_snapshot
        )
        source_info = report.stats
        lines.append(
            f"> Compared against: {prev_date} build | "
            f"Added: {source_info['added']}, Modified: {source_info['modified']}, "
            f"Removed: {source_info['removed']}, Unchanged: {source_info['unchanged']}\n"
        )

        # Breaking changes
        lines.append("### 🚨 Breaking Changes")
        if report.breaking_changes:
            for change in report.breaking_changes:
                lines.append(_format_change_entry(change))
        else:
            lines.append("_None detected_\n")

        # Important changes
        lines.append("### ⚠️ Important Changes")
        if report.important_changes:
            for change in report.important_changes:
                lines.append(_format_change_entry(change))
        else:
            lines.append("_None detected_\n")

        # Informational changes
        lines.append("### ℹ️ Informational Changes")
        if report.informational_changes:
            # Limit to first 10 to keep changelog readable
            for change in report.informational_changes[:10]:
                lines.append(_format_change_entry(change))
            if len(report.informational_changes) > 10:
                lines.append(f"_...and {len(report.informational_changes) - 10} more_\n")
        else:
            lines.append("_None detected_\n")

        # Cosmetic changes (condensed)
        if report.cosmetic_changes:
            lines.append("### 🎨 Cosmetic Changes")
            lines.append(f"_{len(report.cosmetic_changes)} minor formatting/wording updates_\n")

        lines.append("---\n")

    return "\n".join(lines)


def _format_change_entry(change: ChangeEntry) -> str:
    """Format a single change entry for markdown.

    Args:
        change: Change entry to format

    Returns:
        Formatted markdown line
    """
    # Map change types to display labels
    type_labels = {
        ChangeType.ADDED: "NEW",
        ChangeType.REMOVED: "REMOVED",
        ChangeType.MODIFIED: "MODIFIED",
        ChangeType.CONTENT_UPDATED: "UPDATED",
        ChangeType.METADATA_ONLY: "UPDATED",
    }
    type_label = type_labels.get(change.change_type, change.change_type.value.upper())
    return f"- **{type_label}** `{change.path}` — {change.details}\n"


def write_changelog(
    reports: list[DiffReport],
    output_path: Path,
    format: str = "both",
) -> None:
    """Write changelog to file(s).

    Args:
        reports: List of diff reports (newest first)
        output_path: Base output path (e.g., ./knowledge_base/CHANGELOG.md)
        format: Output format - "md", "json", or "both"
    """
    if format in ("md", "both"):
        md_content = render_changelog_markdown(reports)
        md_path = output_path.with_suffix(".md") if output_path.suffix != ".md" else output_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_content)
        logger.info(f"Wrote changelog: {md_path}")

    if format in ("json", "both"):
        import json

        json_path = output_path.with_suffix(".json")
        json_data = {"reports": [r.model_dump(mode="json") for r in reports]}
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(json_data, indent=2))
        logger.info(f"Wrote changelog: {json_path}")
