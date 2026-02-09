"""Pydantic models for documentation structures."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Type of documentation source."""

    GITHUB_MDX = "github_mdx"
    OPENAPI_SPEC = "openapi_spec"
    LIVE_SITE = "live_site"


class SeverityLevel(str, Enum):
    """Severity level for changelog entries."""

    BREAKING = "breaking"
    IMPORTANT = "important"
    INFO = "info"


class DocumentMetadata(BaseModel):
    """Metadata for a documentation page."""

    title: str
    source: SourceType
    source_url: str
    last_updated: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class DocumentContent(BaseModel):
    """Content of a documentation page."""

    metadata: DocumentMetadata
    content: str
    raw_content: str
    content_hash: str


class APIEndpoint(BaseModel):
    """API endpoint information."""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    source: SourceType
    tags: List[str] = Field(default_factory=list)


class ChangelogEntry(BaseModel):
    """A single changelog entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    severity: SeverityLevel
    title: str
    description: str
    affected_paths: List[str] = Field(default_factory=list)
    diff: Optional[str] = None


class KnowledgeBaseIndex(BaseModel):
    """Index for the knowledge base."""

    version: str
    generated_at: datetime = Field(default_factory=datetime.now)
    total_documents: int = 0
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    endpoints: List[APIEndpoint] = Field(default_factory=list)
    categories: Dict[str, List[str]] = Field(default_factory=dict)


class BuildState(BaseModel):
    """State of a documentation build."""

    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    documents: List[DocumentContent]
    index: KnowledgeBaseIndex
    content_hashes: Dict[str, str] = Field(default_factory=dict)
