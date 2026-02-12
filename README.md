# Venice KB Collector

**Pull, collate, and track changes in Venice AI API documentation for agent knowledge bases**

Venice KB Collector is a Python tool that fetches Venice AI API documentation from multiple sources (GitHub repo, live docs site, OpenAPI spec), processes and deduplicates it into a structured knowledge base, and — critically — **tracks changes between runs** so downstream agents and humans can see what's new, modified, or removed since the last build.

## What This Is

This tool solves the problem of keeping AI agents up-to-date with the latest Venice AI API documentation. Instead of manually monitoring docs for changes, Venice KB Collector:

- **Fetches** docs from multiple sources: GitHub MDX files, OpenAPI specs, live web pages (with Playwright), and live API probes
- **Processes** content: converts Mintlify MDX to clean Markdown, deduplicates across sources, merges with intelligent priority rules
- **Tracks changes**: creates snapshots of each build, diffs between builds, classifies changes by severity (breaking/important/info/cosmetic)
- **Generates changelogs**: produces human-readable Markdown and machine-readable JSON changelogs for downstream consumption

Perfect for keeping JetBrains AI Assistant, GitHub Copilot, or custom agents synchronized with Venice AI's evolving API.

---

## Quick Start (GitHub Codespaces)

1. Click the **Code** button at the top of this repo
2. Select **Open with Codespaces** → **Create codespace on main**
3. Wait for the container to build (auto-installs Python 3.12, Playwright, all dependencies)
4. Copy `.env.example` to `.env` and add your Venice API key
5. Run `make build` to build your first knowledge base

That's it! The knowledge base will be in `./knowledge_base/` with a full changelog.

---

## Quick Start (Local)

### Prerequisites
- Python 3.11 or 3.12
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/FoxingWolf/docusynthetic-test.git
cd docusynthetic-test

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make setup
# Or manually: pip install -e '.[dev]' && playwright install chromium --with-deps

# Configure environment
cp .env.example .env
# Edit .env and add your Venice API key
```

### First Build

```bash
# Build the full knowledge base
make build

# View the results
ls -la knowledge_base/
cat knowledge_base/CHANGELOG.md
```

---

## Quick Start (JetBrains IDE)

1. **Open Project**: File → Open → Select this repository
2. **Configure Python Interpreter**:
   - Settings → Project → Python Interpreter
   - Add Interpreter → Virtualenv Environment → New
   - Base interpreter: Python 3.12
3. **Install Dependencies**:
   - Open Terminal in IDE
   - Run `make setup`
4. **Configure `.env`**:
   - Copy `.env.example` to `.env`
   - Add your Venice API key
5. **Create Run Configuration**:
   - Run → Edit Configurations → Add New → Python
   - Script path: `src/venice_kb/__main__.py`
   - Parameters: `build --output ./knowledge_base --snapshot-dir ./snapshots`
   - Working directory: (project root)
6. **Run**: Click the Run button

---

## CLI Reference

### `venice-kb build`

Build the full knowledge base from all sources.

```bash
venice-kb build [OPTIONS]

Options:
  -o, --output PATH         Output directory (default: ./knowledge_base)
  -s, --snapshot-dir PATH   Snapshot directory (default: ./snapshots)
  --sources TEXT            Comma-separated: github,openapi,web,api (default: all)
  -f, --force-refresh       Bypass cache, re-fetch everything
  --skip-llm                Skip LLM-assisted processing (faster)
  --no-changelog            Skip changelog generation
  -l, --log-level TEXT      Log level: DEBUG, INFO, WARNING, ERROR

Example:
  venice-kb build --output ./kb --force-refresh
```

### `venice-kb update`

Incremental update — only fetch and process changed content.

```bash
venice-kb update [OPTIONS]

Options:
  -o, --output PATH         Output directory
  -s, --snapshot-dir PATH   Snapshot directory

Example:
  venice-kb update
```

### `venice-kb changelog`

Generate changelog from snapshots without rebuilding.

```bash
venice-kb changelog [OPTIONS]

