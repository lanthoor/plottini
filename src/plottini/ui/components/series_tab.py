"""Series tab composition.

Contains the series configuration panel.
"""

from __future__ import annotations

from plottini.ui.components.series_config import create_series_config
from plottini.ui.state import AppState


def create_series_tab(state: AppState) -> None:
    """Create the Series tab content.

    Args:
        state: Application state
    """
    create_series_config(state)


__all__ = ["create_series_tab"]
