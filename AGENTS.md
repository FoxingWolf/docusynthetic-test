# Venice AI API Docs → Knowledge Base Collector

## Mission
Create a **complete GitHub repository** for a Python tool that pulls Venice AI API documentation from multiple sources (GitHub repo, live docs site, OpenAPI spec), collates/deduplicates it into a structured knowledge base, and — critically — **tracks changes between runs** so downstream agents and humans can see what's new, modified, or removed since the last build.

The repo must be fully **GitHub Codespace-ready** (one-click open, zero manual setup) and runnable locally in any JetBrains IDE or terminal.

---

## Repository Structure to Create

```
venice-kb-collector/
├── .devcontainer/
│   └── devcontainer.json              # Codespace config — full Python + Playwright + deps
├── .github/
│   ├── workflows/
│   │   ├── build-kb.yml               # Scheduled + manual workflow to rebuild KB
│   │   └── ci.yml                     # Lint + test on PR
│   ├── copilot-instructions.md        # Repo-level Copilot context
│   └── CODEOWNERS
├── src/
│   └── venice_kb/
│       ├── __init__.py
│       ├── __main__.py                # `python -m venice_kb` entry point
│       ├── cli.py                     # Click/Typer CLI with subcommands
│       ├── config.py                  # All configuration, env vars, defaults
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── github_fetcher.py      # Fetch raw MDX from veniceai/api-docs
│       │   ├── openapi_parser.py      # Parse swagger.yaml → structured endpoint docs
│       │   ├── web_scraper.py         # Playwright-based scraping for JS-rendered pages
│       │   ├── manifest_loader.py     # Parse llms.txt + docs.json
│       │   └── api_prober.py          # Hit Venice API /models endpoint for live data
│       ├── processing/
│       │   ├── __init__.py
│       │   ├── mdx_converter.py       # MDX/Mintlify → clean Markdown
│       │   ├── html_converter.py      # Scraped HTML → clean Markdown
│       │   ├── deduplicator.py        # Hash + LLM-assisted dedup
│       │   ├── merger.py              # Multi-source merge per topic
│       │   └── chunker.py             # Semantic chunking with token limits
│       ├── diffing/
│       │   ├── __init__.py
│       │   ├── snapshot.py            # Create/load KB snapshots for comparison
│       │   ├── differ.py              # Diff two KB snapshots → change report
│       │   ├── changelog_writer.py    # Generate human+agent readable changelog
│       │   └── models.py              # Pydantic models for ChangeEntry, DiffReport, etc.
│       ├── output/
│       │   ├── __init__.py
│       │   ├── kb_writer.py           # Write the knowledge_base/ directory tree
│       │   ├── index_writer.py        # Write _index.json master catalog
│       │   └── changelog_renderer.py  # Render changelog as .md + .json
│       ├── llm/
│       │   ├── __init__.py
│       │   └── client.py              # OpenAI-compatible client (works with Venice API)
│       └── utils/
│           ├── __init__.py
│           ├── hashing.py             # Content fingerprinting
│           ├── tokens.py              # Token counting
│           └── logging.py             # Structured logging setup
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures, cached test data
│   ├── fixtures/                      # Cached sample MDX, HTML, YAML for offline tests
│   │   ├── sample_chat_completions.mdx
│   │   ├── sample_swagger_snippet.yaml
│   │   ├── sample_rendered_models.html
│   │   └── sample_llms.txt
│   ├── test_mdx_converter.py
│   ├── test_openapi_parser.py
│   ├── test_html_converter.py
│   ├── test_deduplicator.py
│   ├── test_differ.py
│   ├── test_changelog_writer.py
│   └── test_cli.py
├── knowledge_base/                    # Gitignored output dir (or committed if desired)
│   └── .gitkeep
├── .cache/                            # Gitignored local cache for fetched content
│   └── .gitkeep
├── snapshots/                         # Gitignored (or committed) historical KB snapshots
│   └── .gitkeep
├── pyproject.toml                     # Modern Python packaging (PEP 621)
├── requirements.txt                   # Pinned production deps
├── requirements-dev.txt               # Dev/test deps
├── .env.example                       # Template for required env vars
├── .gitignore
├── .python-version                    # 3.12
├── LICENSE                            # MIT
├── README.md                          # Full usage docs
├── CHANGELOG_TEMPLATE.md              # Template for generated changelogs
└── Makefile                           # Convenience targets: make build, make test, etc.
```

