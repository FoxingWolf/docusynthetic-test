# 🐺 Venice KB Collector — Agent Implementation Spec

This document serves as a complete reference for AI agents working on this codebase. It captures the full requirements, architecture, and implementation details.

## Project Overview

**Name**: Venice KB Collector
**Purpose**: Pull Venice AI API documentation from multiple sources, merge into structured knowledge base, track changes
**Language**: Python 3.11+
**Framework**: Typer (CLI), Pydantic (models), Rich (output)

## Core Philosophy

1. **No stubs, no TODOs** — Every function has a real implementation
2. **Graceful degradation** — If one source fails, continue with what you have
3. **Type hints everywhere** — Use modern Python `str | None` syntax
4. **Async where it matters** — Source fetching is async, processing is sync
5. **Codespace-first UX** — Open → `make build` → done

## Architecture

### Source Fetching (Async)

**github_fetcher.py**
- Fetch `.mdx` files from `veniceai/api-docs` repo (main branch)
- Fetch `swagger.yaml`, `llms.txt`, `docs.json`
- Use page list from `docs.json` to discover all pages
- Cache with ETags in `.cache/github/`
- Exponential backoff on rate limiting
- No crashes on missing files — log and continue

**openapi_parser.py**
- Parse `swagger.yaml` with PyYAML
- Extract ALL endpoints (method, path, summary, params, request/response schemas)
- Fully expand `$ref` pointers recursively
- Generate Markdown per endpoint with parameter tables, examples
- Handle `x-venice-*` extensions

**web_scraper.py**
- Playwright (async, chromium) to scrape JS-rendered pages
- Target pages: models/overview, models/text, models/image, pricing, beta-models
- Wait for placeholder divs to be replaced
- Graceful fallback if Playwright unavailable (CI) — return placeholder text
- Cache in `.cache/web/`

**api_prober.py**
- Hit `https://api.venice.ai/api/v1/models` with API key
- Parse live model catalog
- Must work without API key — skip gracefully if missing

**manifest_loader.py**
- Parse `llms.txt` → URL list with descriptions
- Parse `docs.json` → full navigation hierarchy
- Cross-reference to build canonical page list
- Pages in `docs.json` but not `llms.txt` = newer pages

### Processing (Sync)

**mdx_converter.py**
- Convert Mintlify MDX → Markdown
- Handle: CodeGroup, Steps, Note, Warning, Card, CardGroup, Tabs, Accordion, Tooltip, Frame, Icon
- Extract YAML frontmatter → use title/description
- Flag placeholder divs for merger
- Use regex + BeautifulSoup, NOT full MDX parser

**html_converter.py**
- Convert scraped HTML → Markdown
- Use markdownify library
- Extract semantic content from Venice's class-based styling (vpt-*)
- Strip SVG icons, decorative markup

**merger.py**
- For each canonical page:
  1. Start with MDX from GitHub (converted)
  2. Inject scraped content into placeholders
  3. Enrich endpoint pages with OpenAPI data
  4. Add breadcrumb navigation from `docs.json`
- Conflict resolution: swagger > MDX for schemas, MDX for prose, web scrape for dynamic data

**deduplicator.py**
- Pass 1: SHA256 hash on normalized text → remove exact duplicates
- Pass 2: Jaccard similarity on word sets → merge similar pages (keep longer)
- LLM-merge optional (not implemented in v0.1)

**chunker.py**
- Split pages > CHUNK_MAX_TOKENS (default 3500)
- Split on heading boundaries (H2 > H3 > paragraph)
- Use tiktoken for token counting (fallback to char count ÷ 4)
- Each chunk gets metadata: parent page, chunk index, heading path
- Small pages stay whole

### Diffing & Changelog

**models.py** (Pydantic)
- `ChangeType`: added | modified | removed | unchanged
- `SeverityLevel`: breaking | important | informational | cosmetic
- `ChangeEntry`: change details with diff preview
- `DiffReport`: full report with stats
- `KBSnapshot`: lightweight manifest (hashes, not content)

**snapshot.py**
- `create_snapshot()`: walk KB, hash files, count tokens, extract titles
- `save_snapshot()`: write to `snapshots/{timestamp}.json`
- `load_latest_snapshot()`: find most recent
- Snapshots are compact — just metadata, not full content

**differ.py**
- `diff_snapshots()`: compare old vs new
  - Added: in new, not in old
  - Removed: in old, not in new
  - Modified: same path, different hash
  - Unchanged: skip
- Severity classification:
  - Breaking: endpoint removals, deprecations, "breaking change" in diff
  - Important: pricing, endpoints, auth changes
  - Informational: new pages, model updates
  - Cosmetic: <5% token change

**changelog_writer.py**
- Render `CHANGELOG.md` grouped by severity (🚨 → ⚠️ → ℹ️ → 🎨)
- Each entry: badge (NEW/MODIFIED/REMOVED), path, description, diff preview
- Also write `CHANGELOG.json` for machine consumption
- LLM summary optional (if available)

### Output

