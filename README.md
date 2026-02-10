# 🐺 Venice KB Collector

Pull Venice AI API documentation from multiple sources, merge it into a structured knowledge base, and track what changed between builds.

## ✨ Features

- **Multi-source fetching**: GitHub MDX files, OpenAPI spec, live web scraping, API probing
- **Smart merging**: Combines content from all sources with conflict resolution
- **Mintlify MDX support**: Converts all Mintlify components to clean Markdown
- **Change tracking**: Snapshots with intelligent diffing and changelog generation
- **Deduplication**: Hash-based and similarity-based duplicate detection
- **Chunking**: Automatic splitting of large pages on heading boundaries
- **Rich CLI**: Progress bars, colored output, verbose logging
- **Graceful fallbacks**: Works even when some sources fail or API keys unavailable

## 🚀 Quick Start (Codespace)

1. Open this repo in GitHub Codespaces (click the green "Code" button)
2. Wait for setup to complete (runs `make setup && make install` automatically)
3. Run the build:

```bash
make build
```

That's it! Your knowledge base will be in `knowledge_base/` with a full changelog.

## 🛠 Local Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/FoxingWolf/docusynthetic-test.git
cd docusynthetic-test

# Install dependencies and Playwright browsers
make setup

# Install the package
make install
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Optional environment variables:**

- `VENICE_API_KEY`: For API probing and LLM features (not required)
- `GITHUB_TOKEN`: For higher GitHub API rate limits (not required for public repos)

The tool works fine without these — it just skips optional features gracefully.

## 📖 Usage

### Build Commands

```bash
# Full build
make build

# Or use the CLI directly
python -m venice_kb build --verbose

# Skip web scraping (faster, uses placeholders)
python -m venice_kb build --skip-web-scraping

# Skip LLM features (dedup uses hash-only)
python -m venice_kb build --skip-llm

# Force refresh (bypass all caches)
python -m venice_kb build --force-refresh
```

### Other Commands

```bash
# Show status
make status
# or
python -m venice_kb status

# Generate changelog from existing snapshots
python -m venice_kb changelog

# Validate knowledge base integrity
python -m venice_kb validate

# Run tests
make test

# Lint code
make lint

# Format code
make format
```

## 📁 Output Structure

```
knowledge_base/
├── _index.json           # Master catalog with all pages and endpoints
├── _manifest.json        # Build metadata (timestamp, versions, stats)
├── CHANGELOG.md          # Human-readable changelog
├── CHANGELOG.json        # Machine-readable changelog
├── swagger.yaml          # OpenAPI specification
├── overview/             # Overview pages
├── guides/               # Guide pages
├── models/               # Model documentation
├── api-reference/        # API endpoint docs
│   └── endpoints/
└── meta/                 # Metadata pages

snapshots/
└── snapshot_20240115_143022.json  # KB snapshots for diffing
```

Each `.md` file has YAML frontmatter:

```yaml
---
title: "Getting Started"
source: "venice-kb-collector"
last_updated: "2024-01-15T14:30:22"
content_hash: "abc123..."
token_count: 1542
tags: ["guide", "quickstart"]
---
```

## 🏗 Architecture

### Phase 1: Sources (Fetch Everything)

- **`github_fetcher.py`**: Async fetch all `.mdx` files, `swagger.yaml`, `llms.txt`, `docs.json` from `veniceai/api-docs` repo
- **`openapi_parser.py`**: Parse OpenAPI spec, extract endpoints with full schemas
- **`web_scraper.py`**: Use Playwright to render JS-heavy pages (models, pricing)
- **`api_prober.py`**: Hit live API for current model catalog
- **`manifest_loader.py`**: Parse and cross-reference `llms.txt` and `docs.json`

### Phase 2: Processing (Convert & Merge)

- **`mdx_converter.py`**: Mintlify MDX → Markdown (CodeGroup, Steps, Note, Warning, Card, Tabs, etc.)
- **`html_converter.py`**: Scraped HTML → Markdown tables/lists
- **`merger.py`**: Combine MDX base + OpenAPI enrichment + web scrape injection
- **`deduplicator.py`**: Remove exact and near-duplicate pages
- **`chunker.py`**: Split pages >3500 tokens on heading boundaries

### Phase 3: Diffing (Track Changes)

- **`models.py`**: Pydantic models for snapshots, changes, severity levels
- **`snapshot.py`**: Create/load snapshots (lightweight manifest of hashes, not full content)
- **`differ.py`**: Diff two snapshots, classify severity (breaking/important/informational/cosmetic)
- **`changelog_writer.py`**: Render markdown and JSON changelogs

### Phase 4: Output (Write KB)

- **`kb_writer.py`**: Write pages with frontmatter, create directory structure
- **`index_writer.py`**: Write `_index.json` and `_manifest.json`

### Phase 5: CLI

- **`cli.py`**: Typer-based CLI with rich progress bars
- Commands: `build`, `update`, `changelog`, `validate`, `status`

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=venice_kb tests/

# Run specific test file
pytest tests/test_mdx_converter.py -v
```

Tests use fixtures in `tests/fixtures/` — no external network calls.

## 🤖 Using with AI Agents

The knowledge base is designed for AI consumption:

1. **`_index.json`**: Start here — master catalog with all pages, endpoints, stats
2. **`CHANGELOG.json`**: Machine-readable changes for keeping context up to date
3. **Frontmatter in every `.md`**: Token counts, hashes, tags for efficient retrieval
4. **Clean Markdown**: No proprietary formats, just standard Markdown

### Example: Load into RAG

```python
import json
from pathlib import Path

# Load index
index = json.loads(Path("knowledge_base/_index.json").read_text())

# Get all pages
for page in index["pages"]:
    path = Path("knowledge_base") / page["path"]
    content = path.read_text()
    # Add to your vector store
    vector_store.add(content, metadata=page)
```

## 📝 Changelog Format

Changelogs are grouped by severity:

- 🚨 **Breaking Changes**: API removals, schema changes, deprecations
- ⚠️ **Important Changes**: New endpoints, pricing updates, auth changes
- ℹ️ **Informational**: New pages, model updates, guide additions
- 🎨 **Cosmetic**: Minor edits, typo fixes (<5% token change)

Each entry shows:
- Change type (NEW/MODIFIED/REMOVED)
- File path
- Description
- Diff preview (for modifications)

## 🔧 Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
make format

# Lint
make lint

# Run tests with coverage
make test
```

## 📚 Configuration

All configuration via environment variables (see `.env.example`):

- `CACHE_DIR`: Cache directory (default: `.cache`)
- `CHUNK_MAX_TOKENS`: Max tokens per chunk (default: 3500)
- `SKIP_WEB_SCRAPING`: Skip Playwright (default: false)
- `SKIP_API_PROBING`: Skip API calls (default: false)
- `SKIP_LLM_FEATURES`: Disable LLM dedup/summaries (default: false)

## 🐛 Troubleshooting

### Playwright not working in CI

Use `--skip-web-scraping` flag. Pages will have placeholder text instead of scraped content.

### Rate limited by GitHub

Set `GITHUB_TOKEN` in `.env` for higher rate limits.

### Build fails on missing API key

That's fine! API probing is optional. Set `VENICE_API_KEY` only if you want live model data.

## 📜 License

MIT

## 🙏 Contributing

PRs welcome! Please:

1. Run tests: `make test`
2. Format code: `make format`
3. Update docs if adding features

## 🔗 Links

- [Venice AI Docs](https://docs.venice.ai)
- [Venice AI API](https://api.venice.ai)
- [GitHub Repo](https://github.com/FoxingWolf/docusynthetic-test)
