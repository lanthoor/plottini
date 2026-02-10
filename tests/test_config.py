"""Tests for configuration schema module."""

from __future__ import annotations

from pathlib import Path

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


class TestFileConfig:
    """Tests for FileConfig dataclass."""

    def test_file_config_defaults(self):
        """Test FileConfig default values."""
        config = FileConfig(path=Path("data.tsv"))
        assert config.path == Path("data.tsv")
        assert config.has_header is True
        assert config.comment_chars == ["#"]
        assert config.delimiter == "\t"
        assert config.encoding == "utf-8"

    def test_file_config_custom_values(self):
        """Test FileConfig with custom values."""
        config = FileConfig(
            path=Path("data.csv"),
            has_header=False,
            comment_chars=["#", "//"],
            delimiter=",",
            encoding="latin-1",
        )
        assert config.path == Path("data.csv")
        assert config.has_header is False
        assert config.comment_chars == ["#", "//"]
        assert config.delimiter == ","
        assert config.encoding == "latin-1"


class TestAlignmentConfig:
    """Tests for AlignmentConfig dataclass."""

    def test_alignment_config_defaults(self):
        """Test AlignmentConfig default values."""
        config = AlignmentConfig()
        assert config.enabled is False
        assert config.column == ""

    def test_alignment_config_enabled(self):
        """Test AlignmentConfig with alignment enabled."""
        config = AlignmentConfig(enabled=True, column="time")
        assert config.enabled is True
        assert config.column == "time"


class TestDerivedColumnConfig:
    """Tests for DerivedColumnConfig dataclass."""

    def test_derived_column_config(self):
        """Test DerivedColumnConfig creation."""
        config = DerivedColumnConfig(name="velocity", expression="distance / time")
        assert config.name == "velocity"
        assert config.expression == "distance / time"


class TestFilterConfig:
    """Tests for FilterConfig dataclass."""

    def test_filter_config_defaults(self):
        """Test FilterConfig default values."""
        config = FilterConfig(column="time")
        assert config.column == "time"
        assert config.min is None
        assert config.max is None

    def test_filter_config_with_bounds(self):
        """Test FilterConfig with min and max bounds."""
        config = FilterConfig(column="time", min=0.0, max=100.0)
        assert config.column == "time"
        assert config.min == 0.0
        assert config.max == 100.0

    def test_filter_config_min_only(self):
        """Test FilterConfig with only min bound."""
        config = FilterConfig(column="temperature", min=-273.15)
        assert config.min == -273.15
        assert config.max is None


class TestSeriesConfigSchema:
    """Tests for SeriesConfigSchema dataclass."""

    def test_series_config_defaults(self):
        """Test SeriesConfigSchema default values."""
        config = SeriesConfigSchema(x="time", y="value")
        assert config.x == "time"
        assert config.y == "value"
        assert config.label is None
        assert config.color is None
        assert config.line_style == "-"
        assert config.marker is None
        assert config.line_width == 1.5
        assert config.use_secondary_y is False
        assert config.source_file_index == 0

    def test_series_config_custom_values(self):
        """Test SeriesConfigSchema with custom values."""
        config = SeriesConfigSchema(
            x="time",
            y="temperature",
            label="Temperature",
            color="#FF0000",
            line_style="--",
            marker="o",
            line_width=2.0,
            use_secondary_y=True,
            source_file_index=1,
        )
        assert config.x == "time"
        assert config.y == "temperature"
        assert config.label == "Temperature"
        assert config.color == "#FF0000"
        assert config.line_style == "--"
        assert config.marker == "o"
        assert config.line_width == 2.0
        assert config.use_secondary_y is True
        assert config.source_file_index == 1


class TestPlotConfigSchema:
    """Tests for PlotConfigSchema dataclass."""

    def test_plot_config_defaults(self):
        """Test PlotConfigSchema default values."""
        config = PlotConfigSchema()
        assert config.type == "line"
        assert config.title == ""
        assert config.x_label == ""
        assert config.y_label == ""
        assert config.y2_label == ""
        assert config.figure_width == 10.0
        assert config.figure_height == 6.0
        assert config.show_grid is True
        assert config.show_legend is True

    def test_plot_config_custom_values(self):
        """Test PlotConfigSchema with custom values."""
        config = PlotConfigSchema(
            type="scatter",
            title="My Plot",
            x_label="Time (s)",
            y_label="Value",
            y2_label="Secondary",
            figure_width=12.0,
            figure_height=8.0,
            show_grid=False,
            show_legend=False,
        )
        assert config.type == "scatter"
        assert config.title == "My Plot"
        assert config.x_label == "Time (s)"
        assert config.y_label == "Value"
        assert config.y2_label == "Secondary"
        assert config.figure_width == 12.0
        assert config.figure_height == 8.0
        assert config.show_grid is False
        assert config.show_legend is False


