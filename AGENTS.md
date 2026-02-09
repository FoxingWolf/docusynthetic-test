# DocuSynthetic - Venice AI API Documentation Tool

## Full Specification

### Overview

DocuSynthetic is a Python CLI tool designed to scrape, fetch, merge, and maintain Venice AI API documentation from multiple sources. It creates a unified knowledge base with change tracking and severity-rated changelogs.

### Features

1. **Multi-Source Documentation Fetching**
   - GitHub repository (veniceai/api-docs) MDX files
   - OpenAPI specification (swagger.yaml)
   - Live documentation site (docs.venice.ai) via Playwright

2. **Intelligent Processing**
   - Automatic merging and deduplication of content
   - Content hash-based change detection
   - Source prioritization (GitHub MDX > OpenAPI > Live Site)

3. **Structured Output**
   - Markdown knowledge base with frontmatter metadata
   - JSON index with categorization and tagging
   - Severity-rated changelogs (breaking/important/info)

4. **Development Tools**
   - Typer-based CLI with rich console output
   - Pydantic models for type safety
   - Async httpx for efficient HTTP requests
   - Playwright for live site scraping

5. **DevOps Integration**
   - Codespace-ready devcontainer configuration
   - GitHub Actions for scheduled builds
   - Automated releases with changelog

### Architecture

#### Data Models (Pydantic)

- **DocumentMetadata**: Stores title, source, URL, tags, category, and timestamps
- **DocumentContent**: Contains metadata, content, raw content, and content hash
- **APIEndpoint**: Represents API endpoint information from OpenAPI spec
- **ChangelogEntry**: Records changes with severity levels and affected paths
- **KnowledgeBaseIndex**: JSON index structure for the entire knowledge base
- **BuildState**: Captures the state of each build for change detection

#### Fetchers

All fetchers implement the `BaseFetcher` interface with an async `fetch()` method:

1. **GitHubMDXFetcher**
   - Uses GitHub API to recursively fetch MDX/MD files
   - Parses frontmatter metadata
   - Creates content hashes for change detection
   - Default source: veniceai/api-docs repository

2. **OpenAPIFetcher**
   - Fetches and parses YAML/JSON OpenAPI specifications
   - Generates markdown documentation for each endpoint
   - Extracts parameters, request/response schemas
   - Creates both overview and per-endpoint documents

3. **LiveSiteFetcher**
   - Uses Playwright for browser automation
   - Scrapes documentation from live website
   - Extracts navigation links, content, tags, and categories
   - Runs in headless mode by default

#### Processors

**DocumentProcessor** handles:
- Document merging with deduplication
- Index generation with categorization
- Change detection between builds
- Severity determination (breaking/important/info)
- State persistence for incremental builds
- Markdown and JSON output generation

#### CLI Commands

1. **build**: Main command to build the knowledge base
   - Options: --output, --config, --github, --openapi, --live-site
   - Fetches from all enabled sources
   - Merges and deduplicates content
   - Generates index and changelog
   - Saves state for next build

2. **diff**: Display changes from the last build
   - Shows the generated changelog
   - Useful for reviewing what changed

3. **config**: Generate a default configuration file
   - Creates config.json with all settings
   - Can be customized and passed to build command

4. **install-playwright**: Install Playwright browsers
   - Installs chromium browser for live site scraping

### Configuration

Configuration can be provided via JSON file or command-line options:

```json
{
  "github_repo_owner": "veniceai",
  "github_repo_name": "api-docs",
  "github_branch": "main",
  "github_docs_path": "",
  "openapi_spec_url": "https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml",
  "live_site_url": "https://docs.venice.ai",
  "live_site_headless": true,
  "output_dir": "./output",
  "fetch_github": true,
  "fetch_openapi": true,
  "fetch_live_site": true
}
```

### Output Structure

```
output/
├── index.json              # JSON index with all metadata
├── state.json             # Build state for change detection
├── CHANGELOG.md           # Human-readable changelog
├── changelog.json         # Machine-readable changelog
└── knowledge_base/        # Markdown documentation files
    ├── document-1.md
    ├── document-2.md
    └── ...
```

### Change Detection

Changes are detected by comparing content hashes between builds:

1. **New Documents**: INFO severity
2. **Removed Documents**: BREAKING severity
3. **Modified Documents**: IMPORTANT or INFO based on content:
   - API/endpoint changes: IMPORTANT
   - General updates: INFO

### Severity Levels

- **BREAKING**: Breaking changes, removed content, deprecated APIs
- **IMPORTANT**: Significant updates, API changes, new features
- **INFO**: Minor updates, typo fixes, clarifications

### GitHub Actions Workflow

The workflow:
1. Runs on a schedule (daily at 2 AM UTC)
2. Can be manually triggered
3. Installs dependencies and Playwright
4. Builds the knowledge base
5. Uploads artifacts
6. Creates releases with changelogs on changes

### Development Setup

**Using GitHub Codespaces:**
1. Open repository in Codespaces
2. Devcontainer automatically installs dependencies
3. Start developing immediately

**Local Development:**
```bash
# Clone repository
git clone <repo-url>
cd docusynthetic-test

# Install in development mode
pip install -e '.[dev]'

# Install Playwright browsers
playwright install chromium

# Run the tool
docusynthetic build
```

### Usage Examples

**Build knowledge base with all sources:**
```bash
docusynthetic build --output ./output
```

**Build with specific sources only:**
```bash
docusynthetic build --no-live-site --output ./docs
```

**Use custom configuration:**
```bash
docusynthetic config --output my-config.json
# Edit my-config.json as needed
docusynthetic build --config my-config.json
```

**View changes:**
```bash
docusynthetic diff --output ./output
```

### Testing

Run tests with pytest:
```bash
pytest tests/
```

### Linting and Formatting

```bash
# Format code
black docusynthetic/

# Lint code
ruff check docusynthetic/

# Type checking
mypy docusynthetic/
```

### Dependencies

**Core:**
- typer: CLI framework
- pydantic: Data validation and models
- httpx: Async HTTP client
- playwright: Browser automation
- pyyaml: YAML parsing
- python-frontmatter: Frontmatter parsing
- markdown: Markdown processing
- rich: Rich terminal output

**Development:**
- pytest: Testing framework
- pytest-asyncio: Async test support
- black: Code formatting
- ruff: Fast Python linter
- mypy: Type checking

### Future Enhancements

- Incremental fetching (only fetch changed files)
- Support for additional documentation sources
- Semantic change detection (not just hash-based)
- Search functionality in knowledge base
- Web UI for browsing knowledge base
- Diff visualization between versions
- Webhook notifications for changes
- Custom severity rules configuration
