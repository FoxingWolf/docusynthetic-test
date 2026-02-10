"""Data models for diffing and changelog generation."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of change detected."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


class SeverityLevel(str, Enum):
    """Severity level of a change."""

    BREAKING = "breaking"
    IMPORTANT = "important"
    INFORMATIONAL = "informational"
    COSMETIC = "cosmetic"


class PageInfo(BaseModel):
    """Information about a single page."""

    path: str
    content_hash: str
    token_count: int
    title: str
    tags: list[str] = Field(default_factory=list)


class KBSnapshot(BaseModel):
    """Snapshot of knowledge base at a point in time."""

    timestamp: datetime
    pages: dict[str, PageInfo]
    git_commit: str | None = None
    swagger_hash: str | None = None


class ChangeEntry(BaseModel):
    """Single change entry."""

    change_type: ChangeType
    severity: SeverityLevel
    path: str
    title: str
    description: str
    diff_preview: str | None = None
    old_hash: str | None = None
    new_hash: str | None = None


class DiffReport(BaseModel):
    """Report of changes between two snapshots."""

    old_snapshot_time: datetime
    new_snapshot_time: datetime
    changes: list[ChangeEntry]
    stats: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
