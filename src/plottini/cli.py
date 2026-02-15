"""Command-line interface for Plottini."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click


@click.group(invoke_without_command=True)
@click.option("--port", default=8501, help="Port for web UI (default: 8501)")
@click.option("--no-open", is_flag=True, help="Do not open browser automatically")
@click.pass_context
def cli(ctx: click.Context, port: int, no_open: bool) -> None:
    """Plottini - User-friendly graph builder for publication-quality plots.

    Start the web UI to interactively create graphs from TSV data files.
    """
    if ctx.invoked_subcommand is None:
        # Start Streamlit UI
        _start_streamlit(port=port, open_browser=not no_open)


def _start_streamlit(port: int = 8501, open_browser: bool = True) -> None:
    """Start the Streamlit application.

    Args:
        port: Port to run on
        open_browser: Whether to open browser automatically
    """
    # Get path to app.py
    app_path = Path(__file__).parent / "ui" / "app.py"

    # Build command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.headless",
        "true" if not open_browser else "false",
    ]

    if not open_browser:
        cmd.extend(["--browser.serverAddress", "localhost"])

    click.echo(f"Starting Plottini on http://localhost:{port}")
    click.echo("Press Ctrl+C to stop")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\nStopping Plottini...")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error starting Streamlit: {e}", err=True)
        raise SystemExit(1) from None


@cli.command()
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="Configuration file (TOML format)",
)
@click.option("--output", required=True, type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "fmt",  # Rename to avoid shadowing builtin
    type=click.Choice(["png", "svg", "pdf", "eps"], case_sensitive=False),
    help="Output format (overrides config file)",
)
@click.option("--dpi", type=int, help="DPI for raster formats (overrides config file)")
def render(config: str, output: str, fmt: str | None, dpi: int | None) -> None:
    """Render graph without UI (headless mode).

    Load a configuration file and directly export the graph to a file.
    Useful for batch processing and automation.
    """
    from plottini.config.loader import load_config
    from plottini.core.exporter import ExportConfig, Exporter, ExportFormat
    from plottini.core.parser import ParserConfig, TSVParser
    from plottini.core.plotter import ChartType, PlotConfig, Plotter, SeriesConfig

    click.echo(f"Loading configuration from: {config}")
    cfg = load_config(config)

    # Parse data files using parse_blocks for multi-block support
    parser_config = ParserConfig(
        has_header=cfg.files[0].has_header if cfg.files else True,
        comment_chars=cfg.files[0].comment_chars if cfg.files else ["#"],
        delimiter=cfg.files[0].delimiter if cfg.files else "\t",
    )
    parser = TSVParser(parser_config)

    dataframes = []
    for file_cfg in cfg.files:
        click.echo(f"  Loading: {file_cfg.path}")
        file_dfs = parser.parse_blocks(file_cfg.path)
        n_blocks = len(file_dfs)
        if n_blocks > 1:
            click.echo(f"    Found {n_blocks} data blocks")
        dataframes.extend(file_dfs)

    if not dataframes:
        click.echo("Error: No data files specified in config", err=True)
        raise SystemExit(1)

    # Apply derived columns
    for dc in cfg.derived_columns:
        for df in dataframes:
            if dc.name and dc.expression:
                try:
                    df.add_derived_column(dc.name, dc.expression)
                except Exception as e:
                    click.echo(
                        f"Warning: Could not create derived column '{dc.name}': {e}", err=True
                    )

    # Apply filters
    for f in cfg.filters:
        if f.column:
            dataframes = [df.filter_rows(f.column, f.min, f.max) for df in dataframes]

    # Convert series config
    series = [
        SeriesConfig(
            x_column=s.x,
            y_column=s.y,
            label=s.label,
            color=s.color,
            line_style=s.line_style,
            marker=s.marker,
            line_width=s.line_width,
            use_secondary_y=s.use_secondary_y,
            source_file_index=s.source_file_index,
        )
        for s in cfg.series
    ]

    if not series:
        click.echo("Error: No series defined in config", err=True)
        raise SystemExit(1)

    # Determine chart type
    chart_type = ChartType.LINE
    for ct in ChartType:
        if ct.value == cfg.plot.type:
            chart_type = ct
            break

    # Create plot config
    plot_config = PlotConfig(
        chart_type=chart_type,
        title=cfg.plot.title,
        x_label=cfg.plot.x_label,
        y_label=cfg.plot.y_label,
        y2_label=cfg.plot.y2_label,
        figure_width=cfg.plot.figure_width,
        figure_height=cfg.plot.figure_height,
        show_grid=cfg.plot.show_grid,
        show_legend=cfg.plot.show_legend,
    )

    # Create plotter and render
    click.echo("Rendering plot...")
    plotter = Plotter(plot_config)
    fig = plotter.create_figure(dataframes, series)

    # Determine export format
    export_fmt = ExportFormat.PNG
    if fmt:
        export_fmt = ExportFormat.from_string(fmt)
    elif cfg.export.format:
        export_fmt = ExportFormat.from_string(cfg.export.format)

    # Determine DPI
    export_dpi = dpi if dpi else cfg.export.dpi

    # Export
    exporter = Exporter()
    export_config = ExportConfig(
        format=export_fmt,
        dpi=export_dpi,
        transparent=cfg.export.transparent,
    )

    output_path = exporter.export(fig, Path(output), export_config)
    click.echo(f"Graph exported to: {output_path}")


@cli.command()
def version() -> None:
    """Show version information."""
    from plottini import __version__

    click.echo(f"Plottini version {__version__}")


if __name__ == "__main__":
    cli()
