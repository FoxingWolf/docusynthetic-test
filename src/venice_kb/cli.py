"""Command-line interface for Venice KB Collector."""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from venice_kb.diffing.changelog_writer import ChangelogWriter
from venice_kb.diffing.differ import Differ
from venice_kb.diffing.snapshot import SnapshotManager
from venice_kb.output.index_writer import IndexWriter
from venice_kb.output.kb_writer import KBWriter
from venice_kb.processing.deduplicator import Deduplicator
from venice_kb.processing.merger import Merger
from venice_kb.sources.api_prober import APIProber
from venice_kb.sources.github_fetcher import GitHubFetcher
from venice_kb.sources.manifest_loader import ManifestLoader
from venice_kb.sources.openapi_parser import OpenAPIParser
from venice_kb.sources.web_scraper import WebScraper

# Load environment variables
load_dotenv()

# Create Typer app
app = typer.Typer(
    name="venice-kb",
    help="Venice AI API documentation knowledge base collector",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.command()
def build(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    skip_llm: bool = typer.Option(
        False, "--skip-llm", help="Skip LLM features (dedup falls back to hash-only)"
    ),
    force_refresh: bool = typer.Option(
        False, "--force-refresh", help="Bypass all caches and fetch fresh data"
    ),
    skip_web_scraping: bool = typer.Option(
        False, "--skip-web-scraping", help="Skip web scraping (use placeholders)"
    ),
) -> None:
    """Run full knowledge base build pipeline."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    console.print("[bold green]Venice KB Collector - Full Build[/bold green]\n")

    start_time = time.time()

    try:
        asyncio.run(
            _build_pipeline(
                use_cache=not force_refresh,
                skip_llm=skip_llm,
                skip_web_scraping=skip_web_scraping,
            )
        )

        duration = time.time() - start_time
        console.print(f"\n[bold green]✓ Build completed in {duration:.2f} seconds[/bold green]")

    except Exception as e:
        logger.exception("Build failed")
        console.print(f"[bold red]✗ Build failed: {e}[/bold red]")
        raise typer.Exit(1)


async def _build_pipeline(
    use_cache: bool = True,
    skip_llm: bool = False,
    skip_web_scraping: bool = False,
) -> None:
    """Main build pipeline."""
    logger = logging.getLogger(__name__)

    # Get configuration from environment
    api_key = os.getenv("VENICE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Phase 1: Fetch sources
        task = progress.add_task("Fetching documentation from GitHub...", total=None)

        fetcher = GitHubFetcher(github_token=github_token)
        github_data = await fetcher.fetch_all(use_cache=use_cache)

        progress.update(task, description="✓ Fetched GitHub documentation")

        # Fetch scraped content
        if not skip_web_scraping:
            task2 = progress.add_task("Scraping dynamic web content...", total=None)
            scraper = WebScraper(skip_scraping=skip_web_scraping)
            scraped_content = await scraper.scrape_all(use_cache=use_cache)
            progress.update(task2, description="✓ Scraped web content")
        else:
            scraped_content = {}
            logger.info("Skipping web scraping")

        # Probe API
        task3 = progress.add_task("Probing Venice API...", total=None)
        prober = APIProber(api_key=api_key)
        api_models = await prober.get_models()
        progress.update(task3, description=f"✓ Retrieved {len(api_models)} models from API")

        # Phase 2: Parse sources
        task4 = progress.add_task("Parsing OpenAPI specification...", total=None)

        swagger_yaml = github_data["swagger_yaml"]
        if swagger_yaml:
            openapi_parser = OpenAPIParser(swagger_yaml)
            endpoints = openapi_parser.extract_endpoints()
            swagger_hash = openapi_parser.get_content_hash()
            logger.info(f"Extracted {len(endpoints)} endpoints from OpenAPI spec")
        else:
            endpoints = []
            swagger_hash = None
            logger.warning("No swagger.yaml found")

        progress.update(task4, description=f"✓ Extracted {len(endpoints)} endpoints")

        # Load manifests
        task5 = progress.add_task("Loading manifests...", total=None)
        manifest_loader = ManifestLoader(
            docs_json=github_data["docs_json"], llms_txt=github_data["llms_txt"]
        )
        canonical_pages = manifest_loader.get_canonical_page_list()
        progress.update(task5, description=f"✓ Loaded {len(canonical_pages)} pages")

        # Phase 3: Merge and process
        task6 = progress.add_task("Merging content from sources...", total=None)
        merger = Merger(
            pages=github_data["pages"],
            canonical_pages=canonical_pages,
            openapi_endpoints=endpoints,
            scraped_content=scraped_content,
        )
        merged_pages = merger.merge_all()
        progress.update(task6, description=f"✓ Merged {len(merged_pages)} pages")

        # Deduplicate
        task7 = progress.add_task("Deduplicating content...", total=None)
        deduplicator = Deduplicator(merged_pages)
        unique_pages = deduplicator.deduplicate_similar(use_llm=not skip_llm)
        progress.update(task7, description=f"✓ Deduplicated to {len(unique_pages)} pages")

        # Phase 4: Write output
        task8 = progress.add_task("Writing knowledge base...", total=None)
        kb_writer = KBWriter()
        kb_writer.create_directory_structure()
        kb_writer.write_all(unique_pages)
        if swagger_yaml:
            kb_writer.write_swagger(swagger_yaml)
        progress.update(task8, description="✓ Wrote knowledge base files")

        # Write index
        task9 = progress.add_task("Writing index and manifest...", total=None)
        index_writer = IndexWriter()

        # Build page metadata
        page_metadata = {}
        for path in unique_pages.keys():
            page_metadata[path] = {"title": path, "tags": [], "token_count": 0}

        index_writer.write_index(page_metadata, endpoints)
        index_writer.write_manifest(
            git_commit=None, swagger_hash=swagger_hash, page_count=len(unique_pages)
        )
        progress.update(task9, description="✓ Wrote index and manifest")

        # Phase 5: Snapshot and diff
        task10 = progress.add_task("Creating snapshot...", total=None)
        snapshot_mgr = SnapshotManager()
        new_snapshot = snapshot_mgr.create_snapshot(
            Path("knowledge_base"), swagger_hash=swagger_hash
        )
        snapshot_mgr.save_snapshot(new_snapshot)
        progress.update(task10, description="✓ Created snapshot")

        # Generate diff and changelog
        old_snapshot = snapshot_mgr.load_latest_snapshot()
        if old_snapshot and old_snapshot.timestamp != new_snapshot.timestamp:
            task11 = progress.add_task("Generating changelog...", total=None)
            differ = Differ()
            diff_report = differ.diff_snapshots(old_snapshot, new_snapshot)

            changelog_writer = ChangelogWriter()
            changelog_writer.append_to_existing(diff_report)
            progress.update(task11, description="✓ Generated changelog")
        else:
            logger.info("No previous snapshot found, skipping diff")


@app.command()
def update(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Incremental update (only fetch changed sources)."""
    setup_logging(verbose)
    console.print("[bold yellow]Incremental update not yet implemented[/bold yellow]")
    console.print("Use 'build' command for now")


@app.command()
def changelog(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Generate changelog from existing snapshots."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    console.print("[bold blue]Generating changelog from snapshots...[/bold blue]\n")

    try:
        snapshot_mgr = SnapshotManager()
        snapshots = snapshot_mgr.list_snapshots()

        if len(snapshots) < 2:
            console.print("[yellow]Need at least 2 snapshots to generate changelog[/yellow]")
            return

        # Generate diffs for all consecutive snapshot pairs
        reports = []
        for i in range(len(snapshots) - 1):
            old = snapshot_mgr.load_snapshot(snapshots[i + 1])
            new = snapshot_mgr.load_snapshot(snapshots[i])

            differ = Differ()
            report = differ.diff_snapshots(old, new)
            reports.append(report)

        # Write changelog
        changelog_writer = ChangelogWriter()
        changelog_writer.write_changelog(reports)

        console.print(f"[green]✓ Generated changelog with {len(reports)} builds[/green]")

    except Exception as e:
        logger.exception("Failed to generate changelog")
        console.print(f"[red]✗ Failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Validate knowledge base integrity."""
    setup_logging(verbose)
    console.print("[bold blue]Validating knowledge base...[/bold blue]\n")
    console.print("[yellow]Validation not yet implemented[/yellow]")


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Show build status and statistics."""
    setup_logging(verbose)
    console.print("[bold blue]Knowledge Base Status[/bold blue]\n")

    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        console.print("[yellow]Knowledge base not found. Run 'build' first.[/yellow]")
        return

    # Count files
    md_files = list(kb_path.rglob("*.md"))
    console.print(f"Pages: {len(md_files)}")

    # Check for manifest
    manifest_path = kb_path / "_manifest.json"
    if manifest_path.exists():
        import json

        manifest = json.loads(manifest_path.read_text())
        console.print(f"Last build: {manifest.get('timestamp', 'Unknown')}")
        console.print(f"Page count: {manifest.get('page_count', 'Unknown')}")

    # Check snapshots
    snapshot_mgr = SnapshotManager()
    snapshots = snapshot_mgr.list_snapshots()
    console.print(f"Snapshots: {len(snapshots)}")


if __name__ == "__main__":
    app()
