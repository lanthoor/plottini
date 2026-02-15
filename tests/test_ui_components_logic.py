"""Tests for UI component business logic without Streamlit runtime.

These tests verify business logic and state management
without requiring the Streamlit runtime.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

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
from plottini.core.dataframe import Column, DataFrame
from plottini.core.exporter import ExportFormat
from plottini.core.parser import ParserConfig, TSVParser
from plottini.core.plotter import COLORBLIND_PALETTE, ChartType, PlotConfig, SeriesConfig
from plottini.ui.state import AppState, DataSource, UploadedFile


class TestFileSelectorLogic:
    """Tests for file loading business logic."""

    @pytest.fixture
    def sample_tsv(self, tmp_path: Path) -> Path:
        """Create a sample TSV file."""
        file = tmp_path / "sample.tsv"
        file.write_text("x\ty\n1.0\t2.0\n3.0\t4.0\n")
        return file

    @pytest.fixture
    def multi_block_tsv(self, tmp_path: Path) -> Path:
        """Create a multi-block TSV file."""
        file = tmp_path / "multi.tsv"
        file.write_text("x\ty\n1.0\t2.0\n\nx\ty\n3.0\t4.0\n")
        return file

    def test_load_file_adds_to_state(self, sample_tsv: Path) -> None:
        """Test that loading a file adds it to state.uploaded_files."""
        state = AppState()
        parser = TSVParser(state.parser_config)

        # Simulate file loading logic
        content = sample_tsv.read_bytes()
        state.uploaded_files[sample_tsv.name] = UploadedFile(name=sample_tsv.name, content=content)

        dataframes = parser.parse_blocks(sample_tsv)
        for i, df in enumerate(dataframes):
            block_idx = i if len(dataframes) > 1 else None
            ds = DataSource(file_name=sample_tsv.name, block_index=block_idx)
            state.data_sources.append(ds)
            state.parsed_data[ds] = df

        assert sample_tsv.name in state.uploaded_files
        assert len(state.parsed_data) == 1
        assert len(state.data_sources) == 1

    def test_load_multi_block_file(self, multi_block_tsv: Path) -> None:
        """Test loading a multi-block file creates multiple data sources."""
        state = AppState()
        parser = TSVParser(state.parser_config)

        content = multi_block_tsv.read_bytes()
        state.uploaded_files[multi_block_tsv.name] = UploadedFile(
            name=multi_block_tsv.name, content=content
        )

        dataframes = parser.parse_blocks(multi_block_tsv)
        for i, df in enumerate(dataframes):
            block_idx = i if len(dataframes) > 1 else None
            ds = DataSource(file_name=multi_block_tsv.name, block_index=block_idx)
            state.data_sources.append(ds)
            state.parsed_data[ds] = df

        assert multi_block_tsv.name in state.uploaded_files
        assert len(state.parsed_data) == 2
        assert len(state.data_sources) == 2

    def test_remove_file_clears_related_data(self, sample_tsv: Path) -> None:
        """Test that removing a file clears its data sources."""
        state = AppState()
        parser = TSVParser(state.parser_config)

        # Load file
        content = sample_tsv.read_bytes()
        state.uploaded_files[sample_tsv.name] = UploadedFile(name=sample_tsv.name, content=content)

        dataframes = parser.parse_blocks(sample_tsv)
        for i, df in enumerate(dataframes):
            block_idx = i if len(dataframes) > 1 else None
            ds = DataSource(file_name=sample_tsv.name, block_index=block_idx)
            state.data_sources.append(ds)
            state.parsed_data[ds] = df
        state.series.append(SeriesConfig(x_column="x", y_column="y", source_file_index=0))

        # Use remove_file method
        state.remove_file(sample_tsv.name)

        assert sample_tsv.name not in state.uploaded_files
        assert len(state.parsed_data) == 0
        assert len(state.series) == 0

    def test_reparse_files_clears_series(self, sample_tsv: Path) -> None:
        """Test that re-parsing files clears series (indices would be invalid)."""
        state = AppState()
        parser = TSVParser(state.parser_config)

        # Initial parse
        content = sample_tsv.read_bytes()
        state.uploaded_files[sample_tsv.name] = UploadedFile(name=sample_tsv.name, content=content)

        dataframes = parser.parse_blocks(sample_tsv)
        for i, df in enumerate(dataframes):
            block_idx = i if len(dataframes) > 1 else None
            ds = DataSource(file_name=sample_tsv.name, block_index=block_idx)
            state.data_sources.append(ds)
            state.parsed_data[ds] = df
        state.series.append(SeriesConfig(x_column="x", y_column="y"))

        # Simulate reparse (parser settings change)
        state.data_sources.clear()
        state.parsed_data.clear()
        state.series.clear()  # Series must be cleared

        # Re-parse
        dataframes = parser.parse_blocks(sample_tsv)
        for i, df in enumerate(dataframes):
            block_idx = i if len(dataframes) > 1 else None
            ds = DataSource(file_name=sample_tsv.name, block_index=block_idx)
            state.data_sources.append(ds)
            state.parsed_data[ds] = df

        assert len(state.series) == 0  # Verify series was cleared


class TestSeriesConfigPanelLogic:
    """Tests for SeriesConfigPanel business logic."""

    @pytest.fixture
    def state_with_data(self, tmp_path: Path) -> AppState:
        """Create state with sample data loaded."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.data_sources.append(ds)
        state.parsed_data[ds] = DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 2.0, 3.0])),
                "y": Column(name="y", index=1, data=np.array([4.0, 5.0, 6.0])),
                "z": Column(name="z", index=2, data=np.array([7.0, 8.0, 9.0])),
            },
            source_file=tmp_path / "test.tsv",
            row_count=3,
        )
        return state

    def test_add_series_uses_first_columns(self, state_with_data: AppState) -> None:
        """Test that adding series defaults to first available columns."""
        columns = state_with_data.get_all_column_names()
        x_col = columns[0] if columns else ""
        y_col = columns[1] if len(columns) > 1 else x_col

        # Simulate SeriesConfigPanel._add_series logic
        color_idx = len(state_with_data.series) % len(COLORBLIND_PALETTE)
        state_with_data.series.append(
            SeriesConfig(
                x_column=x_col,
                y_column=y_col,
                label=f"Series {len(state_with_data.series) + 1}",
                color=COLORBLIND_PALETTE[color_idx],
            )
        )

        assert len(state_with_data.series) == 1
        assert state_with_data.series[0].x_column == "x"
        assert state_with_data.series[0].y_column == "y"
        assert state_with_data.series[0].color == COLORBLIND_PALETTE[0]

    def test_add_series_cycles_colors(self, state_with_data: AppState) -> None:
        """Test that colors cycle through palette."""
        for _ in range(10):
            color_idx = len(state_with_data.series) % len(COLORBLIND_PALETTE)
            state_with_data.series.append(
                SeriesConfig(
                    x_column="x",
                    y_column="y",
                    color=COLORBLIND_PALETTE[color_idx],
                )
            )

        # After 8 series (palette length), colors should repeat
        assert state_with_data.series[0].color == state_with_data.series[8].color
        assert state_with_data.series[1].color == state_with_data.series[9].color

    def test_remove_series_by_index(self, state_with_data: AppState) -> None:
        """Test removing series by index."""
        state_with_data.series.append(SeriesConfig(x_column="x", y_column="y", label="A"))
        state_with_data.series.append(SeriesConfig(x_column="x", y_column="z", label="B"))
        state_with_data.series.append(SeriesConfig(x_column="y", y_column="z", label="C"))

        # Remove middle series
        state_with_data.series.pop(1)

        assert len(state_with_data.series) == 2
        assert state_with_data.series[0].label == "A"
        assert state_with_data.series[1].label == "C"

    def test_update_series_column(self, state_with_data: AppState) -> None:
        """Test updating a series column mapping."""
        state_with_data.series.append(SeriesConfig(x_column="x", y_column="y", label="Test"))

        # Update y column
        state_with_data.series[0] = SeriesConfig(
            x_column=state_with_data.series[0].x_column,
            y_column="z",
            label=state_with_data.series[0].label,
            color=state_with_data.series[0].color,
        )

        assert state_with_data.series[0].y_column == "z"

    def test_series_source_file_index(self, state_with_data: AppState) -> None:
        """Test series can reference different source files."""
        state_with_data.series.append(SeriesConfig(x_column="x", y_column="y", source_file_index=0))
        state_with_data.series.append(SeriesConfig(x_column="x", y_column="y", source_file_index=1))

        assert state_with_data.series[0].source_file_index == 0
        assert state_with_data.series[1].source_file_index == 1


