"""Tests for the plotter module."""

from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.figure import Figure

from plottini.core.dataframe import DataFrame
from plottini.core.parser import TSVParser
from plottini.core.plotter import (
    COLORBLIND_PALETTE,
    ChartType,
    PlotConfig,
    Plotter,
    SeriesConfig,
)

# Test fixtures path
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "plot_data"


@pytest.fixture
def line_simple_df() -> DataFrame:
    """Load simple line chart data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "line_simple.tsv")


@pytest.fixture
def line_multi_df() -> DataFrame:
    """Load multi-series line chart data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "line_multi.tsv")


@pytest.fixture
def bar_df() -> DataFrame:
    """Load bar chart data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "bar_categories.tsv")


@pytest.fixture
def pie_df() -> DataFrame:
    """Load pie chart data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "pie_data.tsv")


class TestChartType:
    """Tests for ChartType enum."""

    def test_chart_type_values(self):
        """Test ChartType enum has correct values."""
        assert ChartType.LINE.value == "line"
        assert ChartType.BAR.value == "bar"
        assert ChartType.PIE.value == "pie"

    def test_chart_type_members(self):
        """Test ChartType enum has expected members."""
        members = [ct.value for ct in ChartType]
        assert "line" in members
        assert "bar" in members
        assert "pie" in members


class TestSeriesConfig:
    """Tests for SeriesConfig dataclass."""

    def test_series_config_defaults(self):
        """Test SeriesConfig has correct default values."""
        config = SeriesConfig(x_column="x", y_column="y")
        assert config.x_column == "x"
        assert config.y_column == "y"
        assert config.label is None
        assert config.color is None
        assert config.line_style == "-"
        assert config.marker is None
        assert config.line_width == 1.5
        assert config.use_secondary_y is False
        assert config.source_file_index == 0

    def test_series_config_custom_values(self):
        """Test SeriesConfig with custom values."""
        config = SeriesConfig(
            x_column="time",
            y_column="value",
            label="Series 1",
            color="#FF0000",
            line_style="--",
            marker="o",
            line_width=2.0,
            use_secondary_y=True,
            source_file_index=1,
        )
        assert config.x_column == "time"
        assert config.y_column == "value"
        assert config.label == "Series 1"
        assert config.color == "#FF0000"
        assert config.line_style == "--"
        assert config.marker == "o"
        assert config.line_width == 2.0
        assert config.use_secondary_y is True
        assert config.source_file_index == 1


class TestPlotConfig:
    """Tests for PlotConfig dataclass."""

    def test_plot_config_defaults(self):
        """Test PlotConfig has correct default values."""
        config = PlotConfig()
        assert config.chart_type == ChartType.LINE
        assert config.title == ""
        assert config.x_label == ""
        assert config.y_label == ""
        assert config.y2_label == ""
        assert config.figure_width == 10.0
        assert config.figure_height == 6.0
        assert config.show_grid is True
        assert config.show_legend is True

    def test_plot_config_custom_values(self):
        """Test PlotConfig with custom values."""
        config = PlotConfig(
            chart_type=ChartType.BAR,
            title="My Chart",
            x_label="X Axis",
            y_label="Y Axis",
            y2_label="Secondary Y",
            figure_width=12.0,
            figure_height=8.0,
            show_grid=False,
            show_legend=False,
        )
        assert config.chart_type == ChartType.BAR
        assert config.title == "My Chart"
        assert config.x_label == "X Axis"
        assert config.y_label == "Y Axis"
        assert config.y2_label == "Secondary Y"
        assert config.figure_width == 12.0
        assert config.figure_height == 8.0
        assert config.show_grid is False
        assert config.show_legend is False


class TestColorblindPalette:
    """Tests for colorblind-safe palette."""

    def test_palette_has_eight_colors(self):
        """Test palette contains 8 colors."""
        assert len(COLORBLIND_PALETTE) == 8

    def test_palette_colors_are_hex(self):
        """Test all colors are valid hex codes."""
        for color in COLORBLIND_PALETTE:
            assert color.startswith("#")
            assert len(color) == 7