class TestExportConfigSchema:
    """Tests for ExportConfigSchema dataclass."""

    def test_export_config_defaults(self):
        """Test ExportConfigSchema default values."""
        config = ExportConfigSchema()
        assert config.format == "png"
        assert config.dpi == 300
        assert config.transparent is False

    def test_export_config_custom_values(self):
        """Test ExportConfigSchema with custom values."""
        config = ExportConfigSchema(format="pdf", dpi=600, transparent=True)
        assert config.format == "pdf"
        assert config.dpi == 600
        assert config.transparent is True


class TestGrapherConfig:
    """Tests for GrapherConfig dataclass."""

    def test_grapher_config_defaults(self):
        """Test GrapherConfig default values."""
        config = GrapherConfig()
        assert config.files == []
        assert config.alignment is None
        assert config.derived_columns == []
        assert config.filters == []
        assert config.series == []
        assert isinstance(config.plot, PlotConfigSchema)
        assert isinstance(config.export, ExportConfigSchema)

    def test_grapher_config_with_files(self):
        """Test GrapherConfig with file configurations."""
        files = [
            FileConfig(path=Path("data1.tsv")),
            FileConfig(path=Path("data2.tsv")),
        ]
        config = GrapherConfig(files=files)
        assert len(config.files) == 2
        assert config.files[0].path == Path("data1.tsv")
        assert config.files[1].path == Path("data2.tsv")

    def test_grapher_config_with_alignment(self):
        """Test GrapherConfig with alignment."""
        config = GrapherConfig(
            alignment=AlignmentConfig(enabled=True, column="time"),
        )
        assert config.alignment is not None
        assert config.alignment.enabled is True
        assert config.alignment.column == "time"

    def test_grapher_config_with_derived_columns(self):
        """Test GrapherConfig with derived columns."""
        config = GrapherConfig(
            derived_columns=[
                DerivedColumnConfig(name="velocity", expression="distance / time"),
                DerivedColumnConfig(name="acceleration", expression="velocity / time"),
            ],
        )
        assert len(config.derived_columns) == 2
        assert config.derived_columns[0].name == "velocity"
        assert config.derived_columns[1].name == "acceleration"

    def test_grapher_config_with_filters(self):
        """Test GrapherConfig with filters."""
        config = GrapherConfig(
            filters=[
                FilterConfig(column="time", min=0.0, max=100.0),
                FilterConfig(column="value", min=0.0),
            ],
        )
        assert len(config.filters) == 2

    def test_grapher_config_complete(self):
        """Test GrapherConfig with all options set."""
        config = GrapherConfig(
            files=[FileConfig(path=Path("data.tsv"))],
            alignment=AlignmentConfig(enabled=True, column="time"),
            derived_columns=[DerivedColumnConfig(name="v", expression="d/t")],
            filters=[FilterConfig(column="time", min=0.0)],
            series=[SeriesConfigSchema(x="time", y="value", label="Data")],
            plot=PlotConfigSchema(type="line", title="My Plot"),
            export=ExportConfigSchema(format="pdf", dpi=600),
        )
        assert len(config.files) == 1
        assert config.alignment is not None
        assert len(config.derived_columns) == 1
        assert len(config.filters) == 1
        assert len(config.series) == 1
        assert config.plot.title == "My Plot"
        assert config.export.format == "pdf"