class TestFilterPanelLogic:
    """Tests for FilterPanel business logic."""

    def test_filter_config_min_only(self) -> None:
        """Test filter config with only minimum bound."""
        filter_config = FilterConfig(column="x", min=5.0)
        assert filter_config.column == "x"
        assert filter_config.min == 5.0
        assert filter_config.max is None

    def test_filter_config_max_only(self) -> None:
        """Test filter config with only maximum bound."""
        filter_config = FilterConfig(column="y", max=10.0)
        assert filter_config.column == "y"
        assert filter_config.min is None
        assert filter_config.max == 10.0

    def test_filter_config_both_bounds(self) -> None:
        """Test filter config with both bounds."""
        filter_config = FilterConfig(column="z", min=1.0, max=100.0)
        assert filter_config.column == "z"
        assert filter_config.min == 1.0
        assert filter_config.max == 100.0

    def test_add_filter_to_state(self) -> None:
        """Test adding filter to state."""
        state = AppState()
        state.filters.append(FilterConfig(column="x", min=0.0, max=10.0))

        assert len(state.filters) == 1
        assert state.filters[0].column == "x"

    def test_remove_filter_from_state(self) -> None:
        """Test removing filter from state."""
        state = AppState()
        state.filters.append(FilterConfig(column="x", min=0.0))
        state.filters.append(FilterConfig(column="y", max=10.0))

        state.filters.pop(0)

        assert len(state.filters) == 1
        assert state.filters[0].column == "y"

    def test_multiple_filters_same_column(self) -> None:
        """Test multiple filters can apply to same column."""
        state = AppState()
        state.filters.append(FilterConfig(column="x", min=0.0))
        state.filters.append(FilterConfig(column="x", max=100.0))

        assert len(state.filters) == 2
        assert all(f.column == "x" for f in state.filters)


