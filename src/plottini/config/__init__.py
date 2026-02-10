"""Configuration management for Plottini.

This module provides configuration loading, saving, and schema definitions
for complete graph configuration.
"""

from plottini.config.defaults import (
    DEFAULT_CHART_TYPE,
    DEFAULT_COMMENT_CHARS,
    DEFAULT_DELIMITER,
    DEFAULT_DPI,
    DEFAULT_ENCODING,
    DEFAULT_EXPORT_FORMAT,
    DEFAULT_FIGURE_HEIGHT,
    DEFAULT_FIGURE_WIDTH,
    DEFAULT_HAS_HEADER,
    DEFAULT_SHOW_GRID,
    DEFAULT_SHOW_LEGEND,
    DEFAULT_TRANSPARENT,
    get_default_config,
    get_default_export_config,
    get_default_plot_config,
)
from plottini.config.loader import ConfigError, load_config, save_config
from plottini.config.schema import (
    AlignmentConfig,
    DerivedColumnConfig,
    ExportConfigSchema,
    FileConfig,
    FilterConfig,
    GrapherConfig,
    PlotConfigSchema,
    SeriesConfigSchema,
)

__all__ = [
    # Schema
    "FileConfig",
    "AlignmentConfig",
    "DerivedColumnConfig",
    "FilterConfig",
    "SeriesConfigSchema",
    "PlotConfigSchema",
    "ExportConfigSchema",
    "GrapherConfig",
    # Loader
    "ConfigError",
    "load_config",
    "save_config",
    # Defaults
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
    "get_default_config",
    "get_default_plot_config",
    "get_default_export_config",
]
