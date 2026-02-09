"""Command-line interface for DocuSynthetic."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from docusynthetic.fetchers import GitHubMDXFetcher, LiveSiteFetcher, OpenAPIFetcher
from docusynthetic.processors import DocumentProcessor
from docusynthetic.utils import Config

app = typer.Typer(
    name="docusynthetic",
    help="Venice AI API documentation scraper and knowledge base generator",
)
console = Console()


@app.command()
def build(
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory for knowledge base",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    github: bool = typer.Option(True, "--github/--no-github", help="Fetch from GitHub"),
    openapi: bool = typer.Option(True, "--openapi/--no-openapi", help="Fetch OpenAPI spec"),
    live_site: bool = typer.Option(
        True, "--live-site/--no-live-site", help="Fetch from live site"
    ),
) -> None:
    """Build the documentation knowledge base from all sources."""
    console.print("[bold blue]DocuSynthetic - Building Knowledge Base[/bold blue]")

    # Load configuration
    config = Config.load(config_file) if config_file else Config()
    config.output_dir = output_dir
    config.fetch_github = github
    config.fetch_openapi = openapi
    config.fetch_live_site = live_site

    # Run async build
    asyncio.run(async_build(config))


async def async_build(config: Config) -> None:
    """Async build function.

    Args:
        config: Configuration object.
    """
    all_documents = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Fetch from GitHub
        if config.fetch_github:
            task = progress.add_task("Fetching from GitHub...", total=None)
            try:
                fetcher = GitHubMDXFetcher(
                    repo_owner=config.github_repo_owner,
                    repo_name=config.github_repo_name,
                    branch=config.github_branch,
                    docs_path=config.github_docs_path,
                )
                docs = await fetcher.fetch()
                all_documents.extend(docs)
                progress.update(task, description=f"✓ Fetched {len(docs)} docs from GitHub")
            except Exception as e:
                progress.update(task, description=f"✗ GitHub fetch failed: {e}")
                console.print(f"[yellow]Warning: GitHub fetch failed: {e}[/yellow]")

        # Fetch from OpenAPI
        if config.fetch_openapi:
            task = progress.add_task("Fetching OpenAPI spec...", total=None)
            try:
                fetcher = OpenAPIFetcher(spec_url=config.openapi_spec_url)
                docs = await fetcher.fetch()
                all_documents.extend(docs)
                progress.update(task, description=f"✓ Fetched {len(docs)} docs from OpenAPI")
            except Exception as e:
                progress.update(task, description=f"✗ OpenAPI fetch failed: {e}")
                console.print(f"[yellow]Warning: OpenAPI fetch failed: {e}[/yellow]")

        # Fetch from live site
        if config.fetch_live_site:
            task = progress.add_task("Fetching from live site...", total=None)
            try:
                fetcher = LiveSiteFetcher(
                    base_url=config.live_site_url, headless=config.live_site_headless
                )
                docs = await fetcher.fetch()
                all_documents.extend(docs)
                progress.update(task, description=f"✓ Fetched {len(docs)} docs from live site")
            except Exception as e:
                progress.update(task, description=f"✗ Live site fetch failed: {e}")
                console.print(f"[yellow]Warning: Live site fetch failed: {e}[/yellow]")

    # Process documents
    console.print(f"\n[bold]Total documents fetched: {len(all_documents)}[/bold]")

    processor = DocumentProcessor(output_dir=config.output_dir)

    # Merge and deduplicate
    console.print("[blue]Merging and deduplicating...[/blue]")
    merged_docs = processor.merge_documents(all_documents)
    console.print(f"[green]✓ Merged to {len(merged_docs)} unique documents[/green]")

    # Generate index
    console.print("[blue]Generating index...[/blue]")
    index = processor.generate_index(merged_docs)
    console.print(f"[green]✓ Generated index with {len(index.categories)} categories[/green]")

    # Detect changes
    console.print("[blue]Detecting changes...[/blue]")
    previous_state = processor.load_previous_state()
    changes = processor.detect_changes(previous_state, merged_docs)
    console.print(f"[green]✓ Detected {len(changes)} changes[/green]")

    # Save everything
    console.print("[blue]Saving knowledge base...[/blue]")
    processor.save_knowledge_base(merged_docs, index)
    processor.save_changelog(changes)
    processor.save_state(merged_docs, index)

    console.print(f"\n[bold green]✓ Knowledge base saved to {config.output_dir}[/bold green]")
    console.print(f"  - Documents: {len(merged_docs)}")
    console.print(f"  - Categories: {len(index.categories)}")
    console.print(f"  - Changes: {len(changes)}")


@app.command()
def diff(
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory containing state",
    ),
) -> None:
    """Show changes from the last build."""
    console.print("[bold blue]DocuSynthetic - Changelog[/bold blue]\n")

    processor = DocumentProcessor(output_dir=output_dir)
    changelog_path = output_dir / "CHANGELOG.md"

    if not changelog_path.exists():
        console.print("[yellow]No changelog found. Run 'build' first.[/yellow]")
        raise typer.Exit(1)

    changelog = changelog_path.read_text(encoding="utf-8")
    console.print(changelog)


@app.command()
def config(
    output: Path = typer.Option(
        Path("./config.json"),
        "--output",
        "-o",
        help="Output path for configuration file",
    ),
) -> None:
    """Generate a default configuration file."""
    cfg = Config()
    cfg.save(output)
    console.print(f"[green]✓ Configuration saved to {output}[/green]")


@app.command()
def install_playwright() -> None:
    """Install Playwright browsers."""
    console.print("[blue]Installing Playwright browsers...[/blue]")
    import subprocess

    subprocess.run(["playwright", "install", "chromium"], check=True)
    console.print("[green]✓ Playwright chromium browser installed[/green]")


if __name__ == "__main__":
    app()