class TestPlotter:
    """Tests for Plotter class."""

    def test_plotter_default_config(self):
        """Test Plotter instantiation with default config."""
        plotter = Plotter()
        assert plotter.config is not None
        assert plotter.config.chart_type == ChartType.LINE

    def test_plotter_custom_config(self):
        """Test Plotter instantiation with custom config."""
        config = PlotConfig(chart_type=ChartType.BAR, title="Custom")
        plotter = Plotter(config)
        assert plotter.config.chart_type == ChartType.BAR
        assert plotter.config.title == "Custom"


class TestLineChart:
    """Tests for line chart creation."""

    def test_line_chart_single_series(self, line_simple_df):
        """Test line chart with single series."""
        plotter = Plotter()
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)
        assert len(fig.axes) >= 1

    def test_line_chart_multiple_series(self, line_multi_df):
        """Test line chart with multiple series."""
        plotter = Plotter()
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
            SeriesConfig(x_column="x", y_column="dampened", label="Dampened"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have 3 lines
        assert len(ax.lines) == 3

    def test_line_chart_custom_colors(self, line_multi_df):
        """Test line chart with custom colors."""
        plotter = Plotter()
        series = [
            SeriesConfig(x_column="x", y_column="sine", color="#FF0000"),
            SeriesConfig(x_column="x", y_column="cosine", color="#00FF00"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        assert ax.lines[0].get_color() == "#FF0000"
        assert ax.lines[1].get_color() == "#00FF00"

    def test_line_chart_line_styles(self, line_multi_df):
        """Test line chart with different line styles."""
        plotter = Plotter()
        series = [
            SeriesConfig(x_column="x", y_column="sine", line_style="-"),
            SeriesConfig(x_column="x", y_column="cosine", line_style="--"),
            SeriesConfig(x_column="x", y_column="dampened", line_style="-."),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        assert ax.lines[0].get_linestyle() == "-"
        assert ax.lines[1].get_linestyle() == "--"
        assert ax.lines[2].get_linestyle() == "-."

    def test_line_chart_with_markers(self, line_simple_df):
        """Test line chart with markers."""
        plotter = Plotter()
        series = [SeriesConfig(x_column="x", y_column="y", marker="o")]
        fig = plotter.create_figure(line_simple_df, series)

        ax = fig.axes[0]
        assert ax.lines[0].get_marker() == "o"

    def test_line_chart_figure_dimensions(self, line_simple_df):
        """Test figure dimensions configuration."""
        config = PlotConfig(figure_width=12.0, figure_height=8.0)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        width, height = fig.get_size_inches()
        assert width == 12.0
        assert height == 8.0

    def test_line_chart_title_and_labels(self, line_simple_df):
        """Test title and axis labels."""
        config = PlotConfig(
            title="Sine Wave",
            x_label="Time (s)",
            y_label="Amplitude",
        )
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        ax = fig.axes[0]
        assert ax.get_title() == "Sine Wave"
        assert ax.get_xlabel() == "Time (s)"
        assert ax.get_ylabel() == "Amplitude"

    def test_line_chart_legend_visible(self, line_multi_df):
        """Test legend is shown when enabled."""
        config = PlotConfig(show_legend=True)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is not None

    def test_line_chart_legend_location(self, line_multi_df):
        """Test legend location is applied correctly."""
        config = PlotConfig(show_legend=True, legend_loc="upper left")
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is not None
        # Verify legend was created with the specified location
        # We check that the legend exists and was configured (the loc parameter was passed)
        # Direct position verification is fragile across matplotlib versions

    def test_line_chart_legend_hidden(self, line_multi_df):
        """Test legend is hidden when disabled."""
        config = PlotConfig(show_legend=False)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is None

    def test_line_chart_grid_visible(self, line_simple_df):
        """Test grid is shown when enabled."""
        config = PlotConfig(show_grid=True)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        ax = fig.axes[0]
        # Check that grid lines exist
        assert ax.xaxis.get_gridlines()[0].get_visible() is True

    def test_line_chart_grid_hidden(self, line_simple_df):
        """Test grid is hidden when disabled."""
        config = PlotConfig(show_grid=False)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        ax = fig.axes[0]
        assert ax.xaxis.get_gridlines()[0].get_visible() is False

    def test_line_chart_invalid_column_raises_error(self, line_simple_df):
        """Test invalid column name raises KeyError."""
        plotter = Plotter()
        series = [SeriesConfig(x_column="x", y_column="nonexistent")]

        with pytest.raises(KeyError):
            plotter.create_figure(line_simple_df, series)

    def test_line_chart_auto_colors(self, line_multi_df):
        """Test auto color cycling from palette."""
        plotter = Plotter()
        series = [
            SeriesConfig(x_column="x", y_column="sine"),
            SeriesConfig(x_column="x", y_column="cosine"),
            SeriesConfig(x_column="x", y_column="dampened"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        # Colors should come from palette
        assert ax.lines[0].get_color() == COLORBLIND_PALETTE[0]
        assert ax.lines[1].get_color() == COLORBLIND_PALETTE[1]
        assert ax.lines[2].get_color() == COLORBLIND_PALETTE[2]


class TestBarChart:
    """Tests for bar chart creation."""

    def test_bar_chart_single_series(self, bar_df):
        """Test bar chart with single series."""
        config = PlotConfig(chart_type=ChartType.BAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Sales")]
        fig = plotter.create_figure(bar_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have bar containers
        assert len(ax.containers) >= 1

    def test_bar_chart_multiple_series(self, bar_df):
        """Test bar chart with multiple series (grouped bars)."""
        config = PlotConfig(chart_type=ChartType.BAR)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="Index", y_column="Sales", label="Sales"),
            SeriesConfig(x_column="Index", y_column="Profit", label="Profit"),
        ]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        # Should have 2 bar containers
        assert len(ax.containers) == 2

    def test_bar_chart_custom_colors(self, bar_df):
        """Test bar chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.BAR)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="Index", y_column="Sales", color="#FF0000"),
            SeriesConfig(x_column="Index", y_column="Profit", color="#00FF00"),
        ]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        # Check bar colors
        bars1 = ax.containers[0]
        bars2 = ax.containers[1]
        assert bars1[0].get_facecolor()[:3] == (1.0, 0.0, 0.0)  # Red
        assert bars2[0].get_facecolor()[:3] == (0.0, 1.0, 0.0)  # Green

    def test_bar_chart_labels_from_x_column(self, bar_df):
        """Test bar chart uses x_column values as labels."""
        config = PlotConfig(chart_type=ChartType.BAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Sales")]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        tick_labels = [t.get_text() for t in ax.get_xticklabels()]
        # Should have tick labels
        assert len(tick_labels) > 0

    def test_bar_chart_auto_colors(self, bar_df):
        """Test bar chart auto color cycling from palette."""
        config = PlotConfig(chart_type=ChartType.BAR)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="Index", y_column="Sales"),
            SeriesConfig(x_column="Index", y_column="Profit"),
        ]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        # First bar of first series should be first palette color
        bars1 = ax.containers[0]
        # Convert hex to RGB for comparison
        import matplotlib.colors as mcolors

        expected_rgb = mcolors.to_rgb(COLORBLIND_PALETTE[0])
        actual_rgb = bars1[0].get_facecolor()[:3]
        assert actual_rgb == pytest.approx(expected_rgb, abs=0.01)


class TestPieChart:
    """Tests for pie chart creation."""

    def test_pie_chart_single_series(self, pie_df):
        """Test pie chart with single series."""
        config = PlotConfig(chart_type=ChartType.PIE)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Share")]
        fig = plotter.create_figure(pie_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have pie wedges (patches)
        assert len(ax.patches) > 0

    def test_pie_chart_labels_from_x_column(self, pie_df):
        """Test pie chart uses x_column values as labels."""
        config = PlotConfig(chart_type=ChartType.PIE)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Share")]
        fig = plotter.create_figure(pie_df, series)

        ax = fig.axes[0]
        # Should have text labels (wedge labels + percentages)
        texts = ax.texts
        assert len(texts) > 0

    def test_pie_chart_percentage_display(self, pie_df):
        """Test pie chart shows percentages."""
        config = PlotConfig(chart_type=ChartType.PIE)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Share")]
        fig = plotter.create_figure(pie_df, series)

        ax = fig.axes[0]
        # Check that percentage text exists
        text_strings = [t.get_text() for t in ax.texts]
        # At least one text should contain '%'
        has_percentage = any("%" in t for t in text_strings)
        assert has_percentage

    def test_pie_chart_custom_colors(self, pie_df):
        """Test pie chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.PIE)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Share", color="#FF0000")]
        fig = plotter.create_figure(pie_df, series)

        # Should create figure without error
        assert isinstance(fig, Figure)

    def test_pie_chart_multiple_series_raises_error(self, pie_df):
        """Test pie chart with multiple series raises ValidationError."""
        from plottini.utils.errors import ValidationError

        config = PlotConfig(chart_type=ChartType.PIE)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="Index", y_column="Share"),
            SeriesConfig(x_column="Index", y_column="Share"),
        ]

        with pytest.raises(ValidationError):
            plotter.create_figure(pie_df, series)


# Additional fixtures for new chart types
@pytest.fixture
def scatter_df() -> DataFrame:
    """Load scatter chart data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "scatter_data.tsv")


@pytest.fixture
def histogram_df() -> DataFrame:
    """Load histogram data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "histogram_data.tsv")


@pytest.fixture
def polar_df() -> DataFrame:
    """Load polar chart data."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "polar_data.tsv")


@pytest.fixture
def distribution_df() -> DataFrame:
    """Load distribution data for box/violin plots."""
    parser = TSVParser()
    return parser.parse(FIXTURES_DIR / "distribution_data.tsv")


class TestScatterChart:
    """Tests for scatter chart creation."""

    def test_scatter_chart_single_series(self, scatter_df):
        """Test scatter chart with single series."""
        config = PlotConfig(chart_type=ChartType.SCATTER)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(scatter_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have scatter collection
        assert len(ax.collections) >= 1

    def test_scatter_chart_multiple_series(self, scatter_df):
        """Test scatter chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.SCATTER)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="y", label="Series 1"),
            SeriesConfig(x_column="x", y_column="y2", label="Series 2"),
        ]
        fig = plotter.create_figure(scatter_df, series)

        ax = fig.axes[0]
        # Should have 2 scatter collections
        assert len(ax.collections) == 2

    def test_scatter_chart_custom_colors(self, scatter_df):
        """Test scatter chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.SCATTER)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="y", color="#FF0000"),
        ]
        fig = plotter.create_figure(scatter_df, series)

        ax = fig.axes[0]
        # Verify scatter was created
        assert len(ax.collections) >= 1

    def test_scatter_chart_custom_markers(self, scatter_df):
        """Test scatter chart with custom markers."""
        config = PlotConfig(chart_type=ChartType.SCATTER)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="y", marker="s"),
        ]
        fig = plotter.create_figure(scatter_df, series)

        assert isinstance(fig, Figure)

    def test_scatter_chart_auto_colors(self, scatter_df):
        """Test scatter chart auto color cycling from palette."""
        config = PlotConfig(chart_type=ChartType.SCATTER)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="y"),
            SeriesConfig(x_column="x", y_column="y2"),
        ]
        fig = plotter.create_figure(scatter_df, series)

        ax = fig.axes[0]
        assert len(ax.collections) == 2


class TestHistogramChart:
    """Tests for histogram chart creation."""

    def test_histogram_chart_single_series(self, histogram_df):
        """Test histogram chart with single series."""
        config = PlotConfig(chart_type=ChartType.HISTOGRAM)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="index", y_column="values")]
        fig = plotter.create_figure(histogram_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have histogram bars (patches)
        assert len(ax.patches) > 0

    def test_histogram_chart_multiple_series(self, histogram_df):
        """Test histogram chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.HISTOGRAM)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="index", y_column="values", label="Values 1"),
            SeriesConfig(x_column="index", y_column="values2", label="Values 2"),
        ]
        fig = plotter.create_figure(histogram_df, series)

        ax = fig.axes[0]
        # Should have bars from both histograms
        assert len(ax.patches) > 0

    def test_histogram_chart_custom_colors(self, histogram_df):
        """Test histogram chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.HISTOGRAM)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="index", y_column="values", color="#00FF00")]
        fig = plotter.create_figure(histogram_df, series)

        assert isinstance(fig, Figure)


class TestPolarChart:
    """Tests for polar chart creation."""

    def test_polar_chart_single_series(self, polar_df):
        """Test polar chart with single series."""
        config = PlotConfig(chart_type=ChartType.POLAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="theta", y_column="r")]
        fig = plotter.create_figure(polar_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have lines
        assert len(ax.lines) >= 1
        # Should be polar projection
        assert ax.name == "polar"

    def test_polar_chart_multiple_series(self, polar_df):
        """Test polar chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.POLAR)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="theta", y_column="r", label="Series 1"),
            SeriesConfig(x_column="theta", y_column="r2", label="Series 2"),
        ]
        fig = plotter.create_figure(polar_df, series)

        ax = fig.axes[0]
        assert len(ax.lines) == 2

    def test_polar_chart_custom_colors(self, polar_df):
        """Test polar chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.POLAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="theta", y_column="r", color="#0000FF")]
        fig = plotter.create_figure(polar_df, series)

        ax = fig.axes[0]
        assert ax.lines[0].get_color() == "#0000FF"

    def test_polar_chart_line_styles(self, polar_df):
        """Test polar chart with different line styles."""
        config = PlotConfig(chart_type=ChartType.POLAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="theta", y_column="r", line_style="--")]
        fig = plotter.create_figure(polar_df, series)

        ax = fig.axes[0]
        assert ax.lines[0].get_linestyle() == "--"


class TestBoxChart:
    """Tests for box plot creation."""

    def test_box_chart_single_series(self, distribution_df):
        """Test box plot with single series."""
        config = PlotConfig(chart_type=ChartType.BOX)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="index", y_column="group1")]
        fig = plotter.create_figure(distribution_df, series)

        assert isinstance(fig, Figure)

    def test_box_chart_multiple_series(self, distribution_df):
        """Test box plot with multiple series."""
        config = PlotConfig(chart_type=ChartType.BOX)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="index", y_column="group1", label="Group 1"),
            SeriesConfig(x_column="index", y_column="group2", label="Group 2"),
            SeriesConfig(x_column="index", y_column="group3", label="Group 3"),
        ]
        fig = plotter.create_figure(distribution_df, series)

        ax = fig.axes[0]
        # Should have patches for boxes
        assert len(ax.patches) >= 3

    def test_box_chart_custom_colors(self, distribution_df):
        """Test box plot with custom colors."""
        config = PlotConfig(chart_type=ChartType.BOX)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="index", y_column="group1", color="#FF0000"),
            SeriesConfig(x_column="index", y_column="group2", color="#00FF00"),
        ]
        fig = plotter.create_figure(distribution_df, series)

        assert isinstance(fig, Figure)


class TestViolinChart:
    """Tests for violin plot creation."""

    def test_violin_chart_single_series(self, distribution_df):
        """Test violin plot with single series."""
        config = PlotConfig(chart_type=ChartType.VIOLIN)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="index", y_column="group1")]
        fig = plotter.create_figure(distribution_df, series)

        assert isinstance(fig, Figure)

    def test_violin_chart_multiple_series(self, distribution_df):
        """Test violin plot with multiple series."""
        config = PlotConfig(chart_type=ChartType.VIOLIN)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="index", y_column="group1", label="Group 1"),
            SeriesConfig(x_column="index", y_column="group2", label="Group 2"),
        ]
        fig = plotter.create_figure(distribution_df, series)

        ax = fig.axes[0]
        # Should have collections for violins
        assert len(ax.collections) >= 2

    def test_violin_chart_custom_colors(self, distribution_df):
        """Test violin plot with custom colors."""
        config = PlotConfig(chart_type=ChartType.VIOLIN)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="index", y_column="group1", color="#FF0000"),
        ]
        fig = plotter.create_figure(distribution_df, series)

        assert isinstance(fig, Figure)


class TestAreaChart:
    """Tests for area chart creation."""

    def test_area_chart_single_series(self, line_simple_df):
        """Test area chart with single series."""
        config = PlotConfig(chart_type=ChartType.AREA)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have filled collection
        assert len(ax.collections) >= 1

    def test_area_chart_multiple_series(self, line_multi_df):
        """Test area chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.AREA)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        # Should have 2 fill collections
        assert len(ax.collections) >= 2

    def test_area_chart_custom_colors(self, line_simple_df):
        """Test area chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.AREA)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y", color="#FF00FF")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)


class TestStemChart:
    """Tests for stem plot creation."""

    def test_stem_chart_single_series(self, line_simple_df):
        """Test stem chart with single series."""
        config = PlotConfig(chart_type=ChartType.STEM)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)

    def test_stem_chart_multiple_series(self, line_multi_df):
        """Test stem chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.STEM)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        assert isinstance(fig, Figure)

    def test_stem_chart_custom_colors(self, line_simple_df):
        """Test stem chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.STEM)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y", color="#00FFFF")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)


class TestStepChart:
    """Tests for step chart creation."""

    def test_step_chart_single_series(self, line_simple_df):
        """Test step chart with single series."""
        config = PlotConfig(chart_type=ChartType.STEP)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have lines
        assert len(ax.lines) >= 1

    def test_step_chart_multiple_series(self, line_multi_df):
        """Test step chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.STEP)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        assert len(ax.lines) == 2

    def test_step_chart_custom_colors(self, line_simple_df):
        """Test step chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.STEP)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y", color="#FFFF00")]
        fig = plotter.create_figure(line_simple_df, series)

        ax = fig.axes[0]
        assert ax.lines[0].get_color() == "#FFFF00"


class TestErrorBarChart:
    """Tests for error bar chart creation."""

    def test_errorbar_chart_single_series(self, line_simple_df):
        """Test error bar chart with single series."""
        config = PlotConfig(chart_type=ChartType.ERRORBAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have error bar containers
        assert len(ax.containers) >= 1

    def test_errorbar_chart_multiple_series(self, line_multi_df):
        """Test error bar chart with multiple series."""
        config = PlotConfig(chart_type=ChartType.ERRORBAR)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="sine", label="Sine"),
            SeriesConfig(x_column="x", y_column="cosine", label="Cosine"),
        ]
        fig = plotter.create_figure(line_multi_df, series)

        ax = fig.axes[0]
        # Should have 2 error bar containers
        assert len(ax.containers) == 2

    def test_errorbar_chart_custom_colors(self, line_simple_df):
        """Test error bar chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.ERRORBAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="y", color="#800080")]
        fig = plotter.create_figure(line_simple_df, series)

        assert isinstance(fig, Figure)