---

## Devcontainer Configuration (Codespace-Ready)

Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "Venice KB Collector",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/node:2": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.pylint",
        "ms-playwright.playwright",
        "redhat.vscode-yaml",
        "tamasfe.even-better-toml"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.formatting.provider": "black",
        "editor.formatOnSave": true
      }
    },
    "jetbrains": {
      "plugins": ["PythonCore", "org.toml.lang"]
    }
  },
  "forwardPorts": [],
  "postCreateCommand": "pip install -e '.[dev]' && playwright install chromium --with-deps",
  "remoteEnv": {
    "VENICE_API_KEY": "${localEnv:VENICE_API_KEY}",
    "LLM_BASE_URL": "${localEnv:LLM_BASE_URL:https://api.venice.ai/api/v1}",
    "LLM_MODEL": "${localEnv:LLM_MODEL:venice-uncensored}"
  }
}
```

---

## GitHub Actions Workflows

### `.github/workflows/build-kb.yml` — Scheduled KB Builder
```yaml
name: Build Knowledge Base
on:
  schedule:
    - cron: '0 6 * * 1'       # Weekly Monday 6am UTC
  workflow_dispatch:            # Manual trigger
    inputs:
      force_refresh:
        description: 'Bypass cache and re-fetch all sources'
        type: boolean
        default: false

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e '.[dev]'
          playwright install chromium --with-deps

      - name: Restore previous snapshot
        uses: actions/cache@v4
        with:
          path: snapshots/
          key: kb-snapshot-${{ github.run_number }}
          restore-keys: kb-snapshot-

      - name: Build Knowledge Base
        env:
          VENICE_API_KEY: ${{ secrets.VENICE_API_KEY }}
          LLM_BASE_URL: ${{ secrets.LLM_BASE_URL }}
          LLM_MODEL: ${{ secrets.LLM_MODEL }}
        run: |
          python -m venice_kb build \
            --output ./knowledge_base \
            --snapshot-dir ./snapshots \
            ${{ github.event.inputs.force_refresh == 'true' && '--force-refresh' || '' }}

      - name: Generate Changelog
        run: |
          python -m venice_kb changelog \
            --snapshot-dir ./snapshots \
            --output ./knowledge_base/CHANGELOG.md

      - name: Upload KB artifact
        uses: actions/upload-artifact@v4
        with:
          name: venice-knowledge-base-${{ github.run_number }}
          path: knowledge_base/

      - name: Commit updated KB (if on main)
        if: github.ref == 'refs/heads/main'
        run: |
          git config user.name "venice-kb-bot"
          git config user.email "bot@users.noreply.github.com"
          git add knowledge_base/ snapshots/
          git diff --cached --quiet || git commit -m "chore: rebuild KB $(date -u +%Y-%m-%d)"
          git push
```

### `.github/workflows/ci.yml` — CI on PR
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e '.[dev]'
      - run: python -m pytest tests/ -v --tb=short
      - run: python -m ruff check src/
      - run: python -m black --check src/ tests/
```

---

## The Change Tracking / Diffing System (Core Feature)

This is the "what's new or changed that may need attention in production" layer.

### Snapshot Model (`src/venice_kb/diffing/models.py`)
```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    CONTENT_UPDATED = "content_updated"
    METADATA_ONLY = "metadata_only"

class SeverityLevel(str, Enum):
    BREAKING = "breaking"        # Endpoint removed, schema changed incompatibly
    IMPORTANT = "important"      # New endpoint, new required param, deprecation
    INFORMATIONAL = "info"       # Prose update, typo fix, model list refresh
    COSMETIC = "cosmetic"        # Formatting, nav reorder

class ChangeEntry(BaseModel):
    change_type: ChangeType
    severity: SeverityLevel
    path: str                    # e.g. "api-reference/endpoints/chat-completions.md"
    section: str                 # e.g. "API Reference > Chat > Completions"
    title: str                   # Human-readable summary
    details: str                 # Full description of what changed
    old_hash: str | None = None
    new_hash: str | None = None
    old_token_count: int | None = None
    new_token_count: int | None = None
    diff_preview: str | None = None  # First ~500 chars of unified diff

class DiffReport(BaseModel):
    generated_at: datetime
    previous_snapshot: str       # Timestamp or ID of previous build
    current_snapshot: str
    summary: str                 # LLM-generated executive summary
    stats: dict                  # {added: N, modified: N, removed: N, unchanged: N}
    breaking_changes: list[ChangeEntry]
    important_changes: list[ChangeEntry]
    informational_changes: list[ChangeEntry]
    cosmetic_changes: list[ChangeEntry]

class KBSnapshot(BaseModel):
    snapshot_id: str             # ISO timestamp or UUID
    generated_at: datetime
    source_versions: dict        # {github_commit, openapi_hash, scrape_timestamp}
    page_manifest: dict[str, dict]  # {path: {hash, token_count, title, tags}}
```

