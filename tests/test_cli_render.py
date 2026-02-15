"""Tests for CLI render command (headless mode)."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from plottini.cli import cli


class TestRenderCommand:
    """Tests for the render subcommand."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def simple_data(self, tmp_path: Path) -> Path:
        """Create simple TSV data file."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("time\tvalue\n0.0\t1.0\n1.0\t2.0\n2.0\t4.0\n3.0\t8.0\n")
        return data_path

    @pytest.fixture
    def multi_block_data(self, tmp_path: Path) -> Path:
        """Create multi-block TSV data file."""
        data_path = tmp_path / "multi_block.tsv"
        data_path.write_text(
            "# Block 1\n"
            "time\tvalue\n"
            "0.0\t1.0\n"
            "1.0\t2.0\n"
            "\n"
            "# Block 2\n"
            "time\tvalue\n"
            "0.0\t10.0\n"
            "1.0\t20.0\n"
        )
        return data_path

    @pytest.fixture
    def simple_config(self, tmp_path: Path, simple_data: Path) -> Path:
        """Create simple config file."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{simple_data}"
has_header = true
comment_chars = ["#"]

[[series]]
x = "time"
y = "value"
label = "Data"

[plot]
type = "line"
title = "Test Plot"
x_label = "Time"
y_label = "Value"

[export]
format = "png"
dpi = 150
""")
        return config_path

    def test_render_basic(self, runner: CliRunner, simple_config: Path, tmp_path: Path) -> None:
        """Test basic render command."""
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(simple_config), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        assert "Loading configuration from" in result.output
        assert "Rendering plot" in result.output
        assert "Graph exported to" in result.output

    def test_render_format_override(
        self, runner: CliRunner, simple_config: Path, tmp_path: Path
    ) -> None:
        """Test render with format override from CLI."""
        output_path = tmp_path / "output.svg"
        result = runner.invoke(
            cli,
            [
                "render",
                "--config",
                str(simple_config),
                "--output",
                str(output_path),
                "--format",
                "svg",
            ],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()
        # SVG is text-based XML
        content = output_path.read_text()
        assert "<svg" in content

    def test_render_dpi_override(
        self, runner: CliRunner, simple_config: Path, tmp_path: Path
    ) -> None:
        """Test render with DPI override from CLI."""
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            [
                "render",
                "--config",
                str(simple_config),
                "--output",
                str(output_path),
                "--dpi",
                "300",
            ],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()
        # Higher DPI = larger file
        assert output_path.stat().st_size > 0

    def test_render_pdf_format(
        self, runner: CliRunner, simple_config: Path, tmp_path: Path
    ) -> None:
        """Test render to PDF format."""
        output_path = tmp_path / "output.pdf"
        result = runner.invoke(
            cli,
            [
                "render",
                "--config",
                str(simple_config),
                "--output",
                str(output_path),
                "--format",
                "pdf",
            ],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()
        # PDF starts with %PDF
        content = output_path.read_bytes()
        assert content[:4] == b"%PDF"

    def test_render_eps_format(
        self, runner: CliRunner, simple_config: Path, tmp_path: Path
    ) -> None:
        """Test render to EPS format."""
        output_path = tmp_path / "output.eps"
        result = runner.invoke(
            cli,
            [
                "render",
                "--config",
                str(simple_config),
                "--output",
                str(output_path),
                "--format",
                "eps",
            ],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()

    def test_render_missing_config(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render fails with missing config file."""
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            [
                "render",
                "--config",
                str(tmp_path / "nonexistent.toml"),
                "--output",
                str(output_path),
            ],
        )

        assert result.exit_code != 0

    def test_render_missing_data_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render fails when data file doesn't exist."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[[files]]
path = "nonexistent.tsv"

[[series]]
x = "time"
y = "value"

[plot]
type = "line"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        # Should fail because data file doesn't exist
        assert result.exit_code != 0


class TestRenderWithDerivedColumns:
    """Tests for render with derived columns."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def data_file(self, tmp_path: Path) -> Path:
        """Create TSV data file with multiple columns."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("time\tdistance\n1.0\t10.0\n2.0\t40.0\n3.0\t90.0\n4.0\t160.0\n")
        return data_path

    def test_render_with_derived_column(
        self, runner: CliRunner, data_file: Path, tmp_path: Path
    ) -> None:
        """Test render with derived column expression."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_file}"
has_header = true

[[derived_columns]]
name = "velocity"
expression = "distance / time"

[[series]]
x = "time"
y = "velocity"
label = "Velocity"

[plot]
type = "line"
title = "Derived Column Test"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()

    def test_render_invalid_derived_column_warns(
        self, runner: CliRunner, data_file: Path, tmp_path: Path
    ) -> None:
        """Test render with invalid derived column shows warning."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_file}"
has_header = true

[[derived_columns]]
name = "invalid"
expression = "nonexistent_column * 2"

[[series]]
x = "time"
y = "distance"
label = "Distance"

[plot]
type = "line"
title = "Invalid Derived Column Test"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        # Should still succeed but with warning
        assert "Warning" in result.output or "Could not create derived column" in result.output


