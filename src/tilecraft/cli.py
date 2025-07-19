"""
Command-line interface for Tilecraft.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.traceback import install

from tilecraft import __version__
from tilecraft.core.pipeline import TilecraftPipeline
from tilecraft.models.config import (
    BoundingBox,
    FeatureConfig,
    OutputConfig,
    PaletteConfig,
    TilecraftConfig,
)

# Install rich traceback handler
install(show_locals=True)

console = Console()


def print_banner():
    """Print the Tilecraft banner."""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                         TILECRAFT                            ║
║               OSM Vector Tile Generation                     ║
║                         Version {__version__}                          ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


def validate_bbox(ctx, param, value):
    """Validate bounding box parameter."""
    if value is None:
        return None
    try:
        return BoundingBox.from_string(value)
    except ValueError as e:
        raise click.BadParameter(str(e))


def validate_features(ctx, param, value):
    """Validate features parameter."""
    if value is None:
        return None
    try:
        return FeatureConfig(types=value)
    except ValueError as e:
        raise click.BadParameter(f"Invalid feature types: {e}")


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__)
def cli(ctx):
    """Tilecraft: Streamlined CLI for OSM Vector Tile Generation"""
    if ctx.invoked_subcommand is None:
        # Default behavior - show help
        click.echo(ctx.get_help())


@cli.command("generate")
@click.pass_context
@click.option(
    "--bbox",
    required=True,
    callback=validate_bbox,
    help="Bounding box as 'west,south,east,north' (e.g., '-109.2,36.8,-106.8,38.5')",
)
@click.option(
    "--features",
    required=True,
    callback=validate_features,
    help="Comma-separated feature types (e.g., 'rivers,forest,water')",
)
@click.option(
    "--palette",
    required=True,
    help="Style palette mood (e.g., 'subalpine dusk', 'desert sunset')",
)
@click.option(
    "--output",
    default="output",
    type=click.Path(),
    help="Output directory path (default: 'output')",
)
@click.option(
    "--name",
    default=None,
    help="Project name for file naming (auto-generated if not provided)",
)
@click.option(
    "--min-zoom",
    default=0,
    type=click.IntRange(0, 24),
    help="Minimum zoom level (default: 0)",
)
@click.option(
    "--max-zoom",
    default=14,
    type=click.IntRange(0, 24),
    help="Maximum zoom level (default: 14)",
)
@click.option("--no-cache", is_flag=True, help="Disable caching (re-download OSM data)")
@click.option("--preview", is_flag=True, help="Generate preview after tile creation")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (minimal output)")
def generate(
    ctx,
    bbox: BoundingBox,
    features: FeatureConfig,
    palette: str,
    output: str,
    name: Optional[str],
    min_zoom: int,
    max_zoom: int,
    no_cache: bool,
    preview: bool,
    verbose: bool,
    quiet: bool,
):
    """
    Tilecraft: Streamlined CLI for OSM Vector Tile Generation

    Generate beautiful vector tiles and MapLibre styles from OpenStreetMap data
    with smart caching and optimized feature extraction.

    Example:
        tilecraft --bbox "-109.2,36.8,-106.8,38.5" --features "rivers,forest,water" --palette "subalpine dusk"
    """
    if not quiet:
        print_banner()

    # Quick dependency check before starting
    from tilecraft.utils.system_check import verify_system_dependencies
    if not verify_system_dependencies(verbose=False):
        console.print("[red]❌ Critical dependencies missing![/red]")
        console.print("Run '[cyan]tilecraft check --fix[/cyan]' for installation instructions")
        console.print("Or continue anyway with missing dependencies...")
        
        if not click.confirm("Continue despite missing dependencies?", default=False):
            console.print("[yellow]Aborted. Install dependencies and try again.[/yellow]")
            sys.exit(1)

    # Validate zoom levels
    if max_zoom < min_zoom:
        console.print("[red]Error: Maximum zoom must be >= minimum zoom[/red]")
        sys.exit(1)

    # Create configuration
    try:
        config = TilecraftConfig(
            bbox=bbox,
            features=features,
            palette=PaletteConfig(name=palette),
            output=OutputConfig(base_dir=Path(output), name=name),
            tiles={"min_zoom": min_zoom, "max_zoom": max_zoom},
            cache_enabled=not no_cache,
            verbose=verbose,
        )
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)

    # Display configuration summary
    if not quiet:
        display_config_summary(config)

    # Run the pipeline
    try:
        pipeline = TilecraftPipeline(config)

        if quiet:
            # Simple progress for quiet mode
            with console.status("[bold green]Processing..."):
                result = pipeline.run()
        else:
            # Detailed progress with steps
            result = run_with_progress(pipeline)

        # Display results
        if not quiet:
            display_results(result, config)

        if preview:
            console.print("\n[bold blue]Generating preview...[/bold blue]")
            try:
                from tilecraft.utils.preview import PreviewGenerator
                
                preview_generator = PreviewGenerator(config.output.base_dir / "preview")
                preview_path = preview_generator.generate_html_preview(
                    result["tiles"], result["style"], config.bbox
                )
                
                console.print(f"[green]✓ Preview generated: {preview_path}[/green]")
                console.print(f"[blue]To view preview:[/blue]")
                console.print(f"[blue]1. cd {preview_path.parent}[/blue]")
                console.print(f"[blue]2. python start_tile_server.py[/blue]")
                console.print(f"[blue]3. Open http://localhost:8080[/blue]")
                
            except Exception as e:
                console.print(f"[red]Preview generation failed: {e}[/red]")
                if verbose:
                    console.print_exception()

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def display_config_summary(config: TilecraftConfig):
    """Display configuration summary table."""
    table = Table(title="Configuration", style="cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Bounding Box", config.bbox.to_string())
    table.add_row("Features", ", ".join([f.value for f in config.features.types]))
    table.add_row("Palette", config.palette.name)
    table.add_row("Output Directory", str(config.output.base_dir))
    table.add_row("Zoom Levels", f"{config.tiles.min_zoom} - {config.tiles.max_zoom}")
    table.add_row("Cache Enabled", "Yes" if config.cache_enabled else "No")

    console.print("\n")
    console.print(table)
    console.print()


def run_with_progress(pipeline: TilecraftPipeline):
    """Run pipeline with detailed progress display."""
    steps = [
        ("Downloading OSM data", "download"),
        ("Extracting features", "extract"),
        ("Generating AI schema", "schema"),
        ("Creating vector tiles", "tiles"),
        ("Generating style", "style"),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        result = {}
        for description, step_name in steps:
            task = progress.add_task(description, total=None)

            try:
                if step_name == "download":
                    result["osm_data"] = pipeline.download_osm_data()
                elif step_name == "extract":
                    result["features"] = pipeline.extract_features(result["osm_data"])
                elif step_name == "schema":
                    result["schema"] = pipeline.generate_schema()
                elif step_name == "tiles":
                    result["tiles"] = pipeline.generate_tiles(result["features"])
                elif step_name == "style":
                    result["style"] = pipeline.generate_style(result["schema"])

                progress.update(task, completed=1, total=1)

            except Exception as e:
                progress.update(task, description=f"[red]{description} - Failed[/red]")
                raise e

    return result


def display_results(result, config: TilecraftConfig):
    """Display processing results."""
    console.print("\n[bold green]✓ Processing completed successfully![/bold green]")

    # Create results panel
    results_text = f"""
