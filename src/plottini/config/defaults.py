"""Default configuration values for Plottini.

This module provides default values for all configuration options,
making it easy to create configurations with sensible publication-ready defaults.
"""

from __future__ import annotations

from plottini.config.schema import (
    ExportConfigSchema,
    GrapherConfig,
    PlotConfigSchema,
)

# Parser defaults
DEFAULT_COMMENT_CHARS: list[str] = ["#"]
DEFAULT_DELIMITER: str = "\t"
DEFAULT_ENCODING: str = "utf-8"
DEFAULT_HAS_HEADER: bool = True

# Export defaults
DEFAULT_DPI: int = 300
DEFAULT_EXPORT_FORMAT: str = "png"
DEFAULT_TRANSPARENT: bool = False

# Plot defaults
DEFAULT_CHART_TYPE: str = "line"
DEFAULT_FIGURE_WIDTH: float = 10.0
DEFAULT_FIGURE_HEIGHT: float = 6.0
DEFAULT_SHOW_GRID: bool = True
DEFAULT_SHOW_LEGEND: bool = True


def get_default_config() -> GrapherConfig:
    """Return a GrapherConfig with all default values.

    Returns:
        A GrapherConfig instance with publication-ready defaults.
    """
    return GrapherConfig()


def get_default_plot_config() -> PlotConfigSchema:
    """Return a PlotConfigSchema with default values.

    Returns:
        A PlotConfigSchema instance with publication-ready defaults.
    """
    return PlotConfigSchema()


def get_default_export_config() -> ExportConfigSchema:
    """Return an ExportConfigSchema with default values.

    Returns:
        An ExportConfigSchema instance with publication-ready defaults.
    """
    return ExportConfigSchema()


__all__ = [
    # Constants
    "DEFAULT_COMMENT_CHARS",
    "DEFAULT_DELIMITER",
    "DEFAULT_ENCODING",
    "DEFAULT_HAS_HEADER",
    "DEFAULT_DPI",
    "DEFAULT_EXPORT_FORMAT",
    "DEFAULT_TRANSPARENT",
    "DEFAULT_CHART_TYPE",
    "DEFAULT_FIGURE_WIDTH",
    "DEFAULT_FIGURE_HEIGHT",
    "DEFAULT_SHOW_GRID",
    "DEFAULT_SHOW_LEGEND",
    # Functions
    "get_default_config",
    "get_default_plot_config",
    "get_default_export_config",
]
