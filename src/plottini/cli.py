"""Command-line interface for Plottini."""

from __future__ import annotations

import click


@click.group(invoke_without_command=True)
@click.option("--port", default=None, type=int, help="Port number for the app")
@click.pass_context
def cli(ctx: click.Context, port: int | None) -> None:
    """Plottini - User-friendly graph builder for publication-quality plots.

    Start the desktop app to interactively create graphs from TSV data files.
    """
    if ctx.invoked_subcommand is None:
        # Start desktop app with PyWebView
        from plottini.desktop import start_desktop

        start_desktop(port)


@cli.command()
def version() -> None:
    """Show version information."""
    from plottini import __version__

    click.echo(f"Plottini version {__version__}")


if __name__ == "__main__":
    cli()