### How Diffing Works (`src/venice_kb/diffing/differ.py`)

```
Previous Snapshot (snapshots/2026-02-02T06:00:00.json)
   ↕ compare page_manifest entries
Current Build (just completed)
   ↓
For each page path:
  - In previous but NOT in current → REMOVED
  - In current but NOT in previous → ADDED
  - In both, same hash → UNCHANGED (skip)
  - In both, different hash → MODIFIED
     ↓
     For MODIFIED pages:
       - Load both versions' content
       - Generate unified diff (difflib)
       - Classify severity:
         * If path contains "endpoint/" → check for schema changes → could be BREAKING
         * If page is new model or deprecation notice → IMPORTANT
         * If only token count changed < 5% → likely COSMETIC
         * Otherwise → INFORMATIONAL
       - (Optional) LLM call: "Summarize what changed between these two versions
         of the '{title}' documentation page. Focus on API-breaking changes,
         new parameters, removed features, or behavior changes."
```

### Change Severity Classification Rules
```python
SEVERITY_RULES = {
    # Path patterns → default severity for MODIFIED pages
    "api-reference/endpoints/": SeverityLevel.IMPORTANT,
    "api-reference/error-codes": SeverityLevel.IMPORTANT,
    "api-reference/rate-limiting": SeverityLevel.IMPORTANT,
    "overview/deprecations": SeverityLevel.BREAKING,
    "overview/beta-models": SeverityLevel.INFORMATIONAL,
    "overview/pricing": SeverityLevel.IMPORTANT,
    "models/": SeverityLevel.INFORMATIONAL,
    "guides/": SeverityLevel.INFORMATIONAL,
    "overview/privacy": SeverityLevel.INFORMATIONAL,
}

# Upgrade to BREAKING if any of these patterns found in the diff:
BREAKING_SIGNALS = [
    "removed", "deprecated", "no longer", "breaking",
    "required parameter", "schema change", "endpoint removed",
    "status code changed", "authentication changed",
]
```

### Changelog Output Format (`knowledge_base/CHANGELOG.md`)

The changelog renderer should produce something like:

```markdown
# Venice API Docs Knowledge Base — Changelog

## 2026-02-09 (Latest Build)
> Compared against: 2026-02-02 build | Sources: GitHub commit `abc1234`, OpenAPI hash `def5678`

### 🚨 Breaking Changes
_None detected_

### ⚠️ Important Changes
- **NEW** `api-reference/endpoints/audio-transcriptions.md` — New Audio Transcriptions
  endpoint added (POST /audio/transcriptions). Supports Whisper-compatible speech-to-text.
- **MODIFIED** `api-reference/endpoints/chat-completions.md` — New optional parameter
  `venice_parameters.enable_web_search` added to chat completions. Not breaking (optional).
- **MODIFIED** `overview/pricing.md` — Price decrease for `qwen3-235b` model
  (input: $0.50→$0.30, output: $2.00→$1.50).

### ℹ️ Informational Changes
- **MODIFIED** `models/text.md` — Two new text models added to catalog: `grok-code-fast-1`,
  `venetian-1`.
- **MODIFIED** `guides/crewai.md` — Updated code examples to use CrewAI v0.90 syntax.

### 🎨 Cosmetic Changes
- **MODIFIED** `overview/about-venice.md` — Minor wording update in OpenAI compatibility section.

---

## 2026-02-02
> Compared against: 2026-01-26 build | ...
```