class TestDefaults:
    """Tests for defaults module."""

    def test_default_constants(self):
        """Test that default constants have expected values."""
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
        )

        assert DEFAULT_COMMENT_CHARS == ["#"]
        assert DEFAULT_DELIMITER == "\t"
        assert DEFAULT_ENCODING == "utf-8"
        assert DEFAULT_HAS_HEADER is True
        assert DEFAULT_DPI == 300
        assert DEFAULT_EXPORT_FORMAT == "png"
        assert DEFAULT_TRANSPARENT is False
        assert DEFAULT_CHART_TYPE == "line"
        assert DEFAULT_FIGURE_WIDTH == 10.0
        assert DEFAULT_FIGURE_HEIGHT == 6.0
        assert DEFAULT_SHOW_GRID is True
        assert DEFAULT_SHOW_LEGEND is True

    def test_get_default_config(self):
        """Test get_default_config returns valid GrapherConfig."""
        from plottini.config.defaults import get_default_config

        config = get_default_config()
        assert isinstance(config, GrapherConfig)
        assert config.files == []
        assert config.alignment is None

    def test_get_default_plot_config(self):
        """Test get_default_plot_config returns valid PlotConfigSchema."""
        from plottini.config.defaults import get_default_plot_config

        config = get_default_plot_config()
        assert isinstance(config, PlotConfigSchema)
        assert config.type == "line"
        assert config.figure_width == 10.0

    def test_get_default_export_config(self):
        """Test get_default_export_config returns valid ExportConfigSchema."""
        from plottini.config.defaults import get_default_export_config

        config = get_default_export_config()
        assert isinstance(config, ExportConfigSchema)
        assert config.format == "png"
        assert config.dpi == 300


class TestTOMLLoader:
    """Tests for TOML configuration loading."""

    @pytest.fixture
    def sample_toml_content(self) -> str:
        """Sample TOML configuration content."""
        return """
[[files]]
path = "data.tsv"
has_header = true
comment_chars = ["#"]

[alignment]
enabled = true
column = "time"

[[derived_columns]]
name = "velocity"
expression = "distance / time"

[[filters]]
column = "time"
min = 0.0
max = 100.0

[[series]]
x = "time"
y = "velocity"
label = "Velocity"
color = "#0072B2"

[plot]
type = "line"
title = "Velocity over Time"
x_label = "Time (s)"
y_label = "Velocity (m/s)"
figure_width = 12.0
figure_height = 8.0

[export]
format = "pdf"
dpi = 600
"""

    def test_load_config_basic(self, tmp_path: Path, sample_toml_content: str):
        """Test loading a basic TOML configuration."""
        from plottini.config.loader import load_config

        # Create test file
        config_path = tmp_path / "config.toml"
        config_path.write_text(sample_toml_content)

        # Also create the data file so the path exists
        data_path = tmp_path / "data.tsv"
        data_path.write_text("time\tvelocity\n1.0\t2.0\n")

        config = load_config(config_path)

        assert len(config.files) == 1
        assert config.files[0].has_header is True
        assert config.alignment is not None
        assert config.alignment.enabled is True
        assert config.alignment.column == "time"
        assert len(config.derived_columns) == 1
        assert config.derived_columns[0].name == "velocity"
        assert len(config.filters) == 1
        assert config.filters[0].min == 0.0
        assert config.filters[0].max == 100.0
        assert len(config.series) == 1
        assert config.series[0].x == "time"
        assert config.series[0].y == "velocity"
        assert config.series[0].label == "Velocity"
        assert config.plot.type == "line"
        assert config.plot.title == "Velocity over Time"
        assert config.plot.figure_width == 12.0
        assert config.export.format == "pdf"
        assert config.export.dpi == 600

    def test_load_config_file_not_found(self, tmp_path: Path):
        """Test loading non-existent file raises FileNotFoundError."""
        from plottini.config.loader import load_config

        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.toml")

    def test_load_config_invalid_toml(self, tmp_path: Path):
        """Test loading invalid TOML raises ConfigError."""
        from plottini.config.loader import ConfigError, load_config

        config_path = tmp_path / "invalid.toml"
        config_path.write_text("this is not valid [ toml")

        with pytest.raises(ConfigError):
            load_config(config_path)

    def test_load_config_relative_paths(self, tmp_path: Path):
        """Test that relative paths are resolved relative to config file."""
        from plottini.config.loader import load_config

        # Create subdirectory with config
        subdir = tmp_path / "configs"
        subdir.mkdir()

        config_content = """
[[files]]
path = "../data/input.tsv"
"""
        config_path = subdir / "config.toml"
        config_path.write_text(config_content)

        config = load_config(config_path)

        # Path should be resolved relative to config file's directory
        assert config.files[0].path == subdir / ".." / "data" / "input.tsv"

    def test_load_config_defaults_applied(self, tmp_path: Path):
        """Test that default values are applied for missing fields."""
        from plottini.config.loader import load_config

        config_content = """
[[files]]
path = "data.tsv"

[[series]]
x = "x"
y = "y"
"""
        config_path = tmp_path / "minimal.toml"
        config_path.write_text(config_content)

        config = load_config(config_path)

        # Check defaults
        assert config.files[0].has_header is True
        assert config.files[0].delimiter == "\t"
        assert config.alignment is None
        assert config.series[0].line_style == "-"
        assert config.series[0].line_width == 1.5
        assert config.plot.type == "line"
        assert config.export.format == "png"