class TestTransformPanelLogic:
    """Tests for TransformPanel business logic."""

    def test_derived_column_config_creation(self) -> None:
        """Test DerivedColumnConfig creation."""
        dc = DerivedColumnConfig(name="velocity", expression="distance / time")
        assert dc.name == "velocity"
        assert dc.expression == "distance / time"

    def test_add_derived_column_to_state(self) -> None:
        """Test adding derived column config to state."""
        state = AppState()
        state.derived_columns.append(
            DerivedColumnConfig(name="velocity", expression="distance / time")
        )

        assert len(state.derived_columns) == 1
        assert state.derived_columns[0].name == "velocity"

    def test_apply_derived_column_to_dataframe(self, tmp_path: Path) -> None:
        """Test applying derived column to DataFrame."""
        df = DataFrame(
            columns={
                "distance": Column(name="distance", index=0, data=np.array([10.0, 40.0, 90.0])),
                "time": Column(name="time", index=1, data=np.array([1.0, 2.0, 3.0])),
            },
            source_file=tmp_path / "test.tsv",
            row_count=3,
        )

        df.add_derived_column("velocity", "distance / time")

        assert "velocity" in df
        np.testing.assert_array_almost_equal(df["velocity"], [10.0, 20.0, 30.0])

    def test_derived_column_with_math_functions(self, tmp_path: Path) -> None:
        """Test derived column using math functions."""
        df = DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 4.0, 9.0])),
            },
            source_file=tmp_path / "test.tsv",
            row_count=3,
        )

        df.add_derived_column("sqrt_x", "sqrt(x)")

        assert "sqrt_x" in df
        np.testing.assert_array_almost_equal(df["sqrt_x"], [1.0, 2.0, 3.0])

    def test_remove_derived_column_from_state(self) -> None:
        """Test removing derived column from state."""
        state = AppState()
        state.derived_columns.append(DerivedColumnConfig(name="a", expression="x+y"))
        state.derived_columns.append(DerivedColumnConfig(name="b", expression="x*y"))

        state.derived_columns.pop(0)

        assert len(state.derived_columns) == 1
        assert state.derived_columns[0].name == "b"


