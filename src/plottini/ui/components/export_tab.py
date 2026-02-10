"""Export tab composition.

Contains the plot preview and export panel.
"""

from __future__ import annotations

from nicegui import ui

from plottini.ui.components.export_panel import create_export_panel
from plottini.ui.components.plot_preview import create_plot_preview
from plottini.ui.state import AppState


def create_export_tab(state: AppState) -> None:
    """Create the Export tab content.

    Args:
        state: Application state
    """
    with ui.row().classes("w-full h-full gap-4"):
        # Left: Preview
        with ui.column().classes("w-2/3"):
            create_plot_preview(state)

        # Right: Export options
        with ui.column().classes("w-1/3"):
            create_export_panel(state)


__all__ = ["create_export_tab"]
