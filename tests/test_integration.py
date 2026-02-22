"""Integration tests for Plottini.

These tests verify complete workflows from data loading to export.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from plottini.core.dataframe import DataFrame, align_dataframes
from plottini.core.exporter import ExportConfig, Exporter, ExportFormat
from plottini.core.parser import ParserConfig, TSVParser
from plottini.core.plotter import ChartType, PlotConfig, Plotter, SeriesConfig


class TestBasicWorkflow:
    """Test basic data loading to export workflow."""

    @pytest.fixture
    def sample_data_file(self, tmp_path: Path) -> Path:
        """Create sample TSV data file."""
        data_path = tmp_path / "sample.tsv"
        data_path.write_text(
            "time\tposition\tvelocity\n"
            "0.0\t0.0\t0.0\n"
            "1.0\t4.9\t9.8\n"
            "2.0\t19.6\t19.6\n"
            "3.0\t44.1\t29.4\n"
            "4.0\t78.4\t39.2\n"
        )
        return data_path

    def test_load_transform_plot_export(self, sample_data_file: Path, tmp_path: Path) -> None:
        """Test complete workflow: load, transform, plot, export."""
        # 1. Parse TSV file
        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(sample_data_file)

        # Verify parsing
        assert len(df) == 5
        assert "time" in df
        assert "position" in df
        assert "velocity" in df

        # 2. Add derived column
        df.add_derived_column("kinetic_energy", "0.5 * velocity ** 2")
        assert "kinetic_energy" in df
        assert df.columns["kinetic_energy"].is_derived is True

        # 3. Create plot
        series = [
            SeriesConfig(x_column="time", y_column="position", label="Position"),
            SeriesConfig(x_column="time", y_column="velocity", label="Velocity"),
        ]
        plot_config = PlotConfig(
            chart_type=ChartType.LINE,
            title="Motion Analysis",
            x_label="Time (s)",
            y_label="Value",
            show_legend=True,
        )
        plotter = Plotter(plot_config)
        fig = plotter.create_figure(df, series)

        assert fig is not None

        # 4. Export to multiple formats
        exporter = Exporter()

        # PNG
        png_path = tmp_path / "output.png"
        exporter.export(fig, png_path, ExportConfig(format=ExportFormat.PNG))
        assert png_path.exists()
        assert png_path.stat().st_size > 0

        # SVG
        svg_path = tmp_path / "output.svg"
        exporter.export(fig, svg_path, ExportConfig(format=ExportFormat.SVG))
        assert svg_path.exists()
        assert "<svg" in svg_path.read_text()

    def test_workflow_with_filtering(self, sample_data_file: Path, tmp_path: Path) -> None:
        """Test workflow with row filtering."""
        # Parse
        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(sample_data_file)

        # Filter rows where time >= 1.0 and time <= 3.0
        filtered = df.filter_rows("time", min_val=1.0, max_val=3.0)

        assert len(filtered) == 3  # time 1.0, 2.0, 3.0
        assert filtered["time"].data[0] == 1.0
        assert filtered["time"].data[-1] == 3.0

        # Plot and export filtered data
        series = [SeriesConfig(x_column="time", y_column="velocity", label="Velocity")]
        plotter = Plotter(PlotConfig(chart_type=ChartType.LINE, title="Filtered Data"))
        fig = plotter.create_figure(filtered, series)

        exporter = Exporter()
        output_path = tmp_path / "filtered.png"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.PNG))
        assert output_path.exists()


class TestMultiFileWorkflow:
    """Test workflows with multiple data files."""

    @pytest.fixture
    def experiment1_file(self, tmp_path: Path) -> Path:
        """Create first experiment data file."""
        data_path = tmp_path / "exp1.tsv"
        data_path.write_text(
            "time\tmeasurement\n0.0\t10.0\n0.5\t12.0\n1.0\t15.0\n1.5\t14.0\n2.0\t16.0\n"
        )
        return data_path

    @pytest.fixture
    def experiment2_file(self, tmp_path: Path) -> Path:
        """Create second experiment data file."""
        data_path = tmp_path / "exp2.tsv"
        data_path.write_text(
            "time\tmeasurement\n0.0\t8.0\n0.5\t10.0\n1.0\t13.0\n1.5\t12.0\n2.0\t14.0\n"
        )
        return data_path

    def test_multiple_files_overlay(
        self, experiment1_file: Path, experiment2_file: Path, tmp_path: Path
    ) -> None:
        """Test loading and plotting multiple files overlaid."""
        parser = TSVParser(ParserConfig(has_header=True))

        # Parse both files
        df1 = parser.parse(experiment1_file)
        df2 = parser.parse(experiment2_file)

        # Create overlaid plot
        series = [
            SeriesConfig(
                x_column="time",
                y_column="measurement",
                label="Experiment 1",
                source_file_index=0,
                color="#0072B2",
            ),
            SeriesConfig(
                x_column="time",
                y_column="measurement",
                label="Experiment 2",
                source_file_index=1,
                color="#E69F00",
            ),
        ]

        plotter = Plotter(
            PlotConfig(
                chart_type=ChartType.LINE,
                title="Experiment Comparison",
                show_legend=True,
            )
        )
        fig = plotter.create_figure([df1, df2], series)

        exporter = Exporter()
        output_path = tmp_path / "comparison.png"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.PNG))
        assert output_path.exists()

    def test_multiple_files_alignment(self, tmp_path: Path) -> None:
        """Test aligning multiple files by common column.

        Note: align_dataframes computes range metadata but doesn't
        filter data - it keeps original data intact for plotting.
        """
        # Create files with different time points
        file1 = tmp_path / "data1.tsv"
        file1.write_text("time\tvalue\n0.0\t1.0\n1.0\t2.0\n2.0\t3.0\n3.0\t4.0\n4.0\t5.0\n")

        file2 = tmp_path / "data2.tsv"
        file2.write_text("time\tvalue\n1.0\t10.0\n2.0\t20.0\n3.0\t30.0\n")

        parser = TSVParser(ParserConfig(has_header=True))
        df1 = parser.parse(file1)
        df2 = parser.parse(file2)

        # Align by time column - computes range metadata
        aligned = align_dataframes([df1, df2], align_column="time")

        # Original DataFrames are retained unmodified
        assert len(aligned.dataframes[0]) == 5  # All original rows
        assert len(aligned.dataframes[1]) == 3  # All original rows

        # Alignment computes union range for consistent x-axis
        assert aligned.align_column == "time"
        assert aligned.x_min == 0.0  # Min across both files
        assert aligned.x_max == 4.0  # Max across both files


class TestAllChartTypes:
    """Test integration with all supported chart types."""

    @pytest.fixture
    def sample_data(self, tmp_path: Path) -> DataFrame:
        """Create sample DataFrame."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("x\ty\n1\t10\n2\t25\n3\t15\n4\t30\n5\t20\n")
        parser = TSVParser(ParserConfig(has_header=True))
        return parser.parse(data_path)

    @pytest.mark.parametrize(
        "chart_type",
        [
            ChartType.LINE,
            ChartType.SCATTER,
            ChartType.BAR,
            ChartType.BAR_HORIZONTAL,
            ChartType.AREA,
            ChartType.STEP,
            ChartType.STEM,
        ],
    )
    def test_export_chart_type(
        self, sample_data: DataFrame, tmp_path: Path, chart_type: ChartType
    ) -> None:
        """Test exporting each chart type."""
        series = [SeriesConfig(x_column="x", y_column="y", label="Data")]
        plotter = Plotter(PlotConfig(chart_type=chart_type, title=f"{chart_type.value} Chart"))
        fig = plotter.create_figure(sample_data, series)

        exporter = Exporter()
        output_path = tmp_path / f"{chart_type.value}.png"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.PNG))

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestSecondaryYAxis:
    """Test secondary Y-axis functionality."""

    def test_dual_axis_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow with dual Y-axis."""
        # Create data with two different scales
        data_path = tmp_path / "dual_axis.tsv"
        data_path.write_text(
            "time\ttemperature\tpressure\n"
            "0\t20.0\t1013.0\n"
            "1\t22.5\t1011.0\n"
            "2\t25.0\t1009.0\n"
            "3\t23.0\t1010.0\n"
            "4\t21.0\t1012.0\n"
        )

        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(data_path)

        series = [
            SeriesConfig(
                x_column="time",
                y_column="temperature",
                label="Temperature",
                use_secondary_y=False,
            ),
            SeriesConfig(
                x_column="time",
                y_column="pressure",
                label="Pressure",
                use_secondary_y=True,
            ),
        ]

        plotter = Plotter(
            PlotConfig(
                chart_type=ChartType.LINE,
                title="Weather Data",
                y_label="Temperature (°C)",
                y2_label="Pressure (hPa)",
                show_legend=True,
            )
        )
        fig = plotter.create_figure(df, series)

        exporter = Exporter()
        output_path = tmp_path / "dual_axis.png"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.PNG))

        assert output_path.exists()


class TestMultiBlockFiles:
    """Test multi-block TSV file handling."""

    def test_multi_block_parsing_and_plotting(self, tmp_path: Path) -> None:
        """Test parsing multi-block files and plotting each block."""
        # Create multi-block file
        data_path = tmp_path / "multi_block.tsv"
        data_path.write_text(
            "# Dataset 1: Morning\n"
            "time\ttemperature\n"
            "6\t15.0\n"
            "7\t17.0\n"
            "8\t20.0\n"
            "9\t22.0\n"
            "\n"
            "# Dataset 2: Evening\n"
            "time\ttemperature\n"
            "18\t25.0\n"
            "19\t22.0\n"
            "20\t19.0\n"
            "21\t17.0\n"
        )

        parser = TSVParser(ParserConfig(has_header=True))
        blocks = parser.parse_blocks(data_path)

        # Should have 2 blocks
        assert len(blocks) == 2
        assert blocks[0].block_index == 0
        assert blocks[1].block_index == 1

        # Each block should have correct data
        assert len(blocks[0]) == 4
        assert len(blocks[1]) == 4

        # Plot both blocks
        series = [
            SeriesConfig(
                x_column="time",
                y_column="temperature",
                label="Morning",
                source_file_index=0,
            ),
            SeriesConfig(
                x_column="time",
                y_column="temperature",
                label="Evening",
                source_file_index=1,
            ),
        ]

        plotter = Plotter(
            PlotConfig(
                chart_type=ChartType.LINE,
                title="Temperature Comparison",
                show_legend=True,
            )
        )
        fig = plotter.create_figure(blocks, series)

        exporter = Exporter()
        output_path = tmp_path / "multi_block.png"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.PNG))

        assert output_path.exists()


class TestDerivedColumnsWorkflow:
    """Test derived column creation and usage."""

    def test_complex_expression_workflow(self, tmp_path: Path) -> None:
        """Test workflow with complex derived expressions."""
        # Start time at 1 to avoid division by zero
        data_path = tmp_path / "physics.tsv"
        data_path.write_text("time\tx\ty\n1\t3.0\t4.0\n2\t6.0\t8.0\n3\t9.0\t12.0\n4\t12.0\t16.0\n")

        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(data_path)

        # Add multiple derived columns
        df.add_derived_column("distance", "sqrt(x**2 + y**2)")
        df.add_derived_column("velocity", "distance / time")

        # Verify calculations
        assert "distance" in df
        assert "velocity" in df

        # distance at time=1 should be 5 (3-4-5 triangle)
        np.testing.assert_almost_equal(df["distance"][0], 5.0, decimal=5)

        # velocity at time=1 should be 5/1 = 5
        np.testing.assert_almost_equal(df["velocity"][0], 5.0, decimal=5)

        # Plot the derived data
        series = [
            SeriesConfig(x_column="time", y_column="distance", label="Distance"),
            SeriesConfig(x_column="time", y_column="velocity", label="Velocity"),
        ]

        plotter = Plotter(
            PlotConfig(
                chart_type=ChartType.LINE,
                title="Derived Columns Test",
                show_legend=True,
            )
        )
        fig = plotter.create_figure(df, series)

        exporter = Exporter()
        output_path = tmp_path / "derived.png"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.PNG))

        assert output_path.exists()

    def test_filter_on_derived_column(self, tmp_path: Path) -> None:
        """Test filtering data based on derived column."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("x\ty\n1\t2\n2\t4\n3\t6\n4\t8\n5\t10\n")

        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(data_path)

        # Create derived column
        df.add_derived_column("product", "x * y")

        # Filter on derived column (product > 10)
        filtered = df.filter_rows("product", min_val=10.0)

        # Should have rows where x*y > 10: (3,6)=18, (4,8)=32, (5,10)=50
        assert len(filtered) == 3
        assert "product" in filtered  # Derived column should be preserved


