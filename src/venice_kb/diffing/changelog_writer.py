"""Write changelog from diff reports."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from venice_kb.diffing.models import ChangeType, DiffReport, SeverityLevel

logger = logging.getLogger(__name__)


class ChangelogWriter:
    """Write changelog from diff reports."""

    def __init__(self, changelog_path: Path | None = None):
        self.changelog_path = changelog_path or Path("knowledge_base/CHANGELOG.md")
        self.changelog_json_path = changelog_path.with_suffix(".json") if changelog_path else Path(
            "knowledge_base/CHANGELOG.json"
        )

    def write_changelog(
        self, reports: list[DiffReport], git_commit: str | None = None
    ) -> None:
        """
        Write changelog from list of diff reports.

        Args:
            reports: List of DiffReport objects (newest first)
            git_commit: Git commit SHA of sources
        """
        # Ensure parent directory exists
        self.changelog_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown changelog
        markdown = self._generate_markdown(reports, git_commit)
        self.changelog_path.write_text(markdown)
        logger.info(f"Wrote changelog to {self.changelog_path}")

        # Write JSON changelog
        json_data = [report.model_dump(mode="json") for report in reports]
        self.changelog_json_path.write_text(json.dumps(json_data, indent=2, default=str))
        logger.info(f"Wrote JSON changelog to {self.changelog_json_path}")

    def _generate_markdown(
        self, reports: list[DiffReport], git_commit: str | None = None
    ) -> str:
        """Generate markdown changelog content."""
        lines = ["# Venice AI Documentation Changelog\n"]
        lines.append(
            "This changelog tracks changes to the Venice AI API documentation knowledge base.\n"
        )

        for report in reports:
            lines.append(self._format_report(report, git_commit))

        return "\n".join(lines)

    def _format_report(self, report: DiffReport, git_commit: str | None = None) -> str:
        """Format a single diff report."""
        lines = []

        # Header
        build_date = report.new_snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"\n## Build {build_date}\n")

        # Summary if available
        if report.summary:
            lines.append(f"**Summary:** {report.summary}\n")

        # Stats
        stats = report.stats
        lines.append(
            f"**Changes:** {stats['added']} added, {stats['modified']} modified, "
            f"{stats['removed']} removed\n"
        )

        if git_commit:
            lines.append(f"**Source commit:** `{git_commit[:8]}`\n")

        # Group changes by severity
        breaking = [c for c in report.changes if c.severity == SeverityLevel.BREAKING]
        important = [c for c in report.changes if c.severity == SeverityLevel.IMPORTANT]
        informational = [
            c for c in report.changes if c.severity == SeverityLevel.INFORMATIONAL
        ]
        cosmetic = [c for c in report.changes if c.severity == SeverityLevel.COSMETIC]

        # Breaking changes
        if breaking:
            lines.append("\n### 🚨 Breaking Changes\n")
            for change in breaking:
                lines.append(self._format_change(change))

        # Important changes
        if important:
            lines.append("\n### ⚠️ Important Changes\n")
            for change in important:
                lines.append(self._format_change(change))

        # Informational changes
        if informational:
            lines.append("\n### ℹ️ Informational Changes\n")
            for change in informational:
                lines.append(self._format_change(change))

        # Cosmetic changes
        if cosmetic:
            lines.append("\n### 🎨 Cosmetic Changes\n")
            for change in cosmetic:
                lines.append(self._format_change(change))

        return "\n".join(lines)

    def _format_change(self, change: ChangeType) -> str:
        """Format a single change entry."""
        # Badge for change type
        badge = {
            ChangeType.ADDED: "🆕 NEW",
            ChangeType.MODIFIED: "📝 MODIFIED",
            ChangeType.REMOVED: "🗑️ REMOVED",
        }.get(change.change_type, "")

        line = f"- **{badge}** `{change.path}` — {change.description}"

        # Add diff preview for modifications
        if change.change_type == ChangeType.MODIFIED and change.diff_preview:
            # Indent the preview
            preview_lines = change.diff_preview.split("\n")
            preview = "\n  ".join(preview_lines)
            line += f"\n  ```\n  {preview}\n  ```"

        return line + "\n"

    def append_to_existing(self, new_report: DiffReport, git_commit: str | None = None) -> None:
        """
        Append a new report to existing changelog.

        Args:
            new_report: New diff report to append
            git_commit: Git commit SHA
        """
        existing_reports = []

        # Load existing JSON if available
        if self.changelog_json_path.exists():
            try:
                data = json.loads(self.changelog_json_path.read_text())
                existing_reports = [DiffReport(**report) for report in data]
            except Exception as e:
                logger.warning(f"Failed to load existing changelog: {e}")

        # Prepend new report (newest first)
        all_reports = [new_report] + existing_reports

        # Write updated changelog
        self.write_changelog(all_reports, git_commit)
