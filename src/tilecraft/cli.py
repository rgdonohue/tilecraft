"""
Command-line interface for Tilecraft.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install

from tilecraft.models.config import (
    BoundingBox,
    FeatureConfig,
    PaletteConfig,  
    OutputConfig,
    TilecraftConfig,
)
from tilecraft.core.pipeline import TilecraftPipeline
from tilecraft import __version__

# Install rich traceback handler
install(show_locals=True)

console = Console()


def print_banner():
    """Print the Tilecraft banner."""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                         TILECRAFT                            ║
║              AI-Assisted Vector Tile Generation              ║
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


@click.command()
@click.option(
    "--bbox", 
    required=True,
    callback=validate_bbox,
    help="Bounding box as 'west,south,east,north' (e.g., '-109.2,36.8,-106.8,38.5')"
)
@click.option(
    "--features",
    required=True, 
    callback=validate_features,
    help="Comma-separated feature types (e.g., 'rivers,forest,water')"
)
@click.option(
    "--palette",
    required=True,
    help="Style palette mood (e.g., 'subalpine dusk', 'desert sunset')"
)
@click.option(
    "--output",
    default="output",
    type=click.Path(),
    help="Output directory path (default: 'output')"
)
@click.option(
    "--name",
    default=None,
    help="Project name for file naming (auto-generated if not provided)"
)
@click.option(
    "--ai-provider",
    default="openai",
    type=click.Choice(["openai", "anthropic"]),
    help="AI provider to use (default: openai)"
)
@click.option(
    "--min-zoom",
    default=0,
    type=click.IntRange(0, 24),
    help="Minimum zoom level (default: 0)"
)
@click.option(
    "--max-zoom", 
    default=14,
    type=click.IntRange(0, 24),
    help="Maximum zoom level (default: 14)"
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable caching (re-download OSM data)"
)
@click.option(
    "--preview",
    is_flag=True,
    help="Generate preview after tile creation"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Verbose output"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Quiet mode (minimal output)"
)
@click.version_option(version=__version__)
def main(
    bbox: BoundingBox,
    features: FeatureConfig,
    palette: str,
    output: str,
    name: Optional[str],
    ai_provider: str,
    min_zoom: int,
    max_zoom: int,
    no_cache: bool,
    preview: bool,
    verbose: bool,
    quiet: bool,
):
    """
    Tilecraft: AI-Assisted CLI Tool for Vector Tile Generation from OSM
    
    Generate beautiful vector tiles and MapLibre styles from OpenStreetMap data
    using AI-assisted schema generation and style design.
    
    Example:
        tilecraft --bbox "-109.2,36.8,-106.8,38.5" --features "rivers,forest,water" --palette "subalpine dusk"
    """
    if not quiet:
        print_banner()
    
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
            ai={"provider": ai_provider},
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
            # TODO: Implement preview generation
            console.print("[yellow]Preview generation not yet implemented[/yellow]")

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
    table.add_row("AI Provider", config.ai.provider)
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
        border_style="green"
    )
    console.print(panel)


if __name__ == "__main__":
    main() 