### Machine-Readable Changelog (`knowledge_base/CHANGELOG.json`)

Also output `CHANGELOG.json` with the full `DiffReport` serialized, so downstream agents can programmatically filter changes:

```json
{
  "reports": [
    {
      "generated_at": "2026-02-09T06:00:00Z",
      "previous_snapshot": "2026-02-02T06:00:00Z",
      "current_snapshot": "2026-02-09T06:00:00Z",
      "summary": "1 new endpoint (audio transcriptions), 1 new chat parameter, 2 new models, price changes for qwen3-235b.",
      "stats": {"added": 1, "modified": 4, "removed": 0, "unchanged": 38},
      "breaking_changes": [],
      "important_changes": [
        {
          "change_type": "added",
          "severity": "important",
          "path": "api-reference/endpoints/audio-transcriptions.md",
          "section": "API Reference > Audio > Transcriptions",
          "title": "New Audio Transcriptions endpoint",
          "details": "POST /audio/transcriptions added. Whisper-compatible speech-to-text...",
          "diff_preview": null
        }
      ],
      "informational_changes": [],
      "cosmetic_changes": []
    }
  ]
}
```

---

## CLI Subcommands (Full Spec)

Implement with `typer` (preferred for JetBrains autocomplete) or `click`:

```
venice-kb build       Build the full knowledge base from all sources
  --output PATH         Output directory (default: ./knowledge_base)
  --snapshot-dir PATH   Where to store/load snapshots (default: ./snapshots)
  --sources TEXT         Comma-separated: github,openapi,web,api (default: all)
  --force-refresh       Bypass cache, re-fetch everything
  --skip-llm            Skip LLM-assisted processing (faster, less smart)
  --no-changelog        Skip changelog generation

venice-kb update      Incremental update — only fetch & process changed content
  --output PATH
  --snapshot-dir PATH

venice-kb changelog   Generate changelog from snapshots without rebuilding
  --snapshot-dir PATH
  --output PATH         Where to write CHANGELOG.md + CHANGELOG.json
  --last-n INT          Compare last N builds (default: 5)
  --format TEXT         md, json, or both (default: both)
  --severity TEXT       Filter: breaking, important, info, cosmetic, all (default: all)

venice-kb diff        Compare two specific snapshots
  --old PATH            Path to old snapshot .json
  --new PATH            Path to new snapshot .json
  --output PATH         Where to write diff report

venice-kb validate    Validate an existing knowledge base
  --kb-path PATH        Path to knowledge_base/ directory
  (checks: all index entries exist, no orphan files, hashes match, token counts valid)

venice-kb status      Show current state — last build time, source versions, page count
  --kb-path PATH
  --snapshot-dir PATH
```

---

## Configuration & Environment

### `.env.example`
```bash
# Required for LLM-assisted features (dedup, changelog summaries)
# Can use Venice itself, OpenAI, or any compatible endpoint
VENICE_API_KEY=your-venice-api-key
LLM_BASE_URL=https://api.venice.ai/api/v1
LLM_MODEL=venice-uncensored

# Optional: GitHub token for higher rate limits on API fetches
GITHUB_TOKEN=ghp_...

# Optional: Override defaults
KB_OUTPUT_DIR=./knowledge_base
SNAPSHOT_DIR=./snapshots
CACHE_DIR=./.cache
CHUNK_TARGET_TOKENS=2000
CHUNK_MAX_TOKENS=3500
LOG_LEVEL=INFO
```

