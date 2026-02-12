"""CLI for Venice KB Collector using Typer."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from venice_kb import __version__
from venice_kb.config import KB_OUTPUT_DIR, SNAPSHOT_DIR
from venice_kb.utils.logging import logger, setup_logging
from venice_kb.diffing.snapshot import get_latest_snapshot, list_snapshots, load_snapshot
from venice_kb.diffing.differ import diff_snapshots
from venice_kb.diffing.changelog_writer import write_changelog

app = typer.Typer(
    name="venice-kb",
    help="Venice KB Collector - Pull and track Venice AI API documentation",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"Venice KB Collector v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Venice KB Collector - Documentation knowledge base builder."""
    pass


@app.command()
def build(
    output: Path = typer.Option(
        KB_OUTPUT_DIR,
        "--output",
        "-o",
        help="Output directory for knowledge base",
    ),
    snapshot_dir: Path = typer.Option(
        SNAPSHOT_DIR,
        "--snapshot-dir",
        "-s",
        help="Directory to store snapshots",
    ),
    sources: str = typer.Option(
        "all",
        "--sources",
        help="Comma-separated sources: github,openapi,web,api",
    ),
    force_refresh: bool = typer.Option(
        False,
        "--force-refresh",
        "-f",
        help="Bypass cache and re-fetch everything",
    ),
    skip_llm: bool = typer.Option(
        False,
        "--skip-llm",
        help="Skip LLM-assisted processing",
    ),
    no_changelog: bool = typer.Option(
        False,
        "--no-changelog",
        help="Skip changelog generation",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Log level (DEBUG, INFO, WARNING, ERROR)",
    ),
):
    """Build the full knowledge base from all sources."""
    setup_logging(log_level)
    console.print(f"[bold blue]Building knowledge base...[/bold blue]")
    console.print(f"Output: {output}")
    console.print(f"Snapshots: {snapshot_dir}")
    console.print(f"Sources: {sources}")
    
    # TODO: Implement full build logic
    # This is a placeholder showing the structure
    console.print("[yellow]Note: Full build implementation pending[/yellow]")
    console.print("[green]✓[/green] Build completed successfully (stub)")


@app.command()
def update(
    output: Path = typer.Option(
        KB_OUTPUT_DIR,
        "--output",
        "-o",
        help="Output directory for knowledge base",
    ),
    snapshot_dir: Path = typer.Option(
        SNAPSHOT_DIR,
        "--snapshot-dir",
        "-s",
        help="Directory to store snapshots",
    ),
):
    """Incremental update - only fetch and process changed content."""
    console.print("[bold blue]Running incremental update...[/bold blue]")
    console.print("[yellow]Note: Update implementation pending[/yellow]")


@app.command()
def changelog(
    snapshot_dir: Path = typer.Option(
        SNAPSHOT_DIR,
        "--snapshot-dir",
        "-s",
        help="Directory containing snapshots",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Where to write CHANGELOG (default: <kb>/CHANGELOG.md)",
    ),
    last_n: int = typer.Option(
        5,
        "--last-n",
        "-n",
        help="Compare last N builds",
    ),
    format: str = typer.Option(
        "both",
        "--format",
        help="Output format: md, json, or both",
    ),
    severity: str = typer.Option(
        "all",
        "--severity",
        help="Filter by severity: breaking, important, info, cosmetic, all",
    ),
):
    """Generate changelog from snapshots without rebuilding."""
    console.print(f"[bold blue]Generating changelog from snapshots...[/bold blue]")
    
    snapshots = list_snapshots(snapshot_dir)
    if len(snapshots) < 2:
        console.print(
            f"[yellow]Need at least 2 snapshots to generate changelog. Found: {len(snapshots)}[/yellow]"
        )
        return
    
    # Limit to last_n snapshots
    snapshots = snapshots[:last_n]
    
    console.print(f"Processing {len(snapshots)} snapshots...")
    
    # Generate diff reports
    reports = []
    for i in range(len(snapshots) - 1):
        new_snap = load_snapshot(snapshots[i])
        old_snap = load_snapshot(snapshots[i + 1])
        
        console.print(f"Diffing {old_snap.snapshot_id} → {new_snap.snapshot_id}")
        report = diff_snapshots(old_snap, new_snap)
        reports.append(report)
    
    # Write changelog
    if output is None:
        output = KB_OUTPUT_DIR / "CHANGELOG.md"
    
    write_changelog(reports, output, format=format)
    console.print(f"[green]✓[/green] Changelog written to {output}")