class TestTOMLSaver:
    """Tests for TOML configuration saving."""

    def test_save_config_basic(self, tmp_path: Path):
        """Test saving a basic configuration."""
        from plottini.config.loader import load_config, save_config

        config = GrapherConfig(
            files=[FileConfig(path=Path("data.tsv"))],
            series=[SeriesConfigSchema(x="time", y="value", label="Data")],
            plot=PlotConfigSchema(type="scatter", title="My Plot"),
            export=ExportConfigSchema(format="pdf"),
        )

        config_path = tmp_path / "output.toml"
        save_config(config, config_path)

        # Verify file was created
        assert config_path.exists()

        # Read back and verify
        loaded = load_config(config_path)
        assert loaded.files[0].path.name == "data.tsv"
        assert loaded.series[0].label == "Data"
        assert loaded.plot.type == "scatter"
        assert loaded.export.format == "pdf"

    def test_save_config_roundtrip(self, tmp_path: Path):
        """Test that saving and loading produces equivalent config."""
        from plottini.config.loader import load_config, save_config

        original = GrapherConfig(
            files=[
                FileConfig(path=Path("data1.tsv")),
                FileConfig(path=Path("data2.tsv"), has_header=False),
            ],
            alignment=AlignmentConfig(enabled=True, column="time"),
            derived_columns=[DerivedColumnConfig(name="vel", expression="d/t")],
            filters=[FilterConfig(column="time", min=0.0, max=100.0)],
            series=[
                SeriesConfigSchema(x="time", y="vel", label="Velocity", color="#FF0000"),
                SeriesConfigSchema(x="time", y="acc", use_secondary_y=True),
            ],
            plot=PlotConfigSchema(
                type="line",
                title="Test Plot",
                x_label="Time",
                y_label="Value",
                y2_label="Secondary",
                figure_width=15.0,
                show_grid=False,
            ),
            export=ExportConfigSchema(format="svg", dpi=150, transparent=True),
        )

        config_path = tmp_path / "roundtrip.toml"
        save_config(original, config_path)
        loaded = load_config(config_path)

        # Verify all fields match
        assert len(loaded.files) == 2
        assert loaded.files[1].has_header is False
        assert loaded.alignment is not None
        assert loaded.alignment.enabled is True
        assert len(loaded.derived_columns) == 1
        assert len(loaded.filters) == 1
        assert loaded.filters[0].min == 0.0
        assert len(loaded.series) == 2
        assert loaded.series[0].color == "#FF0000"
        assert loaded.series[1].use_secondary_y is True
        assert loaded.plot.title == "Test Plot"
        assert loaded.plot.y2_label == "Secondary"
        assert loaded.plot.figure_width == 15.0
        assert loaded.plot.show_grid is False
        assert loaded.export.format == "svg"
        assert loaded.export.transparent is True

    def test_save_config_creates_directory(self, tmp_path: Path):
        """Test that save_config creates parent directories."""
        from plottini.config.loader import save_config

        config = GrapherConfig()
        config_path = tmp_path / "nested" / "dir" / "config.toml"

        save_config(config, config_path)

        assert config_path.exists()

    def test_save_config_minimal(self, tmp_path: Path):
        """Test saving minimal config produces valid TOML."""
        from plottini.config.loader import save_config

        config = GrapherConfig()
        config_path = tmp_path / "minimal.toml"

        save_config(config, config_path)

        # Should produce valid but minimal TOML
        content = config_path.read_text()
        # Minimal config should be mostly empty
        assert "[[files]]" not in content or len(config.files) > 0


class TestConfigError:
    """Tests for ConfigError exception."""

    def test_config_error_message(self):
        """Test ConfigError formatting."""
        from plottini.config.loader import ConfigError

        error = ConfigError("Test error")
        assert str(error) == "Test error"

    def test_config_error_with_path(self):
        """Test ConfigError formatting with path."""
        from plottini.config.loader import ConfigError

        error = ConfigError("Test error", path=Path("/path/to/config.toml"))
        assert "Test error" in str(error)
        assert "/path/to/config.toml" in str(error)