### `config.py` Key Constants
```python
# Venice API Doc Sources
GITHUB_REPO = "veniceai/api-docs"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/veniceai/api-docs/main"
OPENAPI_URL = f"{GITHUB_RAW_BASE}/swagger.yaml"
LLMS_TXT_URL = f"{GITHUB_RAW_BASE}/llms.txt"
DOCS_JSON_URL = f"{GITHUB_RAW_BASE}/docs.json"
LIVE_DOCS_BASE = "https://docs.venice.ai"
VENICE_API_BASE = "https://api.venice.ai/api/v1"

# Pages with JS-rendered dynamic content that need Playwright
DYNAMIC_PAGES = [
    "/models/overview", "/models/text", "/models/image",
    "/models/audio", "/models/video", "/models/embeddings",
    "/overview/pricing", "/overview/beta-models",
]

# All known MDX content pages (derived from docs.json navigation)
# The build process should also dynamically discover these from docs.json
KNOWN_MDX_PAGES = [
    "overview/about-venice", "overview/getting-started", "overview/privacy",
    "overview/pricing", "overview/deprecations", "overview/beta-models",
    "overview/guides/generating-api-key", "overview/guides/generating-api-key-agent",
    "overview/guides/ai-agents", "overview/guides/postman",
    "overview/guides/integrations", "overview/guides/structured-responses",
    "overview/guides/reasoning-models", "overview/guides/prompt-caching",
    "overview/guides/claude-code", "overview/guides/openclaw-bot",
    "overview/guides/openai-migration", "overview/guides/langchain",
    "overview/guides/vercel-ai-sdk", "overview/guides/crewai",
    "models/overview", "models/text", "models/image",
    "models/audio", "models/video", "models/embeddings",
    "api-reference/api-spec", "api-reference/rate-limiting", "api-reference/error-codes",
    "api-reference/endpoint/chat/completions",
    "api-reference/endpoint/chat/model_feature_suffix",
    "api-reference/endpoint/image/generate",
    "api-reference/endpoint/image/upscale",
    "api-reference/endpoint/image/edit",
    "api-reference/endpoint/image/multi-edit",
    "api-reference/endpoint/image/background-remove",
    "api-reference/endpoint/image/styles",
    "api-reference/endpoint/image/generations",
    "api-reference/endpoint/audio/speech",
    "api-reference/endpoint/audio/transcriptions",
    "api-reference/endpoint/video/queue",
    "api-reference/endpoint/video/retrieve",
    "api-reference/endpoint/video/quote",
    "api-reference/endpoint/video/complete",
    "api-reference/endpoint/embeddings/generate",
    "api-reference/endpoint/models/list",
    "api-reference/endpoint/models/compatibility_mapping",
    "api-reference/endpoint/models/traits",
    "api-reference/endpoint/characters/list",
    "api-reference/endpoint/api_keys/list",
    "api-reference/endpoint/api_keys/create",
    "api-reference/endpoint/api_keys/delete",
]
```

---

## Merge Priority (When Sources Conflict)
| Content Type | Winner | Why |
|---|---|---|
| Endpoint schemas/params | `swagger.yaml` | Canonical machine-readable spec |
| Prose, guides, tutorials | GitHub MDX files | Author-written, version-controlled |
| Model catalogs, pricing tables | Live site scrape or API probe | JS-rendered, most current |
| Deprecation notices | GitHub MDX | Version-controlled announcements |
| Navigation structure | `docs.json` | Defines canonical hierarchy |

---

## MDX → Markdown Conversion Rules
The docs use Mintlify components. Convert as follows:

| Mintlify MDX | Clean Markdown Output |
|---|---|
| `<CodeGroup>` wrapper | Strip wrapper, keep inner fenced code blocks with lang labels |
| `<Steps><Step title="X">content</Step></Steps>` | `### Step 1: X\ncontent` (numbered) |
| `<Note>text</Note>` | `> **Note:** text` |
| `<Warning>text</Warning>` | `> ⚠️ **Warning:** text` |
| `<Card title="T" href="U">desc</Card>` | `- **[T](U)** — desc` |
| `<CardGroup cols={N}>` | Strip wrapper |
| `<Tabs><Tab title="T">` | `#### T` subsection |
| `<Accordion title="T">` | `<details><summary>T</summary>` |
| `<div id="*-placeholder">` | Replace with scraped content or `[Dynamic content — see live docs]` |
| YAML frontmatter `---` block | Extract `title` as H1, preserve rest as HTML comment metadata |
| `<Tooltip>`, `<Frame>`, etc. | Strip tags, keep inner text |

---