@app.command()
def diff(
    old: Path = typer.Option(..., "--old", help="Path to old snapshot JSON"),
    new: Path = typer.Option(..., "--new", help="Path to new snapshot JSON"),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Where to write diff report",
    ),
):
    """Compare two specific snapshots."""
    console.print(f"[bold blue]Comparing snapshots...[/bold blue]")
    
    old_snap = load_snapshot(old)
    new_snap = load_snapshot(new)
    
    report = diff_snapshots(old_snap, new_snap)
    
    console.print(f"\n[bold]Summary:[/bold] {report.summary}")
    console.print(f"Breaking: {len(report.breaking_changes)}")
    console.print(f"Important: {len(report.important_changes)}")
    console.print(f"Informational: {len(report.informational_changes)}")
    console.print(f"Cosmetic: {len(report.cosmetic_changes)}")
    
    if output:
        write_changelog([report], output, format="both")
        console.print(f"[green]✓[/green] Report written to {output}")


@app.command()
def validate(
    kb_path: Path = typer.Option(
        KB_OUTPUT_DIR,
        "--kb-path",
        help="Path to knowledge_base/ directory",
    ),
):
    """Validate an existing knowledge base."""
    console.print(f"[bold blue]Validating knowledge base: {kb_path}[/bold blue]")
    console.print("[yellow]Note: Validation implementation pending[/yellow]")


@app.command()
def status(
    kb_path: Path = typer.Option(
        KB_OUTPUT_DIR,
        "--kb-path",
        help="Path to knowledge_base/ directory",
    ),
    snapshot_dir: Path = typer.Option(
        SNAPSHOT_DIR,
        "--snapshot-dir",
        "-s",
        help="Directory containing snapshots",
    ),
):
    """Show current state - last build time, source versions, page count."""
    console.print("[bold blue]Venice KB Collector Status[/bold blue]\n")
    
    # Check for latest snapshot
    latest = get_latest_snapshot(snapshot_dir)
    
    if latest:
        table = Table(title="Latest Build")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Snapshot ID", latest.snapshot_id)
        table.add_row("Generated At", latest.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
        table.add_row("Total Pages", str(len(latest.page_manifest)))
        
        # Source versions
        for key, value in latest.source_versions.items():
            table.add_row(f"Source: {key}", str(value))
        
        console.print(table)
        
        # Token stats
        total_tokens = sum(m.token_count for m in latest.page_manifest.values())
        avg_tokens = total_tokens // len(latest.page_manifest) if latest.page_manifest else 0
        
        console.print(f"\n[bold]Token Statistics:[/bold]")
        console.print(f"  Total tokens: {total_tokens:,}")
        console.print(f"  Average tokens per page: {avg_tokens:,}")
    else:
        console.print("[yellow]No snapshots found. Run 'venice-kb build' first.[/yellow]")
    
    # List all snapshots
    snapshots = list_snapshots(snapshot_dir)
    if snapshots:
        console.print(f"\n[bold]Available Snapshots:[/bold] {len(snapshots)}")
        for snap_path in snapshots[:5]:
            console.print(f"  • {snap_path.name}")
        if len(snapshots) > 5:
            console.print(f"  ... and {len(snapshots) - 5} more")


if __name__ == "__main__":
    app()
