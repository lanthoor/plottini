"""Configuration schema for Plottini.

This module defines the dataclasses used for complete graph configuration,
including file settings, data transformations, series, and export options.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileConfig:
    """Configuration for a data file.

    Attributes:
        path: Path to the TSV file
        has_header: Whether the file has a header row
        comment_chars: Characters that indicate comment lines
        delimiter: Column delimiter character
        encoding: File encoding
    """

    path: Path
    has_header: bool = True
    comment_chars: list[str] = field(default_factory=lambda: ["#"])
    delimiter: str = "\t"
    encoding: str = "utf-8"


@dataclass
class AlignmentConfig:
    """Configuration for multi-file alignment.

    Attributes:
        enabled: Whether alignment is enabled
        column: Column name to align on
    """

    enabled: bool = False
    column: str = ""


@dataclass
class DerivedColumnConfig:
    """Configuration for a derived column.

    Attributes:
        name: Name for the new column
        expression: Mathematical expression to evaluate
    """

    name: str
    expression: str


@dataclass
class FilterConfig:
    """Configuration for row filtering.

    Attributes:
        column: Column name to filter on
        min: Minimum value (inclusive), or None for no lower bound
        max: Maximum value (inclusive), or None for no upper bound
    """

    column: str
    min: float | None = None
    max: float | None = None


@dataclass
class SeriesConfigSchema:
    """Configuration for a single data series in TOML format.

    This uses simpler field names than the internal SeriesConfig
    for a more user-friendly TOML format.

    Attributes:
        x: Column name for x-axis values
        y: Column name for y-axis values
        label: Legend label for this series
        color: Color for this series
        line_style: Line style ('-', '--', '-.', ':')
        marker: Marker style ('o', 's', '^', etc.)
        line_width: Width of the line
        use_secondary_y: Whether to plot on secondary y-axis
        source_file_index: Index of source file
    """

    x: str
    y: str
    label: str | None = None
    color: str | None = None
    line_style: str = "-"
    marker: str | None = None
    line_width: float = 1.5
    use_secondary_y: bool = False
    source_file_index: int = 0


@dataclass
class PlotConfigSchema:
    """Configuration for plot appearance in TOML format.

    Attributes:
        type: Chart type ('line', 'bar', 'pie', etc.)
        title: Plot title
        x_label: Label for x-axis
        y_label: Label for y-axis
        y2_label: Label for secondary y-axis
        figure_width: Figure width in inches
        figure_height: Figure height in inches
        show_grid: Whether to show grid lines
        show_legend: Whether to show legend
        legend_loc: Legend location ('best', 'upper left', 'upper right', etc.)
        # Chart-type specific options
        bar_width: Bar width for bar charts (0.1-1.0)
        histogram_bins: Number of bins for histograms
        histogram_density: Show density instead of counts
        scatter_size: Marker size for scatter plots
        area_alpha: Transparency for area charts (0.0-1.0)
        pie_explode: Explode factor for pie charts (0.0-0.5)
        pie_show_labels: Show labels on pie chart
        box_show_outliers: Show outliers in box plots
        violin_show_median: Show median line in violin plots
        step_where: Step alignment ('pre', 'mid', 'post')
        errorbar_capsize: Cap size for error bars
    """

    type: str = "line"
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    y2_label: str = ""
    figure_width: float = 10.0
    figure_height: float = 6.0
    show_grid: bool = True
    show_legend: bool = True
    legend_loc: str = "best"
    # Chart-type specific options
    bar_width: float = 0.8
    histogram_bins: int = 20
    histogram_density: bool = False
    scatter_size: int = 50
    area_alpha: float = 0.5
    pie_explode: float = 0.0
    pie_show_labels: bool = True
    box_show_outliers: bool = True
    violin_show_median: bool = True
    step_where: str = "mid"
    errorbar_capsize: int = 3


@dataclass
class ExportConfigSchema:
    """Configuration for export settings in TOML format.

    Attributes:
        format: Export format ('png', 'svg', 'pdf', 'eps')
        dpi: Resolution for raster formats
        transparent: Whether to use transparent background
    """

    format: str = "png"
    dpi: int = 300
    transparent: bool = False


@dataclass
class GrapherConfig:
    """Complete configuration for a graph.

    This is the top-level configuration object that contains all
    settings for loading data, transforming it, and creating plots.

    Attributes:
        files: List of file configurations
        alignment: Optional alignment configuration
        derived_columns: List of derived column configurations
        filters: List of filter configurations
        series: List of series configurations
        plot: Plot appearance configuration
        export: Export settings
    """

    files: list[FileConfig] = field(default_factory=list)
    alignment: AlignmentConfig | None = None
    derived_columns: list[DerivedColumnConfig] = field(default_factory=list)
    filters: list[FilterConfig] = field(default_factory=list)
    series: list[SeriesConfigSchema] = field(default_factory=list)
    plot: PlotConfigSchema = field(default_factory=PlotConfigSchema)
    export: ExportConfigSchema = field(default_factory=ExportConfigSchema)


__all__ = [
    "FileConfig",
    "AlignmentConfig",
    "DerivedColumnConfig",
    "FilterConfig",
    "SeriesConfigSchema",
    "PlotConfigSchema",
    "ExportConfigSchema",
    "GrapherConfig",
]