## `pyproject.toml`
```toml
[project]
name = "venice-kb-collector"
version = "0.1.0"
description = "Pull, collate, and track changes in Venice AI API documentation for agent knowledge bases"
requires-python = ">=3.11"
license = {text = "MIT"}
dependencies = [
    "httpx>=0.27",
    "pyyaml>=6.0",
    "beautifulsoup4>=4.12",
    "playwright>=1.45",
    "openai>=1.30",
    "tiktoken>=0.7",
    "pydantic>=2.7",
    "typer[all]>=0.12",
    "rich>=13.7",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.5",
    "black>=24.0",
    "mypy>=1.10",
]

[project.scripts]
venice-kb = "venice_kb.cli:app"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## README.md Content

Write a comprehensive README with these sections:
1. **What This Is** — One-paragraph description
2. **Quick Start (Codespace)** — "Click the green Code button → Open with Codespaces → run `make build`"
3. **Quick Start (Local)** — Clone, create venv, install, configure `.env`, run
4. **Quick Start (JetBrains IDE)** — Open project, set Python interpreter, run config for `venice_kb build`
5. **CLI Reference** — All subcommands with examples
6. **Understanding the Changelog** — How change tracking works, severity levels explained, how to read CHANGELOG.md and CHANGELOG.json
7. **Output Structure** — Full tree of knowledge_base/ with descriptions
8. **Architecture** — Data flow diagram (ASCII art), module responsibilities
9. **Configuration** — All env vars, their defaults, what they do
10. **Using the KB with AI Agents** — How to point JetBrains AI / Copilot / Cursor at the output, how to use `_index.json` programmatically
11. **Contributing** — Standard PR workflow
12. **License** — MIT

---

## Makefile
```makefile
.PHONY: build update changelog test lint format clean setup

setup:
	pip install -e '.[dev]'
	playwright install chromium --with-deps

build:
	python -m venice_kb build --output ./knowledge_base --snapshot-dir ./snapshots

update:
	python -m venice_kb update --output ./knowledge_base --snapshot-dir ./snapshots

changelog:
	python -m venice_kb changelog --snapshot-dir ./snapshots --output ./knowledge_base/CHANGELOG.md

diff:
	python -m venice_kb changelog --snapshot-dir ./snapshots --last-n 2 --severity important

status:
	python -m venice_kb status --kb-path ./knowledge_base --snapshot-dir ./snapshots

test:
	python -m pytest tests/ -v

lint:
	python -m ruff check src/ tests/
	python -m black --check src/ tests/

format:
	python -m black src/ tests/
	python -m ruff check --fix src/ tests/

clean:
	rm -rf .cache/ knowledge_base/ snapshots/ .pytest_cache/
```

---

## Key Implementation Notes

1. **Playwright is required** for model catalog and pricing pages — the Venice docs use `model-search.js` (100KB) that hydrates `<div id="model-search-placeholder">` at render time. The raw MDX files contain only empty placeholder divs.

2. **The Venice API itself** at `https://api.venice.ai/api/v1/models` returns live model data and can supplement or verify scraped model catalogs. Probe this endpoint (requires API key) and cross-reference.

3. **`swagger.yaml` is 292KB** — it's the single most valuable file and should be parsed into individual endpoint pages, each containing: method, path, parameters (with types), request body schema (fully expanded), response schemas, and any `x-venice-*` extensions.

4. **`docs.json`** (not `mint.json`) is the Mintlify navigation manifest. It defines the canonical page hierarchy and should be used to discover all pages, even ones not yet in `llms.txt`.

5. **`llms.txt`** is specifically designed for LLM consumption — it's a curated index. Use it as the starting manifest but cross-reference with `docs.json` for completeness (some newer guide pages like `crewai`, `langchain`, `vercel-ai-sdk` may be in `docs.json` but not `llms.txt`).

6. **Snapshot files** should be compact — they store `{path: {hash, token_count, title, tags}}` per page, NOT the full content. Full content lives in the KB output files. This keeps snapshots small and diffing fast.

7. **LLM calls should be optional** — the `--skip-llm` flag must work. Without LLM, dedup uses content hashing only, changelog summaries are omitted, and merge conflicts use the priority table above without intelligent reconciliation.

8. **Cache everything** — `.cache/` stores raw fetched content keyed by source+hash. Incremental builds (`update` command) check ETags/Last-Modified headers and GitHub commit SHAs to skip unchanged content.

9. **The changelog is the killer feature for production use** — it should be the first thing a developer or agent reads after a build. Make it prominent in the output, well-formatted, and available in both `.md` (human) and `.json` (machine) formats.

10. **Token counts matter** — JetBrains AI assistant and other agent frameworks have context windows. Every page in the index should report its token count so agents can decide what fits in context.