Options:
  -s, --snapshot-dir PATH   Snapshot directory
  -o, --output PATH         Output file (default: <kb>/CHANGELOG.md)
  -n, --last-n INT          Compare last N builds (default: 5)
  --format TEXT             Output format: md, json, or both (default: both)
  --severity TEXT           Filter: breaking, important, info, cosmetic, all

Example:
  venice-kb changelog --last-n 10 --format md --severity important
```

### `venice-kb diff`

Compare two specific snapshots.

```bash
venice-kb diff --old PATH --new PATH [--output PATH]

Example:
  venice-kb diff \
    --old snapshots/2024-01-01.json \
    --new snapshots/2024-01-08.json \
    --output diff-report.md
```

### `venice-kb validate`

Validate an existing knowledge base.

```bash
venice-kb validate --kb-path PATH

Example:
  venice-kb validate --kb-path ./knowledge_base
```

### `venice-kb status`

Show current state — last build time, source versions, page count.

```bash
venice-kb status [OPTIONS]

Options:
  --kb-path PATH            KB directory
  --snapshot-dir PATH       Snapshot directory

Example:
  venice-kb status
```

---

## Understanding the Changelog

The changelog is the **killer feature** — it tells you exactly what changed between builds.

### Severity Levels

- **🚨 Breaking**: Endpoint removed, schema changed incompatibly, authentication changed
- **⚠️ Important**: New endpoint, new required parameter, pricing change, deprecation notice
- **ℹ️ Informational**: New optional parameter, model list refresh, guide updates
- **🎨 Cosmetic**: Minor wording changes, formatting fixes

### Reading CHANGELOG.md

```markdown
## 2024-02-12 (Latest Build)
> Compared against: 2024-02-05 build | Added: 1, Modified: 4, Removed: 0

### 🚨 Breaking Changes
_None detected_

### ⚠️ Important Changes
- **NEW** `api-reference/endpoint/audio/transcriptions.md` — New Audio Transcriptions endpoint...
- **MODIFIED** `overview/pricing.md` — Price decrease for qwen3-235b model...

### ℹ️ Informational Changes
- **MODIFIED** `models/text.md` — Two new models added: grok-code-fast-1, venetian-1
```

### Using CHANGELOG.json Programmatically

```python
import json

with open('knowledge_base/CHANGELOG.json') as f:
    data = json.load(f)

latest_report = data['reports'][0]

# Filter for breaking changes only
for change in latest_report['breaking_changes']:
    print(f"BREAKING: {change['path']} - {change['details']}")

# Get all changes to pricing
for report in data['reports']:
    for change in report['important_changes']:
        if 'pricing' in change['path']:
            print(change)
```

---

## Output Structure

```
knowledge_base/
├── _index.json                           # Master catalog with metadata
├── CHANGELOG.md                          # Human-readable changelog
├── CHANGELOG.json                        # Machine-readable changelog
├── overview/
│   ├── about-venice.md
│   ├── getting-started.md
│   ├── pricing.md
│   └── guides/
│       ├── openai-migration.md
│       ├── langchain.md
│       └── ...
├── models/
│   ├── overview.md
│   ├── text.md
│   ├── image.md
│   └── ...
└── api-reference/
    ├── api-spec.md
    ├── rate-limiting.md
    ├── error-codes.md
    └── endpoint/
        ├── chat/
        │   └── completions.md
        ├── image/
        │   └── generate.md
        └── ...