class TestRenderWithFilters:
    """Tests for render with data filters."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def data_file(self, tmp_path: Path) -> Path:
        """Create TSV data file."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text(
            "time\tvalue\n0.0\t1.0\n1.0\t2.0\n2.0\t3.0\n3.0\t4.0\n4.0\t5.0\n5.0\t6.0\n"
        )
        return data_path

    def test_render_with_filter(self, runner: CliRunner, data_file: Path, tmp_path: Path) -> None:
        """Test render with row filter."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_file}"
has_header = true

[[filters]]
column = "time"
min = 1.0
max = 4.0

[[series]]
x = "time"
y = "value"
label = "Filtered Data"

[plot]
type = "line"
title = "Filtered Data Test"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()


class TestRenderChartTypes:
    """Tests for render with various chart types."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def data_file(self, tmp_path: Path) -> Path:
        """Create TSV data file."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text(
            "category\tvalue\n1.0\t10.0\n2.0\t20.0\n3.0\t30.0\n4.0\t25.0\n5.0\t15.0\n"
        )
        return data_path

    @pytest.mark.parametrize(
        "chart_type",
        ["line", "scatter", "bar", "area", "step", "stem"],
    )
    def test_render_chart_type(
        self, runner: CliRunner, data_file: Path, tmp_path: Path, chart_type: str
    ) -> None:
        """Test render with various chart types."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_file}"
has_header = true

[[series]]
x = "category"
y = "value"
label = "{chart_type.capitalize()} Chart"

[plot]
type = "{chart_type}"
title = "{chart_type.capitalize()} Chart Test"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error for {chart_type}: {result.output}"
        assert output_path.exists()

    def test_render_histogram(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render histogram chart type."""
        data_path = tmp_path / "histogram_data.tsv"
        import random

        data_path.write_text(
            "value\n" + "\n".join(f"{random.gauss(50, 10):.2f}" for _ in range(100))
        )
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[[series]]
x = "value"
y = "value"
label = "Distribution"

[plot]
type = "histogram"
title = "Histogram Test"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()

    def test_render_pie_chart(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render pie chart type."""
        data_path = tmp_path / "pie_data.tsv"
        data_path.write_text("category\tvalue\n1\t30.0\n2\t20.0\n3\t25.0\n4\t15.0\n5\t10.0\n")
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[[series]]
x = "category"
y = "value"
label = "Distribution"

[plot]
type = "pie"
title = "Pie Chart Test"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()


class TestRenderMultipleSeries:
    """Tests for render with multiple series."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_render_multiple_series(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render with multiple series on same plot."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text(
            "time\tseries1\tseries2\n0.0\t1.0\t2.0\n1.0\t2.0\t3.0\n2.0\t4.0\t5.0\n3.0\t8.0\t7.0\n"
        )
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[[series]]
x = "time"
y = "series1"
label = "Series 1"
color = "#0072B2"

[[series]]
x = "time"
y = "series2"
label = "Series 2"
color = "#E69F00"

[plot]
type = "line"
title = "Multiple Series Test"
show_legend = true
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()

    def test_render_secondary_y_axis(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render with secondary Y-axis."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text(
            "time\ttemperature\tpressure\n"
            "0.0\t20.0\t1013.0\n"
            "1.0\t22.0\t1012.0\n"
            "2.0\t25.0\t1010.0\n"
            "3.0\t23.0\t1011.0\n"
        )
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[[series]]
x = "time"
y = "temperature"
label = "Temperature"
use_secondary_y = false

[[series]]
x = "time"
y = "pressure"
label = "Pressure"
use_secondary_y = true

[plot]
type = "line"
title = "Dual Y-Axis Test"
y_label = "Temperature (C)"
y2_label = "Pressure (hPa)"
show_legend = true
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()


class TestRenderMultiBlockFiles:
    """Tests for render with multi-block TSV files."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_render_multi_block_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render with multi-block TSV file."""
        data_path = tmp_path / "multi_block.tsv"
        data_path.write_text(
            "# First data block\n"
            "time\tvalue\n"
            "0.0\t1.0\n"
            "1.0\t2.0\n"
            "\n"
            "# Second data block\n"
            "time\tvalue\n"
            "0.0\t10.0\n"
            "1.0\t20.0\n"
        )
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[[series]]
x = "time"
y = "value"
label = "Block 1"
source_file_index = 0

[[series]]
x = "time"
y = "value"
label = "Block 2"
source_file_index = 1

[plot]
type = "line"
title = "Multi-Block Test"
show_legend = true
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code == 0, f"Error: {result.output}"
        assert output_path.exists()
        assert "Found 2 data blocks" in result.output


class TestRenderErrorHandling:
    """Tests for render command error handling."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_render_no_series_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render fails with no series defined."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("time\tvalue\n1.0\t2.0\n")
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[plot]
type = "line"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code != 0
        assert "No series defined" in result.output

    def test_render_no_files_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render fails with no files defined."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[[series]]
x = "time"
y = "value"

[plot]
type = "line"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        assert result.exit_code != 0
        assert "No data files" in result.output

    def test_render_invalid_column_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test render fails with invalid column name."""
        data_path = tmp_path / "data.tsv"
        data_path.write_text("time\tvalue\n1.0\t2.0\n")
        config_path = tmp_path / "config.toml"
        config_path.write_text(f"""
[[files]]
path = "{data_path}"
has_header = true

[[series]]
x = "time"
y = "nonexistent"

[plot]
type = "line"
""")
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            cli,
            ["render", "--config", str(config_path), "--output", str(output_path)],
        )

        # Should fail because column doesn't exist
        assert result.exit_code != 0
