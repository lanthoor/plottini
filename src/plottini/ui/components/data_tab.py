"""Data tab composition.

Combines file selector, data preview, transforms, filters,
and alignment into the Data tab.
"""

from __future__ import annotations

from nicegui import ui

from plottini.ui.components.alignment_panel import create_alignment_panel
from plottini.ui.components.data_preview import create_data_preview
from plottini.ui.components.file_selector import create_file_selector
from plottini.ui.components.filter_panel import create_filter_panel
from plottini.ui.components.transform_panel import create_transform_panel
from plottini.ui.state import AppState


def create_data_tab(state: AppState) -> None:
    """Create the Data tab content.

    Args:
        state: Application state
    """
    with ui.row().classes("w-full gap-4"):
        # Left column: File selector and parser settings
        with ui.column().classes("w-1/3"):
            create_file_selector(state)

        # Right column: Data preview
        with ui.column().classes("w-2/3"):
            create_data_preview(state)

    # Bottom section: Transforms, filters, alignment
    with ui.row().classes("w-full gap-4 mt-4"):
        with ui.column().classes("w-1/2"):
            create_transform_panel(state)
        with ui.column().classes("w-1/2"):
            create_filter_panel(state)
            ui.space()
            create_alignment_panel(state)


__all__ = ["create_data_tab"]
