"""Settings tab composition.

Contains the chart configuration panel.
"""

from __future__ import annotations

from plottini.ui.components.chart_config import create_chart_config
from plottini.ui.state import AppState


def create_settings_tab(state: AppState) -> None:
    """Create the Settings tab content.

    Args:
        state: Application state
    """
    create_chart_config(state)


__all__ = ["create_settings_tab"]
