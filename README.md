# DocuSynthetic

A Python CLI tool for scraping and managing Venice AI API documentation from multiple sources.

## Overview

DocuSynthetic fetches Venice AI API documentation from:
- GitHub repository (veniceai/api-docs) MDX files
- OpenAPI specification (swagger.yaml)
- Live documentation site (docs.venice.ai) via Playwright

It merges and deduplicates content into a structured Markdown knowledge base with JSON indexing and tracks changes between builds with severity-rated changelogs.

## Features

- 🚀 **Multi-Source Fetching**: Combines docs from GitHub, OpenAPI specs, and live sites
- 🔄 **Smart Merging**: Deduplicates content and prioritizes sources
- 📊 **Change Tracking**: Detects and categorizes changes (breaking/important/info)
- 📝 **Structured Output**: Markdown files with JSON index
- 🛠️ **Modern Stack**: Built with Typer, Pydantic, async httpx, and Playwright
- 🐳 **DevContainer Ready**: Works seamlessly in GitHub Codespaces
- ⚡ **CI/CD**: GitHub Actions for scheduled builds

## Installation

```bash
# Clone the repository
git clone https://github.com/FoxingWolf/docusynthetic-test.git
cd docusynthetic-test

# Install the package
pip install -e .

# Install Playwright browsers
playwright install chromium
```

Or use with development dependencies:

```bash
pip install -e '.[dev]'
```

## Quick Start

### Build Documentation

```bash
# Build knowledge base from all sources
docusynthetic build

# Build with custom output directory
docusynthetic build --output ./my-docs

# Build from specific sources only
docusynthetic build --no-live-site --no-openapi
```

### View Changes

```bash
# Display changelog from last build
docusynthetic diff
```

### Generate Configuration

```bash
# Create a default config file
docusynthetic config --output config.json

# Use custom config
docusynthetic build --config config.json
```

### Install Playwright

```bash
# Install required browsers
docusynthetic install-playwright
```

## Configuration

Create a `config.json` file to customize behavior:

```json
{
  "github_repo_owner": "veniceai",
  "github_repo_name": "api-docs",
  "github_branch": "main",
  "openapi_spec_url": "https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml",
  "live_site_url": "https://docs.venice.ai",
  "output_dir": "./output",
  "fetch_github": true,
  "fetch_openapi": true,
  "fetch_live_site": true
}
```

## Output Structure

```
output/
├── index.json              # Complete documentation index
├── state.json             # Build state for change tracking
├── CHANGELOG.md           # Human-readable changelog
├── changelog.json         # Machine-readable changelog
└── knowledge_base/        # Documentation files
    ├── api-endpoint-1.md
    ├── api-endpoint-2.md
    └── ...
```

## Development

### Using GitHub Codespaces

1. Click "Code" → "Create codespace on main"
2. Wait for devcontainer to initialize
3. Start coding!

### Local Development

```bash
# Install dev dependencies
pip install -e '.[dev]'

# Format code
black docusynthetic/

# Lint code
ruff check docusynthetic/

# Type check
mypy docusynthetic/

# Run tests
pytest tests/
```

## GitHub Actions

The repository includes a workflow that:
- Runs daily at 2 AM UTC
- Can be manually triggered
- Builds the knowledge base
- Uploads artifacts
- Creates releases with changelogs

## Architecture

See [AGENTS.md](AGENTS.md) for the full specification including:
- Data models (Pydantic)
- Fetcher implementations
- Processing pipeline
- Change detection logic
- Output formats

## Dependencies

- **typer** - CLI framework
- **pydantic** - Data validation
- **httpx** - Async HTTP client
- **playwright** - Browser automation
- **pyyaml** - YAML parsing
- **python-frontmatter** - Frontmatter parsing
- **rich** - Terminal output

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.