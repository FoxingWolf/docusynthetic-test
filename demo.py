"""Demo script to test DocuSynthetic functionality without live API calls."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from docusynthetic.models import DocumentContent, DocumentMetadata, SourceType
from docusynthetic.processors import DocumentProcessor


async def demo() -> None:
    """Run a demo of DocuSynthetic functionality."""
    print("🚀 DocuSynthetic Demo\n")

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "demo_output"
        print(f"📁 Output directory: {output_dir}\n")

        # Create sample documents
        documents = []

        # Document 1: API Overview
        metadata1 = DocumentMetadata(
            title="Venice AI API Overview",
            source=SourceType.GITHUB_MDX,
            source_url="https://github.com/veniceai/api-docs/blob/main/overview.md",
            tags=["api", "overview"],
            category="Getting Started",
        )
        doc1 = DocumentContent(
            metadata=metadata1,
            content="""# Venice AI API Overview

Welcome to the Venice AI API documentation!

## Introduction

The Venice AI API provides powerful AI capabilities for your applications.

## Key Features

- Text generation
- Image generation
- Audio processing
- Model fine-tuning

## Authentication

All API requests require authentication using an API key.
""",
            raw_content="---\ntitle: Venice AI API Overview\n---\n# Venice AI API Overview...",
            content_hash="overview_hash_123",
        )
        documents.append(doc1)

        # Document 2: Authentication Guide
        metadata2 = DocumentMetadata(
            title="Authentication Guide",
            source=SourceType.GITHUB_MDX,
            source_url="https://github.com/veniceai/api-docs/blob/main/auth.md",
            tags=["authentication", "security"],
            category="Guides",
        )
        doc2 = DocumentContent(
            metadata=metadata2,
            content="""# Authentication Guide

## API Keys

To use the Venice AI API, you need an API key.

## Getting Your API Key

1. Sign up at https://venice.ai
2. Navigate to your account settings
3. Generate a new API key

## Using Your API Key

Include your API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```
""",
            raw_content="---\ntitle: Authentication Guide\n---\n# Authentication Guide...",
            content_hash="auth_hash_456",
        )
        documents.append(doc2)

        # Document 3: Text Generation Endpoint
        metadata3 = DocumentMetadata(
            title="POST /v1/completions",
            source=SourceType.OPENAPI_SPEC,
            source_url="https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml",
            tags=["endpoint", "text-generation"],
            category="API Endpoints",
        )
        doc3 = DocumentContent(
            metadata=metadata3,
            content="""# POST /v1/completions

## Summary

Generate text completions using AI models.

## Description

This endpoint accepts a prompt and returns AI-generated text completions.

## Parameters

- **model** (body) - Required: The ID of the model to use
- **prompt** (body) - Required: The prompt to generate completions for
- **max_tokens** (body): Maximum number of tokens to generate
- **temperature** (body): Sampling temperature (0-2)

## Responses

### 200

Successful response with generated completion
""",
            raw_content="paths:\n  /v1/completions:\n    post: ...",
            content_hash="completions_hash_789",
        )
        documents.append(doc3)

        # Document 4: Error Handling (from live site)
        metadata4 = DocumentMetadata(
            title="Error Handling",
            source=SourceType.LIVE_SITE,
            source_url="https://docs.venice.ai/error-handling",
            tags=["errors", "troubleshooting"],
            category="Guides",
        )
        doc4 = DocumentContent(
            metadata=metadata4,
            content="""# Error Handling

## Common Error Codes

- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Invalid or missing API key
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Best Practices

Always implement retry logic with exponential backoff.
""",
            raw_content="<html><h1>Error Handling</h1>...</html>",
            content_hash="errors_hash_abc",
        )
        documents.append(doc4)

        # Process documents
        processor = DocumentProcessor(output_dir=output_dir)

        print("📝 Processing documents...")
        merged_docs = processor.merge_documents(documents)
        print(f"   ✓ Merged to {len(merged_docs)} unique documents\n")

        print("📊 Generating index...")
        index = processor.generate_index(merged_docs)
        print(f"   ✓ Generated index with {len(index.categories)} categories\n")

        print("🔍 Detecting changes...")
        previous_state = processor.load_previous_state()
        changes = processor.detect_changes(previous_state, merged_docs)
        print(f"   ✓ Detected {len(changes)} changes\n")

        print("💾 Saving knowledge base...")
        processor.save_knowledge_base(merged_docs, index)
        processor.save_changelog(changes)
        processor.save_state(merged_docs, index)
        print(f"   ✓ Knowledge base saved to {output_dir}\n")

        # Display results
        print("📦 Output Structure:")
        for item in sorted(output_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(output_dir)
                size = item.stat().st_size
                print(f"   {rel_path} ({size} bytes)")

        print("\n📋 Categories:")
        for category, docs in index.categories.items():
            print(f"   {category}: {len(docs)} documents")

        print("\n📄 Sample Document (venice-ai-api-overview.md):")
        sample_doc = output_dir / "knowledge_base" / "venice-ai-api-overview.md"
        if sample_doc.exists():
            content = sample_doc.read_text()
            lines = content.split("\n")
            print("   " + "\n   ".join(lines[:15]))
            if len(lines) > 15:
                print("   ...")

        print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo())
