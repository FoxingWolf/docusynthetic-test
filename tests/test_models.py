"""Tests for pydantic models."""

from datetime import datetime

import pytest

from docusynthetic.models import (
    ChangelogEntry,
    DocumentContent,
    DocumentMetadata,
    KnowledgeBaseIndex,
    SeverityLevel,
    SourceType,
)


def test_document_metadata_creation() -> None:
    """Test creating DocumentMetadata."""
    metadata = DocumentMetadata(
        title="Test Document",
        source=SourceType.GITHUB_MDX,
        source_url="https://example.com/doc",
        tags=["test", "example"],
        category="Testing",
    )

    assert metadata.title == "Test Document"
    assert metadata.source == SourceType.GITHUB_MDX
    assert metadata.tags == ["test", "example"]
    assert metadata.category == "Testing"
    assert isinstance(metadata.last_updated, datetime)


def test_document_content_creation() -> None:
    """Test creating DocumentContent."""
    metadata = DocumentMetadata(
        title="Test Document",
        source=SourceType.GITHUB_MDX,
        source_url="https://example.com/doc",
    )

    content = DocumentContent(
        metadata=metadata,
        content="# Test Content",
        raw_content="---\ntitle: Test\n---\n# Test Content",
        content_hash="abc123",
    )

    assert content.metadata.title == "Test Document"
    assert content.content == "# Test Content"
    assert content.content_hash == "abc123"


def test_changelog_entry_severity() -> None:
    """Test ChangelogEntry with different severities."""
    breaking = ChangelogEntry(
        severity=SeverityLevel.BREAKING,
        title="Breaking Change",
        description="API endpoint removed",
        affected_paths=["/api/v1/users"],
    )

    important = ChangelogEntry(
        severity=SeverityLevel.IMPORTANT,
        title="Important Update",
        description="API endpoint modified",
        affected_paths=["/api/v1/posts"],
    )

    info = ChangelogEntry(
        severity=SeverityLevel.INFO,
        title="Info Update",
        description="Documentation typo fixed",
        affected_paths=["docs/intro.md"],
    )

    assert breaking.severity == SeverityLevel.BREAKING
    assert important.severity == SeverityLevel.IMPORTANT
    assert info.severity == SeverityLevel.INFO


def test_knowledge_base_index() -> None:
    """Test KnowledgeBaseIndex creation."""
    index = KnowledgeBaseIndex(
        version="0.1.0",
        total_documents=5,
        documents=[
            {"title": "Doc 1", "filename": "doc-1.md"},
            {"title": "Doc 2", "filename": "doc-2.md"},
        ],
        categories={"API": ["doc-1.md"], "Guides": ["doc-2.md"]},
    )

    assert index.version == "0.1.0"
    assert index.total_documents == 5
    assert len(index.documents) == 2
    assert "API" in index.categories
