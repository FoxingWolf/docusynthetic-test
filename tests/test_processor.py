"""Tests for document processor."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from docusynthetic.models import (
    DocumentContent,
    DocumentMetadata,
    KnowledgeBaseIndex,
    SourceType,
)
from docusynthetic.processors import DocumentProcessor


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    docs = []

    # Document 1 - from GitHub
    metadata1 = DocumentMetadata(
        title="API Overview",
        source=SourceType.GITHUB_MDX,
        source_url="https://github.com/test/doc1",
        category="API",
    )
    docs.append(
        DocumentContent(
            metadata=metadata1,
            content="# API Overview\n\nThis is the API overview.",
            raw_content="---\ntitle: API Overview\n---\n# API Overview",
            content_hash="hash1",
        )
    )

    # Document 2 - from OpenAPI
    metadata2 = DocumentMetadata(
        title="GET /users",
        source=SourceType.OPENAPI_SPEC,
        source_url="https://example.com/swagger.yaml",
        category="Endpoints",
    )
    docs.append(
        DocumentContent(
            metadata=metadata2,
            content="# GET /users\n\nGet all users.",
            raw_content="get: /users",
            content_hash="hash2",
        )
    )

    return docs


def test_processor_initialization(temp_output_dir: Path) -> None:
    """Test DocumentProcessor initialization."""
    processor = DocumentProcessor(output_dir=temp_output_dir)
    assert processor.output_dir == temp_output_dir
    assert temp_output_dir.exists()


def test_merge_documents(temp_output_dir: Path, sample_documents: list) -> None:
    """Test document merging."""
    processor = DocumentProcessor(output_dir=temp_output_dir)

    # Add duplicate document (same content hash)
    duplicate = DocumentContent(
        metadata=DocumentMetadata(
            title="API Overview Copy",
            source=SourceType.LIVE_SITE,
            source_url="https://example.com/doc1",
        ),
        content="# API Overview\n\nThis is the API overview.",
        raw_content="<html>API Overview</html>",
        content_hash="hash1",  # Same hash as first doc
    )

    all_docs = sample_documents + [duplicate]
    merged = processor.merge_documents(all_docs)

    # Should have 2 unique documents (deduplicated by hash)
    assert len(merged) == 2

    # GitHub source should be preferred over Live Site
    api_overview = next(d for d in merged if d.content_hash == "hash1")
    assert api_overview.metadata.source == SourceType.GITHUB_MDX


def test_generate_index(temp_output_dir: Path, sample_documents: list) -> None:
    """Test index generation."""
    processor = DocumentProcessor(output_dir=temp_output_dir)
    index = processor.generate_index(sample_documents)

    assert index.total_documents == 2
    assert len(index.documents) == 2
    assert "API" in index.categories
    assert "Endpoints" in index.categories


def test_save_knowledge_base(temp_output_dir: Path, sample_documents: list) -> None:
    """Test saving knowledge base."""
    processor = DocumentProcessor(output_dir=temp_output_dir)
    index = processor.generate_index(sample_documents)
    processor.save_knowledge_base(sample_documents, index)

    # Check that files were created
    kb_dir = temp_output_dir / "knowledge_base"
    assert kb_dir.exists()

    index_file = temp_output_dir / "index.json"
    assert index_file.exists()

    # Check markdown files exist
    md_files = list(kb_dir.glob("*.md"))
    assert len(md_files) == 2


def test_filename_creation(temp_output_dir: Path) -> None:
    """Test safe filename creation."""
    processor = DocumentProcessor(output_dir=temp_output_dir)

    # Test with special characters
    filename = processor._create_filename("GET /api/v1/users?param=value")
    assert "/" not in filename
    assert "?" not in filename
    assert "=" not in filename

    # Test with long title
    long_title = "A" * 200
    filename = processor._create_filename(long_title)
    assert len(filename) <= 100
