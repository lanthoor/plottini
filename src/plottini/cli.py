"""Command-line interface for Plottini."""

import click


@click.group(invoke_without_command=True)
@click.option("--port", default=8050, help="Port for web UI (default: 8050)")
@click.option("--no-open", is_flag=True, help="Do not open browser automatically")
@click.option("--config", type=click.Path(exists=True), help="Load configuration file")
@click.pass_context
def cli(ctx: click.Context, port: int, no_open: bool, config: str | None) -> None:
    """Plottini - User-friendly graph builder for publication-quality plots.

    Start the web UI to interactively create graphs from TSV data files.
    """
    if ctx.invoked_subcommand is None:
        # Start UI mode (to be implemented)
        click.echo(f"Starting Plottini on port {port}...")
        click.echo("UI functionality coming soon!")
        if config:
            click.echo(f"Loading config from: {config}")
        # from plottini.ui.app import start_app
        # start_app(port=port, open_browser=not no_open, config_file=config)


@cli.command()
@click.option(
    "--config", required=True, type=click.Path(exists=True), help="Configuration file (TOML format)"
)
@click.option("--output", required=True, type=click.Path(), help="Output file path")
@click.option(
    "--format",
    type=click.Choice(["png", "svg", "pdf", "eps"], case_sensitive=False),
    help="Output format (overrides config file)",
)
@click.option("--dpi", type=int, help="DPI for raster formats (overrides config file)")
def render(config: str, output: str, format: str | None, dpi: int | None) -> None:
    """Render graph without UI (expert mode).

    Load a configuration file and directly export the graph to a file.
    Useful for batch processing and automation.
    """
    click.echo(f"Rendering graph from config: {config}")
    click.echo(f"Output: {output}")
    if format:
        click.echo(f"Format: {format}")
    if dpi:
        click.echo(f"DPI: {dpi}")
    click.echo("Render functionality coming soon!")
    # from plottini.config.loader import load_config
    # from plottini.core.plotter import Plotter
    # from plottini.core.exporter import Exporter
    # cfg = load_config(config)
    # ... render and export
    # click.echo(f"Graph exported to {output}")


@cli.command()
def version() -> None:
    """Show version information."""
    from plottini import __version__

    click.echo(f"Plottini version {__version__}")


if __name__ == "__main__":
    cli()