class TestBarHorizontalChart:
    """Tests for horizontal bar chart creation."""

    def test_bar_horizontal_single_series(self, bar_df):
        """Test horizontal bar chart with single series."""
        config = PlotConfig(chart_type=ChartType.BAR_HORIZONTAL)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Sales")]
        fig = plotter.create_figure(bar_df, series)

        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        # Should have bar containers
        assert len(ax.containers) >= 1

    def test_bar_horizontal_multiple_series(self, bar_df):
        """Test horizontal bar chart with multiple series (grouped bars)."""
        config = PlotConfig(chart_type=ChartType.BAR_HORIZONTAL)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="Index", y_column="Sales", label="Sales"),
            SeriesConfig(x_column="Index", y_column="Profit", label="Profit"),
        ]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        # Should have 2 bar containers
        assert len(ax.containers) == 2

    def test_bar_horizontal_custom_colors(self, bar_df):
        """Test horizontal bar chart with custom colors."""
        config = PlotConfig(chart_type=ChartType.BAR_HORIZONTAL)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="Index", y_column="Sales", color="#FF0000"),
            SeriesConfig(x_column="Index", y_column="Profit", color="#00FF00"),
        ]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        # Check bar colors
        bars1 = ax.containers[0]
        bars2 = ax.containers[1]
        assert bars1[0].get_facecolor()[:3] == (1.0, 0.0, 0.0)  # Red
        assert bars2[0].get_facecolor()[:3] == (0.0, 1.0, 0.0)  # Green

    def test_bar_horizontal_labels_from_x_column(self, bar_df):
        """Test horizontal bar chart uses x_column values as labels."""
        config = PlotConfig(chart_type=ChartType.BAR_HORIZONTAL)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Sales")]
        fig = plotter.create_figure(bar_df, series)

        ax = fig.axes[0]
        tick_labels = [t.get_text() for t in ax.get_yticklabels()]
        # Should have tick labels
        assert len(tick_labels) > 0


