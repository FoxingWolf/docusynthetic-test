"""Shared test fixtures and configuration."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_mdx(fixtures_dir: Path) -> str:
    """Load sample MDX content."""
    mdx_file = fixtures_dir / "sample_chat_completions.mdx"
    if mdx_file.exists():
        return mdx_file.read_text()
    return """---
title: Chat Completions
description: Generate chat completions
---

# Chat Completions

<Note>This is a sample MDX file for testing.</Note>

Generate chat completions using the Venice API.

<CodeGroup>
```python Python
import openai
client = openai.OpenAI(base_url="https://api.venice.ai/api/v1")
```

```javascript JavaScript
const openai = require('openai');
const client = new openai.OpenAI({baseURL: 'https://api.venice.ai/api/v1'});
```
</CodeGroup>
"""


@pytest.fixture
def sample_swagger_snippet() -> dict:
    """Sample OpenAPI spec snippet."""
    return {
        "openapi": "3.0.0",
        "paths": {
            "/chat/completions": {
                "post": {
                    "summary": "Create chat completion",
                    "description": "Generate a chat completion",
                    "parameters": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "model": {"type": "string"},
                                        "messages": {"type": "array"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                        }
                    },
                }
            }
        },
    }


@pytest.fixture
def sample_html() -> str:
    """Sample HTML content."""
    return """
    <html>
    <body>
        <main>
            <h1>Models Overview</h1>
            <p>Venice AI supports multiple model types.</p>
            <ul>
                <li>Text models</li>
                <li>Image models</li>
            </ul>
        </main>
    </body>
    </html>
    """
