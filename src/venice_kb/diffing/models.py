"""Pydantic models for snapshots and change tracking."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of change detected."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    CONTENT_UPDATED = "content_updated"
    METADATA_ONLY = "metadata_only"


class SeverityLevel(str, Enum):
    """Severity level of a change."""

    BREAKING = "breaking"  # Endpoint removed, schema changed incompatibly
    IMPORTANT = "important"  # New endpoint, new required param, deprecation
    INFORMATIONAL = "info"  # Prose update, typo fix, model list refresh
    COSMETIC = "cosmetic"  # Formatting, nav reorder


class ChangeEntry(BaseModel):
    """A single change detected between snapshots."""

    change_type: ChangeType
    severity: SeverityLevel
    path: str = Field(..., description="e.g. 'api-reference/endpoints/chat-completions.md'")
    section: str = Field(..., description="e.g. 'API Reference > Chat > Completions'")
    title: str = Field(..., description="Human-readable summary")
    details: str = Field(..., description="Full description of what changed")
    old_hash: str | None = None
    new_hash: str | None = None
    old_token_count: int | None = None
    new_token_count: int | None = None
    diff_preview: str | None = Field(None, description="First ~500 chars of unified diff")


class DiffReport(BaseModel):
    """Complete diff report between two snapshots."""

    generated_at: datetime
    previous_snapshot: str = Field(..., description="Timestamp or ID of previous build")
    current_snapshot: str
    summary: str = Field(..., description="LLM-generated executive summary")
    stats: dict = Field(..., description="{added: N, modified: N, removed: N, unchanged: N}")
    breaking_changes: list[ChangeEntry] = Field(default_factory=list)
    important_changes: list[ChangeEntry] = Field(default_factory=list)
    informational_changes: list[ChangeEntry] = Field(default_factory=list)
    cosmetic_changes: list[ChangeEntry] = Field(default_factory=list)

    def get_all_changes(self) -> list[ChangeEntry]:
        """Get all changes sorted by severity."""
        return (
            self.breaking_changes
            + self.important_changes
            + self.informational_changes
            + self.cosmetic_changes
        )


class PageMetadata(BaseModel):
    """Metadata for a single page in the knowledge base."""

    hash: str
    token_count: int
    title: str
    tags: list[str] = Field(default_factory=list)


class KBSnapshot(BaseModel):
    """Snapshot of a knowledge base build."""

    snapshot_id: str = Field(..., description="ISO timestamp or UUID")
    generated_at: datetime
    source_versions: dict = Field(
        ..., description="{github_commit, openapi_hash, scrape_timestamp}"
    )
    page_manifest: dict[str, PageMetadata] = Field(..., description="{path: PageMetadata}")

    def get_page_paths(self) -> set[str]:
        """Get all page paths in this snapshot."""
        return set(self.page_manifest.keys())