class TestErrorRecovery:
    """Test error handling and recovery scenarios."""

    def test_invalid_file_doesnt_affect_valid_files(self, tmp_path: Path) -> None:
        """Test that one invalid file doesn't prevent loading valid ones."""
        # Create valid file
        valid_file = tmp_path / "valid.tsv"
        valid_file.write_text("x\ty\n1\t2\n3\t4\n")

        parser = TSVParser(ParserConfig(has_header=True))

        # Parse valid file
        df = parser.parse(valid_file)
        assert len(df) == 2

        # Try to parse invalid file
        invalid_file = tmp_path / "invalid.tsv"
        invalid_file.write_text("x\ty\n1\ttext\n")  # Non-numeric value

        from plottini.utils.errors import ParseError

        with pytest.raises(ParseError):
            parser.parse(invalid_file)

        # Valid file should still work after error
        df2 = parser.parse(valid_file)
        assert len(df2) == 2

    def test_invalid_expression_handled(self, tmp_path: Path) -> None:
        """Test that invalid expressions are handled gracefully."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("x\ty\n1\t2\n3\t4\n")

        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(data_path)

        # Try to add invalid derived column
        from plottini.utils.errors import ExpressionError

        with pytest.raises(ExpressionError):
            df.add_derived_column("invalid", "nonexistent_column * 2")

        # DataFrame should still be usable
        assert len(df) == 2
        assert "x" in df
        assert "y" in df

        # Valid expression should still work
        df.add_derived_column("sum", "x + y")
        assert "sum" in df


class TestEndToEndWorkflows:
    """End-to-end workflow tests."""

    def test_workflow_transform_filter_export(self, tmp_path: Path) -> None:
        """Test workflow with transforms and filters."""
        # Create data
        data_path = tmp_path / "velocity.tsv"
        data_path.write_text(
            "time\tdistance\n1.0\t10.0\n2.0\t40.0\n3.0\t90.0\n4.0\t160.0\n5.0\t250.0\n"
        )

        # Parse
        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(data_path)

        # Add derived column
        df.add_derived_column("velocity", "distance / time")

        # Filter (time >= 2 and time <= 4)
        filtered = df.filter_rows("time", min_val=2.0, max_val=4.0)

        # Verify
        assert len(filtered) == 3
        assert "velocity" in filtered

        # Plot and export
        series = [SeriesConfig(x_column="time", y_column="velocity", label="Velocity")]
        plotter = Plotter(PlotConfig(chart_type=ChartType.LINE))
        fig = plotter.create_figure(filtered, series)

        exporter = Exporter()
        output_path = tmp_path / "velocity.svg"
        exporter.export(fig, output_path, ExportConfig(format=ExportFormat.SVG))

        assert output_path.exists()
        assert "<svg" in output_path.read_text()

    def test_workflow_multi_file_comparison(self, tmp_path: Path) -> None:
        """Test workflow comparing data from multiple files."""
        # Create two experiment files
        exp1_path = tmp_path / "experiment1.tsv"
        exp1_path.write_text("time\tvalue\n0\t10\n1\t20\n2\t30\n3\t40\n")

        exp2_path = tmp_path / "experiment2.tsv"
        exp2_path.write_text("time\tvalue\n0\t12\n1\t22\n2\t32\n3\t42\n")

        # Parse both
        parser = TSVParser(ParserConfig(has_header=True))
        df1 = parser.parse(exp1_path)
        df2 = parser.parse(exp2_path)

        # Plot comparison
        series = [
            SeriesConfig(x_column="time", y_column="value", label="Exp 1", source_file_index=0),
            SeriesConfig(x_column="time", y_column="value", label="Exp 2", source_file_index=1),
        ]
        plotter = Plotter(
            PlotConfig(chart_type=ChartType.LINE, title="Comparison", show_legend=True)
        )
        fig = plotter.create_figure([df1, df2], series)

        # Export to multiple formats
        exporter = Exporter()
        formats = [ExportFormat.PNG, ExportFormat.PDF]
        results = exporter.export_multiple(fig, tmp_path / "comparison", formats)

        assert len(results) == 2
        assert all(p.exists() for p in results)
