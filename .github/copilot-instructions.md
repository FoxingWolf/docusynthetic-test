# Venice KB Collector - GitHub Copilot Instructions

This repository contains the **Venice KB Collector**, a Python tool that fetches, processes, and tracks changes in Venice AI API documentation.

## Architecture

- **sources/**: Fetch docs from GitHub (MDX), OpenAPI specs, live web scraping (Playwright), and API probing
- **processing/**: Convert MDX/Mintlify to Markdown, deduplicate, merge multi-source content, chunk with token limits
- **diffing/**: Core change tracking - create snapshots, diff between builds, classify severity (breaking/important/info/cosmetic)
- **output/**: Write knowledge_base/ directory, _index.json catalog, and human+machine readable changelogs
- **llm/**: Optional LLM client for smart deduplication and changelog summaries
- **utils/**: Content hashing, token counting (tiktoken), structured logging

## Key Conventions

- **Modern Python**: 3.11+ with `str | None` syntax, Pydantic v2 models, async for I/O
- **CLI**: Typer-based with subcommands: build, update, changelog, diff, validate, status
- **Change Tracking**: Snapshots store `{path: {hash, token_count, title, tags}}` per page, not full content
- **Severity Rules**: api-reference/endpoints/ → IMPORTANT, deprecations → BREAKING, models/ → INFO
- **Optional LLM**: `--skip-llm` flag must work - all LLM features gracefully degrade to hash-based logic

## MDX Conversion Rules

- `<CodeGroup>` → strip wrapper, keep code blocks
- `<Steps><Step title="X">` → `### Step N: X`
- `<Note>` → `> **Note:**`
- `<Warning>` → `> ⚠️ **Warning:**`
- `<Card title="T" href="U">` → `- **[T](U)**`
- Frontmatter → extract title as H1

## Running Locally

```bash
make setup    # Install deps + Playwright
make build    # Full KB build
make test     # Run pytest
make lint     # Run ruff + black
```

## GitHub Codespace Ready

Open in Codespaces → auto-installs Python 3.12, Playwright, all deps → `make build` works immediately.