Output Directory: {config.output.base_dir}
├── tiles/        Vector tiles (.mbtiles)
├── styles/       MapLibre style JSON
├── data/         Extracted GeoJSON files
└── cache/        Cached OSM data

Files generated:
• Vector tiles: {config.output.tiles_dir}
• Style JSON: {config.output.styles_dir}
• Feature data: {config.output.data_dir}
"""

    panel = Panel(
        results_text.strip(),
        title="[bold green]Results[/bold green]",
        border_style="green",
    )
    console.print(panel)


@cli.command("check")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed dependency information")
@click.option("--fix", is_flag=True, help="Show installation commands for missing dependencies")
def check_system(verbose: bool, fix: bool):
    """Check system dependencies and installation."""
    from tilecraft.utils.system_check import SystemVerifier
    
    console.print("🔍 [bold blue]Checking Tilecraft Dependencies[/bold blue]\n")
    
    verifier = SystemVerifier()
    verifier.verify_all_dependencies()
    
    # Create results table
    table = Table(title="System Dependencies")
    table.add_column("Dependency", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Version")
    if verbose:
        table.add_column("Path")
    
    for name, result in verifier.results.items():
        status = "✅ Available" if result.available else "❌ Missing"
        status_style = "green" if result.available else "red"
        version = result.version or "unknown"
        
        row = [name, f"[{status_style}]{status}[/{status_style}]", version]
        if verbose:
            row.append(result.path or "N/A")
        
        table.add_row(*row)
    
    console.print(table)
    
    # Show summary
    summary = verifier.get_summary()
    
    if summary["all_available"]:
        console.print("\n🎉 [bold green]All dependencies are available![/bold green]")
        console.print("✅ Tilecraft is ready to use.")
    else:
        console.print(f"\n⚠️  [yellow]{summary['missing_dependencies']} dependencies missing[/yellow]")
        
        if summary["critical_missing"]:
            console.print(f"🚨 [red]Critical missing: {', '.join(summary['critical_missing'])}[/red]")
            console.print("❌ Tilecraft will not function without these dependencies.")
        
        # Show installation help
        if fix:
            console.print("\n📋 [bold]Installation Instructions:[/bold]")
            for name, result in verifier.results.items():
                if not result.available and result.installation_help:
                    console.print(f"\n[bold]{name}:[/bold]")
                    console.print(result.installation_help)
    
    # Show errors if verbose
    if verbose:
        errors = [(name, result.error) for name, result in verifier.results.items() 
                 if not result.available and result.error]
        if errors:
            console.print("\n🐛 [bold red]Error Details:[/bold red]")
            for name, error in errors:
                console.print(f"• [red]{name}[/red]: {error}")
    
    # Exit with error code if critical dependencies missing
    if summary["critical_missing"]:
        console.print("\n💡 [yellow]Run 'tilecraft check --fix' for installation instructions[/yellow]")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
