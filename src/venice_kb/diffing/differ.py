"""Generate diffs between knowledge base snapshots."""

import difflib
import logging
from typing import Any

from venice_kb.diffing.models import (
    ChangeEntry,
    ChangeType,
    DiffReport,
    KBSnapshot,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class Differ:
    """Generate diffs between snapshots."""

    def __init__(self):
        self.severity_signals = {
            "breaking": [
                "removed",
                "deprecated",
                "no longer",
                "breaking change",
                "required parameter",
                "endpoint removed",
                "incompatible",
            ],
            "important": [
                "pricing",
                "cost",
                "endpoint",
                "authentication",
                "authorization",
                "security",
            ],
        }

    def diff_snapshots(self, old: KBSnapshot, new: KBSnapshot) -> DiffReport:
        """
        Generate diff report between two snapshots.

        Args:
            old: Old snapshot
            new: New snapshot

        Returns:
            DiffReport with all changes
        """
        changes: list[ChangeEntry] = []

        old_paths = set(old.pages.keys())
        new_paths = set(new.pages.keys())

        # Added pages
        for path in new_paths - old_paths:
            page_info = new.pages[path]
            changes.append(
                ChangeEntry(
                    change_type=ChangeType.ADDED,
                    severity=SeverityLevel.INFORMATIONAL,
                    path=path,
                    title=page_info.title,
                    description=f"New page: {page_info.title}",
                    new_hash=page_info.content_hash,
                )
            )

        # Removed pages
        for path in old_paths - new_paths:
            page_info = old.pages[path]
            changes.append(
                ChangeEntry(
                    change_type=ChangeType.REMOVED,
                    severity=self._classify_removal_severity(path),
                    path=path,
                    title=page_info.title,
                    description=f"Removed page: {page_info.title}",
                    old_hash=page_info.content_hash,
                )
            )

        # Modified pages
        for path in old_paths & new_paths:
            old_page = old.pages[path]
            new_page = new.pages[path]

            if old_page.content_hash == new_page.content_hash:
                # Unchanged - skip
                continue

            # Generate diff preview
            diff_preview = self._generate_diff_preview(old_page, new_page)

            # Classify severity
            severity = self._classify_modification_severity(path, diff_preview, old_page, new_page)

            changes.append(
                ChangeEntry(
                    change_type=ChangeType.MODIFIED,
                    severity=severity,
                    path=path,
                    title=new_page.title,
                    description=f"Modified: {new_page.title}",
                    diff_preview=diff_preview,
                    old_hash=old_page.content_hash,
                    new_hash=new_page.content_hash,
                )
            )

        # Calculate stats
        stats = {
            "total_changes": len(changes),
            "added": sum(1 for c in changes if c.change_type == ChangeType.ADDED),
            "removed": sum(1 for c in changes if c.change_type == ChangeType.REMOVED),
            "modified": sum(1 for c in changes if c.change_type == ChangeType.MODIFIED),
            "breaking": sum(1 for c in changes if c.severity == SeverityLevel.BREAKING),
            "important": sum(1 for c in changes if c.severity == SeverityLevel.IMPORTANT),
        }

        report = DiffReport(
            old_snapshot_time=old.timestamp,
            new_snapshot_time=new.timestamp,
            changes=changes,
            stats=stats,
        )

        logger.info(
            f"Generated diff: {stats['added']} added, {stats['modified']} modified, "
            f"{stats['removed']} removed"
        )

        return report

    def _generate_diff_preview(self, old_page: Any, new_page: Any) -> str:
        """Generate a preview of the diff (first 500 chars)."""
        # For now, we don't have the actual content, just metadata
        # In a real implementation, you'd load the content and generate unified diff
        preview = (
            f"Token count: {old_page.token_count} → {new_page.token_count}\n"
            f"Hash: {old_page.content_hash[:8]}...{old_page.content_hash[-8:]} → "
            f"{new_page.content_hash[:8]}...{new_page.content_hash[-8:]}"
        )
        return preview[:500]

    def _classify_removal_severity(self, path: str) -> SeverityLevel:
        """Classify severity of a page removal."""
        # API endpoint removals are breaking
        if "api-reference" in path or "endpoint" in path:
            return SeverityLevel.BREAKING

        # Deprecation page removals are important
        if "deprecat" in path.lower():
            return SeverityLevel.IMPORTANT

        # Everything else is informational
        return SeverityLevel.INFORMATIONAL

    def _classify_modification_severity(
        self, path: str, diff_preview: str, old_page: Any, new_page: Any
    ) -> SeverityLevel:
        """Classify severity of a page modification."""
        diff_lower = diff_preview.lower()

        # Check for breaking change signals
        for signal in self.severity_signals["breaking"]:
            if signal in diff_lower:
                return SeverityLevel.BREAKING

        # Check for important signals
        for signal in self.severity_signals["important"]:
            if signal in diff_lower or signal in path.lower():
                return SeverityLevel.IMPORTANT

        # Check token count change percentage
        if old_page.token_count > 0:
            change_pct = abs(new_page.token_count - old_page.token_count) / old_page.token_count
            if change_pct < 0.05:
                # Less than 5% change - cosmetic
                return SeverityLevel.COSMETIC

        # Default to informational
        return SeverityLevel.INFORMATIONAL