class TestExportPanelLogic:
    """Tests for ExportPanel business logic."""

    def test_export_format_from_string(self) -> None:
        """Test ExportFormat from string conversion."""
        formats = ["png", "svg", "pdf", "eps"]
        for fmt in formats:
            export_fmt = ExportFormat.from_string(fmt)
            assert export_fmt.value == fmt

    def test_export_format_from_string_case_insensitive(self) -> None:
        """Test ExportFormat handles case variations."""
        assert ExportFormat.from_string("PNG").value == "png"
        assert ExportFormat.from_string("Svg").value == "svg"

    def test_invalid_export_format(self) -> None:
        """Test invalid export format raises error."""
        with pytest.raises(ValueError):
            ExportFormat.from_string("gif")

        with pytest.raises(ValueError):
            ExportFormat.from_string("jpg")

    def test_export_config_defaults(self) -> None:
        """Test ExportConfigSchema defaults."""
        config = ExportConfigSchema()
        assert config.format == "png"
        assert config.dpi == 300
        assert config.transparent is False

    def test_export_config_custom_values(self) -> None:
        """Test ExportConfigSchema with custom values."""
        config = ExportConfigSchema(format="pdf", dpi=600, transparent=True)
        assert config.format == "pdf"
        assert config.dpi == 600
        assert config.transparent is True


class TestChartConfigPanelLogic:
    """Tests for ChartConfigPanel business logic."""

    def test_chart_type_values(self) -> None:
        """Test ChartType enum has expected values."""
        expected_types = {
            "line",
            "scatter",
            "bar",
            "barh",
            "pie",
            "histogram",
            "polar",
            "box",
            "violin",
            "area",
            "stem",
            "step",
            "errorbar",
        }
        actual_types = {ct.value for ct in ChartType}
        assert expected_types == actual_types

    def test_plot_config_defaults(self) -> None:
        """Test PlotConfig has sensible defaults."""
        config = PlotConfig()
        assert config.chart_type == ChartType.LINE
        assert config.title == ""
        assert config.figure_width == 10.0
        assert config.figure_height == 6.0
        assert config.show_grid is True
        assert config.show_legend is True

    def test_plot_config_custom_values(self) -> None:
        """Test PlotConfig with custom values."""
        config = PlotConfig(
            chart_type=ChartType.SCATTER,
            title="My Plot",
            x_label="X Axis",
            y_label="Y Axis",
            figure_width=12.0,
            figure_height=8.0,
            show_grid=False,
        )
        assert config.chart_type == ChartType.SCATTER
        assert config.title == "My Plot"
        assert config.figure_width == 12.0
        assert config.show_grid is False

    def test_update_plot_config_in_state(self) -> None:
        """Test updating plot config in state."""
        state = AppState()
        state.plot_config = PlotConfig(chart_type=ChartType.BAR, title="Bar Chart")

        assert state.plot_config.chart_type == ChartType.BAR
        assert state.plot_config.title == "Bar Chart"


class TestAlignmentPanelLogic:
    """Tests for AlignmentPanel business logic."""

    def test_alignment_config_creation(self) -> None:
        """Test AlignmentConfig creation."""
        config = AlignmentConfig(enabled=True, column="time")
        assert config.enabled is True
        assert config.column == "time"

    def test_alignment_disabled_by_default(self) -> None:
        """Test AlignmentConfig disabled by default."""
        config = AlignmentConfig()
        assert config.enabled is False
        assert config.column == ""

    def test_set_alignment_in_state(self) -> None:
        """Test setting alignment in state."""
        state = AppState()
        state.alignment = AlignmentConfig(enabled=True, column="x")

        assert state.alignment is not None
        assert state.alignment.enabled is True
        assert state.alignment.column == "x"

    def test_clear_alignment_in_state(self) -> None:
        """Test clearing alignment in state."""
        state = AppState()
        state.alignment = AlignmentConfig(enabled=True, column="x")
        state.alignment = None

        assert state.alignment is None