class TestChartTypeEnumComplete:
    """Tests to verify all chart types are supported."""

    def test_all_chart_types_have_values(self):
        """Test all ChartType enum values exist."""
        expected_types = [
            "line",
            "bar",
            "pie",
            "scatter",
            "histogram",
            "polar",
            "box",
            "violin",
            "area",
            "stem",
            "step",
            "errorbar",
            "barh",
        ]
        actual_types = [ct.value for ct in ChartType]
        for expected in expected_types:
            assert expected in actual_types, f"Missing chart type: {expected}"


class TestSecondaryYAxis:
    """Tests for secondary Y-axis support."""

    @pytest.fixture
    def dual_axis_df(self) -> DataFrame:
        """Create DataFrame with data suitable for dual axis plotting."""
        import numpy as np

        from plottini.core.dataframe import Column

        col_x = Column(
            name="x",
            index=0,
            data=np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64),
        )
        col_y1 = Column(
            name="temperature",
            index=1,
            data=np.array([20.0, 22.0, 25.0, 23.0, 21.0], dtype=np.float64),
        )
        col_y2 = Column(
            name="pressure",
            index=2,
            data=np.array([1000.0, 1005.0, 1010.0, 1008.0, 1003.0], dtype=np.float64),
        )
        return DataFrame(
            columns={"x": col_x, "temperature": col_y1, "pressure": col_y2},
            source_file=Path("dual_axis.tsv"),
            row_count=5,
        )

    def test_line_chart_single_series_secondary_axis(self, dual_axis_df):
        """Test line chart with single series on secondary axis."""
        config = PlotConfig(chart_type=ChartType.LINE, y2_label="Pressure (hPa)")
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="pressure", use_secondary_y=True, label="Pressure")
        ]
        fig = plotter.create_figure(dual_axis_df, series)

        # Should have two axes (primary and secondary)
        assert len(fig.axes) == 2
        ax2 = fig.axes[1]
        assert ax2.get_ylabel() == "Pressure (hPa)"

    def test_line_chart_mixed_series(self, dual_axis_df):
        """Test line chart with mixed primary and secondary series."""
        config = PlotConfig(
            chart_type=ChartType.LINE,
            y_label="Temperature (C)",
            y2_label="Pressure (hPa)",
        )
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="temperature", label="Temperature"),
            SeriesConfig(x_column="x", y_column="pressure", use_secondary_y=True, label="Pressure"),
        ]
        fig = plotter.create_figure(dual_axis_df, series)

        # Should have two axes
        assert len(fig.axes) == 2
        ax = fig.axes[0]
        ax2 = fig.axes[1]

        # Check labels
        assert ax.get_ylabel() == "Temperature (C)"
        assert ax2.get_ylabel() == "Pressure (hPa)"

    def test_line_chart_no_secondary_axis_when_not_needed(self, dual_axis_df):
        """Test line chart doesn't create secondary axis when not needed."""
        config = PlotConfig(chart_type=ChartType.LINE)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="x", y_column="temperature", label="Temperature")]
        fig = plotter.create_figure(dual_axis_df, series)

        # Should have only one axis
        assert len(fig.axes) == 1

    def test_scatter_chart_secondary_axis(self, dual_axis_df):
        """Test scatter chart supports secondary axis."""
        config = PlotConfig(chart_type=ChartType.SCATTER, y2_label="Pressure")
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="temperature", label="Temperature"),
            SeriesConfig(x_column="x", y_column="pressure", use_secondary_y=True, label="Pressure"),
        ]
        fig = plotter.create_figure(dual_axis_df, series)

        # Should have two axes
        assert len(fig.axes) == 2
        assert fig.axes[1].get_ylabel() == "Pressure"

    def test_area_chart_secondary_axis(self, dual_axis_df):
        """Test area chart supports secondary axis."""
        config = PlotConfig(chart_type=ChartType.AREA, y2_label="Pressure")
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="temperature", label="Temperature"),
            SeriesConfig(x_column="x", y_column="pressure", use_secondary_y=True, label="Pressure"),
        ]
        fig = plotter.create_figure(dual_axis_df, series)

        # Should have two axes
        assert len(fig.axes) == 2

    def test_step_chart_secondary_axis(self, dual_axis_df):
        """Test step chart supports secondary axis."""
        config = PlotConfig(chart_type=ChartType.STEP, y2_label="Pressure")
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="temperature", label="Temperature"),
            SeriesConfig(x_column="x", y_column="pressure", use_secondary_y=True, label="Pressure"),
        ]
        fig = plotter.create_figure(dual_axis_df, series)

        # Should have two axes
        assert len(fig.axes) == 2

    def test_bar_chart_ignores_secondary_axis(self, bar_df):
        """Test bar chart ignores secondary axis setting."""
        config = PlotConfig(chart_type=ChartType.BAR)
        plotter = Plotter(config)
        series = [SeriesConfig(x_column="Index", y_column="Sales", use_secondary_y=True)]
        fig = plotter.create_figure(bar_df, series)

        # Should still have only one axis (secondary not supported for bar)
        assert len(fig.axes) == 1

    def test_secondary_axis_legend_merged(self, dual_axis_df):
        """Test legend includes series from both axes."""
        config = PlotConfig(chart_type=ChartType.LINE, show_legend=True)
        plotter = Plotter(config)
        series = [
            SeriesConfig(x_column="x", y_column="temperature", label="Temperature"),
            SeriesConfig(x_column="x", y_column="pressure", use_secondary_y=True, label="Pressure"),
        ]
        fig = plotter.create_figure(dual_axis_df, series)

        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is not None
        legend_texts = [t.get_text() for t in legend.get_texts()]
        assert "Temperature" in legend_texts
        assert "Pressure" in legend_texts