**kb_writer.py**
- Write pages to `knowledge_base/` with frontmatter
- Directory structure: overview/, guides/, models/, api-reference/endpoints/, meta/
- Frontmatter: title, source, last_updated, content_hash, token_count, tags
- Write `swagger.yaml` unchanged

**index_writer.py**
- `_index.json`: sections, pages (with metadata), endpoints list, stats
- `_manifest.json`: build metadata (timestamp, source versions, git commit, duration, page count)

### CLI

**cli.py** (Typer + Rich)
- `build`: Full pipeline (default command)
  - Flags: --verbose, --skip-llm, --force-refresh, --skip-web-scraping
- `update`: Incremental (not implemented yet)
- `changelog`: Generate from existing snapshots
- `validate`: Check KB integrity (not implemented)
- `status`: Show last build, page count, snapshot count
- Rich progress bars for each phase

## Data Flow

```
[GitHub] → github_fetcher → MDX files
[GitHub] → github_fetcher → swagger.yaml → openapi_parser → endpoints
[GitHub] → github_fetcher → docs.json, llms.txt → manifest_loader → canonical pages
[Web] → web_scraper → HTML → html_converter → Markdown
[API] → api_prober → model catalog

↓

MDX files → mdx_converter → Markdown
Markdown + scraped + OpenAPI → merger → merged pages
Merged pages → deduplicator → unique pages
Unique pages → chunker → chunks (if needed)

↓

Unique pages → kb_writer → knowledge_base/*.md
Unique pages → index_writer → _index.json, _manifest.json
Current KB → snapshot → snapshots/*.json
Old snapshot + new snapshot → differ → DiffReport
DiffReport → changelog_writer → CHANGELOG.md, CHANGELOG.json
```

## Testing Strategy

**Fixtures** (`tests/fixtures/`)
- `sample.mdx`: Realistic MDX with all Mintlify components
- `sample_swagger.yaml`: OpenAPI spec with 2 endpoints, $ref examples
- `sample_html.html`: HTML fragment with table, Venice classes
- `sample_llms.txt`: Sample sitemap

**Test Files**
- `test_mdx_converter.py`: Test every component (CodeGroup, Steps, Note, etc.)
- `test_openapi_parser.py`: Test endpoint extraction, $ref resolution
- `test_html_converter.py`: Test table conversion
- `test_deduplicator.py`: Test hash and similarity dedup
- `test_differ.py`: Test all change types, severity classification
- `test_changelog_writer.py`: Test Markdown and JSON output
- `test_cli.py`: Smoke test build command with fixtures

**No external network calls in tests** — use fixtures and mocks

## Error Handling

- **Missing GitHub files**: Log warning, continue with empty
- **Rate limiting**: Exponential backoff, retry 3 times
- **Playwright unavailable**: Skip scraping, use placeholders
- **No API key**: Skip API probing, log info
- **Malformed YAML**: Log error, continue without that source
- **One source fails**: Build produces something, not nothing

## Environment Variables

- `VENICE_API_KEY`: Optional, for API probing
- `GITHUB_TOKEN`: Optional, for higher rate limits
- `CACHE_DIR`: Default `.cache`
- `CHUNK_MAX_TOKENS`: Default 3500
- `SKIP_WEB_SCRAPING`: Default false
- `SKIP_API_PROBING`: Default false
- `SKIP_LLM_FEATURES`: Default false
- `FORCE_REFRESH`: Default false

## File Conventions

- Type hints: `str | None` (not `Optional[str]`)
- Logging: Use `logging.getLogger(__name__)`
- Async: `async def` for I/O, sync for processing
- Docstrings: Google-style with Args and Returns
- Line length: 100 chars (black, ruff)

## Key Design Decisions

1. **Why snapshots, not diffs of full content?**
   Snapshots are lightweight (just hashes), so we can keep many without bloat.

2. **Why not full LLM integration?**
   Works offline/without API key. LLM features are optional enhancements.

3. **Why Playwright for scraping?**
   Venice's model pages are JS-rendered. Raw MDX has empty placeholder divs.

4. **Why both llms.txt and docs.json?**
   llms.txt is human-friendly, docs.json has structure. Cross-referencing catches new pages.

5. **Why separate chunker?**
   Not all pages need chunking. Chunker preserves context with heading paths.

## Known Limitations

- `update` command not implemented (always does full build)
- `validate` command not implemented
- LLM-based dedup not implemented (hash + similarity only)
- No git integration for auto-detecting upstream changes
- Playwright requires browser install (`make setup`)

## Future Enhancements

- Incremental updates (ETags, conditional requests)
- LLM-powered similarity merging
- Auto-detect new pages from git diff
- Vector embeddings for semantic search
- GitHub Actions workflow for scheduled builds
- Diff visualization in HTML

## Maintenance Notes

- Update `veniceai/api-docs` repo URL if it moves
- Update Playwright if selectors change
- Update OpenAPI parser if Venice switches to AsyncAPI
- Add new Mintlify components to mdx_converter as they appear

---

**For AI Agents**: This spec is the source of truth. When in doubt, refer to this document. All code should match the architecture described here.