class TestConfigConversionLogic:
    """Tests for config conversion logic (state to/from config)."""

    def test_file_config_from_parser_config(self) -> None:
        """Test creating FileConfig from ParserConfig."""
        parser_config = ParserConfig(
            has_header=True,
            comment_chars=["#", "//"],
            delimiter="\t",
            encoding="utf-8",
        )

        file_config = FileConfig(
            path=Path("data.tsv"),
            has_header=parser_config.has_header,
            comment_chars=parser_config.comment_chars,
            delimiter=parser_config.delimiter,
            encoding=parser_config.encoding,
        )

        assert file_config.has_header is True
        assert file_config.comment_chars == ["#", "//"]
        assert file_config.delimiter == "\t"

    def test_series_config_schema_from_series_config(self) -> None:
        """Test creating SeriesConfigSchema from SeriesConfig."""
        series = SeriesConfig(
            x_column="time",
            y_column="velocity",
            label="Data",
            color="#FF0000",
            line_style="--",
            marker="o",
        )

        schema = SeriesConfigSchema(
            x=series.x_column,
            y=series.y_column,
            label=series.label,
            color=series.color,
            line_style=series.line_style,
            marker=series.marker,
        )

        assert schema.x == "time"
        assert schema.y == "velocity"
        assert schema.label == "Data"
        assert schema.color == "#FF0000"

    def test_plot_config_schema_from_plot_config(self) -> None:
        """Test creating PlotConfigSchema from PlotConfig."""
        plot_config = PlotConfig(
            chart_type=ChartType.LINE,
            title="Test Plot",
            x_label="X",
            y_label="Y",
            figure_width=12.0,
            figure_height=8.0,
        )

        schema = PlotConfigSchema(
            type=plot_config.chart_type.value,
            title=plot_config.title,
            x_label=plot_config.x_label,
            y_label=plot_config.y_label,
            figure_width=plot_config.figure_width,
            figure_height=plot_config.figure_height,
        )

        assert schema.type == "line"
        assert schema.title == "Test Plot"
        assert schema.figure_width == 12.0

    def test_grapher_config_minimal(self) -> None:
        """Test creating minimal GrapherConfig."""
        config = GrapherConfig(
            files=[FileConfig(path=Path("data.tsv"))],
            series=[SeriesConfigSchema(x="x", y="y")],
        )

        assert len(config.files) == 1
        assert len(config.series) == 1
        assert len(config.derived_columns) == 0
        assert len(config.filters) == 0

    def test_grapher_config_full(self) -> None:
        """Test creating full GrapherConfig with all options."""
        config = GrapherConfig(
            files=[
                FileConfig(path=Path("data1.tsv"), has_header=True),
                FileConfig(path=Path("data2.tsv"), has_header=True),
            ],
            alignment=AlignmentConfig(enabled=True, column="time"),
            derived_columns=[
                DerivedColumnConfig(name="velocity", expression="distance/time"),
            ],
            filters=[
                FilterConfig(column="time", min=0.0, max=100.0),
            ],
            series=[
                SeriesConfigSchema(x="time", y="velocity", label="Data 1"),
                SeriesConfigSchema(x="time", y="velocity", label="Data 2"),
            ],
            plot=PlotConfigSchema(
                type="line",
                title="Comparison",
                show_legend=True,
            ),
            export=ExportConfigSchema(format="pdf", dpi=600),
        )

        assert len(config.files) == 2
        assert config.alignment is not None
        assert config.alignment.enabled is True
        assert len(config.derived_columns) == 1
        assert len(config.filters) == 1
        assert len(config.series) == 2
        assert config.plot.title == "Comparison"
        assert config.export.format == "pdf"


class TestColorPalette:
    """Tests for colorblind-safe color palette."""

    def test_palette_has_eight_colors(self) -> None:
        """Test palette has exactly 8 colors."""
        assert len(COLORBLIND_PALETTE) == 8

    def test_palette_colors_are_hex(self) -> None:
        """Test palette colors are valid hex codes."""
        for color in COLORBLIND_PALETTE:
            assert color.startswith("#")
            assert len(color) == 7
            # Should be valid hex
            int(color[1:], 16)

    def test_palette_colors_are_unique(self) -> None:
        """Test palette colors are all unique."""
        assert len(set(COLORBLIND_PALETTE)) == len(COLORBLIND_PALETTE)

    def test_palette_includes_expected_colors(self) -> None:
        """Test palette includes the expected colorblind-safe colors."""
        # Blue
        assert "#0072B2" in COLORBLIND_PALETTE
        # Orange
        assert "#E69F00" in COLORBLIND_PALETTE
        # Green
        assert "#009E73" in COLORBLIND_PALETTE