```

### `_index.json` Structure

```json
{
  "version": "1.0",
  "generated_at": "2024-02-12T06:00:00Z",
  "sources": {
    "github_commit": "abc123",
    "openapi_hash": "def456"
  },
  "pages": {
    "api-reference/endpoint/chat/completions.md": {
      "hash": "sha256hash",
      "token_count": 2847,
      "title": "Chat Completions",
      "tags": ["api", "chat", "completions"]
    }
  },
  "stats": {
    "total_pages": 58,
    "total_tokens": 124500
  }
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         SOURCES                              │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ GitHub       │ OpenAPI      │ Web Scraper  │ API Prober     │
│ (MDX files)  │ (swagger.yml)│ (Playwright) │ (/models)      │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬───────┘
       │              │              │                │
       └──────────────┴──────────────┴────────────────┘
                      │
         ┌────────────▼────────────┐
         │     PROCESSING          │
         ├─────────────────────────┤
         │ • MDX → Markdown        │
         │ • HTML → Markdown       │
         │ • Deduplication         │
         │ • Multi-source merge    │
         │ • Semantic chunking     │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │     DIFFING             │
         ├─────────────────────────┤
         │ • Create snapshot       │
         │ • Compare with previous │
         │ • Classify severity     │
         │ • Generate changelog    │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │     OUTPUT              │
         ├─────────────────────────┤
         │ • Write KB files        │
         │ • Write _index.json     │
         │ • Write CHANGELOG       │
         └─────────────────────────┘
```

### Module Responsibilities

- **sources/**: Fetch content from various sources (async I/O)
- **processing/**: Convert, deduplicate, merge content (sync data processing)
- **diffing/**: Snapshot management, diff engine, severity classification
- **output/**: Write files to disk in structured format
- **llm/**: Optional OpenAI-compatible client for smart features
- **utils/**: Hashing, token counting, logging

---

## Configuration

### Environment Variables

All configuration is in `.env` (copy from `.env.example`):

```bash
# Required for LLM features (optional, gracefully degrades without it)
VENICE_API_KEY=your-api-key
LLM_BASE_URL=https://api.venice.ai/api/v1
LLM_MODEL=venice-uncensored

# Optional: GitHub token for higher rate limits
GITHUB_TOKEN=ghp_...

# Optional: Override defaults
KB_OUTPUT_DIR=./knowledge_base
SNAPSHOT_DIR=./snapshots
CACHE_DIR=./.cache
CHUNK_TARGET_TOKENS=2000
CHUNK_MAX_TOKENS=3500
LOG_LEVEL=INFO
```

### Defaults (in `config.py`)

- **Sources**: GitHub repo `veniceai/api-docs`, live site `https://docs.venice.ai`, OpenAPI at `swagger.yaml`
- **Dynamic pages**: Model catalogs, pricing (require Playwright)
- **Chunk size**: 2000 tokens target, 3500 max
- **Cache**: `.cache/` directory, respects ETags and Last-Modified headers

---

## Using the KB with AI Agents

### JetBrains AI Assistant

1. Build the KB: `make build`
2. In PyCharm/IntelliJ: Settings → Tools → AI Assistant
3. Add custom context: Point to `knowledge_base/` directory
4. AI Assistant can now answer questions about Venice AI API using the latest docs

### GitHub Copilot

Add to `.github/copilot-instructions.md`:

```markdown
When working with Venice AI API, refer to the knowledge base in `knowledge_base/`.
Check `CHANGELOG.md` for recent API changes.
```

### Cursor

Add to `.cursorrules`:

```
Use the Venice AI docs in knowledge_base/ for API questions.
```

### Programmatic Access

```python
import json

# Load the index
with open('knowledge_base/_index.json') as f:
    index = json.load(f)

# Find pages under a certain token limit
pages_under_4k = {
    path: meta
    for path, meta in index['pages'].items()
    if meta['token_count'] < 4000
}

# Load specific page content
with open(f"knowledge_base/{path}") as f:
    content = f.read()
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `make test`
5. Run linters: `make lint`
6. Format code: `make format`
7. Commit: `git commit -m "feat: add my feature"`
8. Push: `git push origin feature/my-feature`
9. Open a Pull Request

### Running Tests

```bash
make test           # Run all tests
pytest tests/ -v    # Verbose output
pytest tests/test_differ.py -k test_diff_added_pages  # Specific test
```

### Code Style

- Black for formatting (line length 100)
- Ruff for linting
- Pydantic v2 for data models
- Modern Python 3.11+ syntax (`str | None`, not `Optional[str]`)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Roadmap

- [x] Core snapshot and diff system
- [x] CLI with all subcommands
- [x] MDX/Mintlify conversion
- [x] Multi-source fetching
- [ ] Full build implementation (currently stub)
- [ ] LLM-assisted changelog summaries
- [ ] Incremental update optimization
- [ ] API endpoint validation
- [ ] Automated GitHub Actions builds

---

## Credits

Built for tracking Venice AI API documentation changes. Not affiliated with Venice AI.

**Maintainer**: [@FoxingWolf](https://github.com/FoxingWolf)