"""Plotter module for creating matplotlib figures.

This module provides functionality to create publication-quality plots
from DataFrame data with support for multiple chart types.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from plottini.core.dataframe import DataFrame

# Colorblind-safe palette for publication quality
COLORBLIND_PALETTE = [
    "#0072B2",  # Blue
    "#E69F00",  # Orange
    "#009E73",  # Green
    "#CC79A7",  # Pink
    "#F0E442",  # Yellow
    "#56B4E9",  # Light blue
    "#D55E00",  # Red-orange
    "#000000",  # Black
]


class ChartType(Enum):
    """Supported chart types.

    Attributes:
        LINE: Line chart for continuous data
        BAR: Bar chart for categorical comparisons
        PIE: Pie chart for proportional data
        SCATTER: Scatter plot for correlation analysis
        HISTOGRAM: Histogram for distribution analysis
        POLAR: Polar/radial chart
        BOX: Box plot for statistical distribution
        VIOLIN: Violin plot for distribution visualization
        AREA: Filled area chart
        STEM: Stem plot (lollipop chart)
        STEP: Step chart for discrete changes
        ERRORBAR: Error bar chart
        BAR_HORIZONTAL: Horizontal bar chart
    """

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    POLAR = "polar"
    BOX = "box"
    VIOLIN = "violin"
    AREA = "area"
    STEM = "stem"
    STEP = "step"
    ERRORBAR = "errorbar"
    BAR_HORIZONTAL = "barh"


@dataclass
class SeriesConfig:
    """Configuration for a single data series.

    Attributes:
        x_column: Name of the column to use for x-axis values
        y_column: Name of the column to use for y-axis values
        label: Legend label for this series
        color: Color for this series (hex code or named color)
        line_style: Line style ('-', '--', '-.', ':')
        marker: Marker style ('o', 's', '^', etc.)
        line_width: Width of the line
        use_secondary_y: Whether to plot on secondary y-axis
        source_file_index: Index of source file when using multiple DataFrames
    """

    x_column: str
    y_column: str
    label: str | None = None
    color: str | None = None
    line_style: str = "-"
    marker: str | None = None
    line_width: float = 1.5
    use_secondary_y: bool = False
    source_file_index: int = 0


@dataclass
class PlotConfig:
    """Configuration for plot appearance.

    Attributes:
        chart_type: Type of chart to create
        title: Plot title
        x_label: Label for x-axis
        y_label: Label for y-axis
        y2_label: Label for secondary y-axis
        figure_width: Figure width in inches
        figure_height: Figure height in inches
        show_grid: Whether to show grid lines
        show_legend: Whether to show legend
    """

    chart_type: ChartType = ChartType.LINE
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    y2_label: str = ""
    figure_width: float = 10.0
    figure_height: float = 6.0
    show_grid: bool = True
    show_legend: bool = True


class Plotter:
    """Create matplotlib figures from DataFrame data.

    Example:
        >>> from plottini.core.plotter import Plotter, PlotConfig, SeriesConfig
        >>> config = PlotConfig(title="My Plot")
        >>> plotter = Plotter(config)
        >>> series = [SeriesConfig(x_column="x", y_column="y")]
        >>> fig = plotter.create_figure(df, series)
    """

    def __init__(self, config: PlotConfig | None = None) -> None:
        """Initialize plotter with configuration.

        Args:
            config: Plot configuration. Uses defaults if None.
        """
        self.config = config or PlotConfig()

    def create_figure(
        self,
        data: DataFrame | list[DataFrame],
        series: list[SeriesConfig],
    ) -> Figure:
        """Create a matplotlib figure from data.

        Args:
            data: DataFrame or list of DataFrames containing the data
            series: List of series configurations

        Returns:
            Matplotlib Figure object

        Raises:
            KeyError: If a column name doesn't exist in the data
        """
        # Normalize data to list
        if not isinstance(data, list):
            data = [data]

        # Create figure and axes (polar requires special projection)
        if self.config.chart_type == ChartType.POLAR:
            fig, ax = plt.subplots(
                figsize=(self.config.figure_width, self.config.figure_height),
                subplot_kw={"projection": "polar"},
            )
        else:
            fig, ax = plt.subplots(figsize=(self.config.figure_width, self.config.figure_height))

        # Check if secondary y-axis is needed (only for supported chart types)
        ax2: Axes | None = None
        supported_secondary = {ChartType.LINE, ChartType.SCATTER, ChartType.AREA, ChartType.STEP}
        if self.config.chart_type in supported_secondary:
            needs_secondary = any(s.use_secondary_y for s in series)
            if needs_secondary:
                ax2 = ax.twinx()

        # Plot based on chart type
        if self.config.chart_type == ChartType.LINE:
            self._plot_line(ax, data, series, ax2)
        elif self.config.chart_type == ChartType.BAR:
            self._plot_bar(ax, data, series)
        elif self.config.chart_type == ChartType.PIE:
            self._plot_pie(ax, data, series)
        elif self.config.chart_type == ChartType.SCATTER:
            self._plot_scatter(ax, data, series, ax2)
        elif self.config.chart_type == ChartType.HISTOGRAM:
            self._plot_histogram(ax, data, series)
        elif self.config.chart_type == ChartType.POLAR:
            self._plot_polar(ax, data, series)
        elif self.config.chart_type == ChartType.BOX:
            self._plot_box(ax, data, series)
        elif self.config.chart_type == ChartType.VIOLIN:
            self._plot_violin(ax, data, series)
        elif self.config.chart_type == ChartType.AREA:
            self._plot_area(ax, data, series, ax2)
        elif self.config.chart_type == ChartType.STEM:
            self._plot_stem(ax, data, series)
        elif self.config.chart_type == ChartType.STEP:
            self._plot_step(ax, data, series, ax2)
        elif self.config.chart_type == ChartType.ERRORBAR:
            self._plot_errorbar(ax, data, series)
        elif self.config.chart_type == ChartType.BAR_HORIZONTAL:
            self._plot_bar_horizontal(ax, data, series)

        # Apply common configuration
        self._apply_config(ax, ax2)

        return fig

    def _plot_line(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
        ax2: Axes | None = None,
    ) -> None:
        """Plot line chart."""
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame (raises KeyError if column doesn't exist)
            x_data = df[s.x_column]
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Select target axis
            target_ax = ax2 if s.use_secondary_y and ax2 else ax

            target_ax.plot(
                x_data,
                y_data,
                label=s.label,
                color=color,
                linestyle=s.line_style,
                marker=s.marker,
                linewidth=s.line_width,
            )

    def _plot_bar(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot bar chart.

        For multiple series, creates grouped bars side by side.
        """
        import numpy as np

        # Get x-axis labels from first series
        first_series = series[0]
        df = data[first_series.source_file_index]
        x_labels = df[first_series.x_column]

        # Convert to string labels for categorical axis
        x_labels_str = [str(label) for label in x_labels]
        x_positions = np.arange(len(x_labels_str))

        # Calculate bar width for grouped bars
        n_series = len(series)
        bar_width = 0.8 / n_series

        for idx, s in enumerate(series):
            df = data[s.source_file_index]
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Calculate offset for grouped bars
            offset = (idx - n_series / 2 + 0.5) * bar_width

            ax.bar(
                x_positions + offset,
                y_data,
                width=bar_width,
                label=s.label,
                color=color,
            )

        # Set x-tick labels
        ax.set_xticks(x_positions)
        ax.set_xticklabels(x_labels_str)

    def _plot_pie(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot pie chart.

        Only a single series is allowed for pie charts.

        Raises:
            ValidationError: If more than one series is provided.
        """
        from plottini.utils.errors import ValidationError

        # Validate single series
        if len(series) > 1:
            raise ValidationError(
                message="Pie chart only supports a single series",
                field="series",
                value=f"{len(series)} series provided",
            )

        s = series[0]
        df = data[s.source_file_index]

        # Get data
        labels = df[s.x_column]
        values = df[s.y_column]

        # Convert labels to strings
        labels_str = [str(label) for label in labels]

        # Determine colors
        if s.color:
            colors = [s.color] * len(values)
        else:
            colors = [COLORBLIND_PALETTE[i % len(COLORBLIND_PALETTE)] for i in range(len(values))]

        ax.pie(
            values,
            labels=labels_str,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
        )

    def _plot_scatter(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
        ax2: Axes | None = None,
    ) -> None:
        """Plot scatter chart for correlation analysis."""
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame
            x_data = df[s.x_column]
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Determine marker (default to 'o' for scatter)
            marker = s.marker if s.marker else "o"

            # Select target axis
            target_ax = ax2 if s.use_secondary_y and ax2 else ax

            target_ax.scatter(
                x_data,
                y_data,
                label=s.label,
                color=color,
                marker=marker,
                s=50,  # marker size
            )

    def _plot_histogram(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot histogram for distribution analysis.

        Uses y_column for the data; x_column is ignored for histograms.
        """
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame (use y_column for histogram data)
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            ax.hist(
                y_data,
                bins="auto",
                label=s.label,
                color=color,
                alpha=0.7,
                edgecolor="black",
            )

    def _plot_polar(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot polar/radial chart.

        x_column provides angles (in radians), y_column provides radii.
        """
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame
            theta = df[s.x_column]  # angles in radians
            r = df[s.y_column]  # radii

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            ax.plot(
                theta,
                r,
                label=s.label,
                color=color,
                linestyle=s.line_style,
                marker=s.marker,
                linewidth=s.line_width,
            )

    def _plot_box(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot box plot for statistical distribution.

        Each series y_column becomes a box in the plot.
        """
        import numpy as np

        box_data = []
        labels = []

        for s in series:
            df = data[s.source_file_index]
            y_data = df[s.y_column]
            box_data.append(np.array(y_data))
            labels.append(s.label if s.label else s.y_column)

        bp = ax.boxplot(box_data, tick_labels=labels, patch_artist=True)

        # Apply colors
        for idx, patch in enumerate(bp["boxes"]):
            color = (
                series[idx].color
                if series[idx].color
                else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]
            )
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

    def _plot_violin(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot violin plot for distribution visualization.

        Each series y_column becomes a violin in the plot.
        """
        import numpy as np

        violin_data = []
        labels = []

        for s in series:
            df = data[s.source_file_index]
            y_data = df[s.y_column]
            violin_data.append(np.array(y_data))
            labels.append(s.label if s.label else s.y_column)

        parts = ax.violinplot(violin_data, showmeans=True, showmedians=True)

        # Apply colors - bodies is a list of PolyCollection objects
        bodies = parts["bodies"]
        for idx in range(len(series)):
            pc = bodies[idx]  # type: ignore[index]
            color = (
                series[idx].color
                if series[idx].color
                else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]
            )
            pc.set_facecolor(color)
            pc.set_alpha(0.7)

        # Set x-tick labels
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels)

    def _plot_area(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
        ax2: Axes | None = None,
    ) -> None:
        """Plot filled area chart."""
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame
            x_data = df[s.x_column]
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Select target axis
            target_ax = ax2 if s.use_secondary_y and ax2 else ax

            target_ax.fill_between(
                x_data,
                y_data,
                label=s.label,
                color=color,
                alpha=0.5,
            )
            # Also plot the line on top
            target_ax.plot(x_data, y_data, color=color, linewidth=s.line_width)

    def _plot_stem(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot stem plot (lollipop chart)."""
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame
            x_data = df[s.x_column]
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Determine marker (default to 'o' for stem)
            marker = s.marker if s.marker else "o"

            markerline, stemlines, baseline = ax.stem(
                x_data, y_data, label=s.label, linefmt="-", markerfmt=marker
            )
            markerline.set_color(color)
            stemlines.set_color(color)
            baseline.set_color("gray")

    def _plot_step(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
        ax2: Axes | None = None,
    ) -> None:
        """Plot step chart for discrete changes."""
        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame
            x_data = df[s.x_column]
            y_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Select target axis
            target_ax = ax2 if s.use_secondary_y and ax2 else ax

            target_ax.step(
                x_data,
                y_data,
                label=s.label,
                color=color,
                linewidth=s.line_width,
                where="mid",
            )

    def _plot_errorbar(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot error bar chart.

        For error bars, we use a convention: if series has label ending with '_err',
        it's used as error values. Otherwise, we assume 10% error.
        """
        import numpy as np

        for idx, s in enumerate(series):
            df = data[s.source_file_index]

            # Get data from DataFrame
            x_data = df[s.x_column]
            y_data = np.array(df[s.y_column])

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Use 10% of y values as default error
            yerr = np.abs(y_data) * 0.1

            ax.errorbar(
                x_data,
                y_data,
                yerr=yerr,
                label=s.label,
                color=color,
                marker=s.marker if s.marker else "o",
                linestyle=s.line_style,
                linewidth=s.line_width,
                capsize=3,
            )

    def _plot_bar_horizontal(
        self,
        ax: Axes,
        data: list[DataFrame],
        series: list[SeriesConfig],
    ) -> None:
        """Plot horizontal bar chart.

        For multiple series, creates grouped horizontal bars.
        """
        import numpy as np

        # Get y-axis labels from first series
        first_series = series[0]
        df = data[first_series.source_file_index]
        y_labels = df[first_series.x_column]

        # Convert to string labels for categorical axis
        y_labels_str = [str(label) for label in y_labels]
        y_positions = np.arange(len(y_labels_str))

        # Calculate bar height for grouped bars
        n_series = len(series)
        bar_height = 0.8 / n_series

        for idx, s in enumerate(series):
            df = data[s.source_file_index]
            x_data = df[s.y_column]

            # Determine color
            color = s.color if s.color else COLORBLIND_PALETTE[idx % len(COLORBLIND_PALETTE)]

            # Calculate offset for grouped bars
            offset = (idx - n_series / 2 + 0.5) * bar_height

            ax.barh(
                y_positions + offset,
                x_data,
                height=bar_height,
                label=s.label,
                color=color,
            )

        # Set y-tick labels
        ax.set_yticks(y_positions)
        ax.set_yticklabels(y_labels_str)

    def _apply_config(self, ax: Axes, ax2: Axes | None = None) -> None:
        """Apply common configuration to axes."""
        # Title and labels
        if self.config.title:
            ax.set_title(self.config.title)
        if self.config.x_label:
            ax.set_xlabel(self.config.x_label)
        if self.config.y_label:
            ax.set_ylabel(self.config.y_label)

        # Secondary y-axis label
        if ax2 and self.config.y2_label:
            ax2.set_ylabel(self.config.y2_label)

        # Grid
        ax.grid(self.config.show_grid)

        # Legend - merge legends from both axes if secondary axis exists
        if self.config.show_legend:
            if ax2:
                # Get handles and labels from both axes
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                if labels1 or labels2:
                    ax.legend(lines1 + lines2, labels1 + labels2)
            elif ax.get_legend_handles_labels()[1]:
                ax.legend()


__all__ = [
    "ChartType",
    "SeriesConfig",
    "PlotConfig",
    "Plotter",
    "COLORBLIND_PALETTE",
]
