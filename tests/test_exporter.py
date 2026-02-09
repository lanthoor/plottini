"""Tests for Exporter module."""

from collections.abc import Generator
from pathlib import Path

import pytest
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from plottini.core.exporter import ExportConfig, Exporter, ExportFormat
from plottini.utils.errors import ExportError


@pytest.fixture
def sample_figure() -> Figure:
    """Create a sample matplotlib figure for testing."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [1, 4, 9, 16])
    ax.set_title("Test Plot")
    return fig


@pytest.fixture
def exporter() -> Exporter:
    """Create an Exporter instance."""
    return Exporter()


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_format_values(self) -> None:
        """Test that format values are correct."""
        assert ExportFormat.PNG.value == "png"
        assert ExportFormat.SVG.value == "svg"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.EPS.value == "eps"

    def test_from_string_valid(self) -> None:
        """Test creating format from valid string."""
        assert ExportFormat.from_string("png") == ExportFormat.PNG
        assert ExportFormat.from_string("PNG") == ExportFormat.PNG
        assert ExportFormat.from_string("svg") == ExportFormat.SVG
        assert ExportFormat.from_string("pdf") == ExportFormat.PDF
        assert ExportFormat.from_string("eps") == ExportFormat.EPS

    def test_from_string_invalid(self) -> None:
        """Test that invalid format string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExportFormat.from_string("gif")

        error_msg = str(exc_info.value)
        assert "gif" in error_msg
        assert "Valid formats" in error_msg


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ExportConfig(format=ExportFormat.PNG)
        assert config.format == ExportFormat.PNG
        assert config.dpi == 300
        assert config.transparent is False
        assert config.bbox_inches == "tight"
        assert config.pad_inches == 0.1

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = ExportConfig(
            format=ExportFormat.SVG,
            dpi=150,
            transparent=True,
            bbox_inches="standard",
            pad_inches=0.2,
        )
        assert config.format == ExportFormat.SVG
        assert config.dpi == 150
        assert config.transparent is True
        assert config.bbox_inches == "standard"
        assert config.pad_inches == 0.2


class TestExporter:
    """Tests for Exporter class."""

    def test_export_png(self, sample_figure: Figure, exporter: Exporter, tmp_path: Path) -> None:
        """Test exporting to PNG format."""
        output = tmp_path / "test.png"
        config = ExportConfig(format=ExportFormat.PNG, dpi=300)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()
        assert result.suffix == ".png"
        assert result.stat().st_size > 0

    def test_export_svg(self, sample_figure: Figure, exporter: Exporter, tmp_path: Path) -> None:
        """Test exporting to SVG format."""
        output = tmp_path / "test.svg"
        config = ExportConfig(format=ExportFormat.SVG)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()
        assert result.suffix == ".svg"
        # SVG should contain XML/SVG content
        content = result.read_text()
        assert "<svg" in content

    def test_export_pdf(self, sample_figure: Figure, exporter: Exporter, tmp_path: Path) -> None:
        """Test exporting to PDF format."""
        output = tmp_path / "test.pdf"
        config = ExportConfig(format=ExportFormat.PDF)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()
        assert result.suffix == ".pdf"
        # PDF should start with %PDF header
        content = result.read_bytes()
        assert content.startswith(b"%PDF")

    def test_export_eps(self, sample_figure: Figure, exporter: Exporter, tmp_path: Path) -> None:
        """Test exporting to EPS format."""
        output = tmp_path / "test.eps"
        config = ExportConfig(format=ExportFormat.EPS)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()
        assert result.suffix == ".eps"

    def test_export_creates_directory(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test that export creates parent directory if needed."""
        output = tmp_path / "subdir" / "nested" / "test.png"
        config = ExportConfig(format=ExportFormat.PNG)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()
        assert result.parent.exists()

    def test_export_fixes_extension(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test that export fixes incorrect extension."""
        output = tmp_path / "test.jpg"  # Wrong extension
        config = ExportConfig(format=ExportFormat.PNG)

        result = exporter.export(sample_figure, output, config)

        assert result.suffix == ".png"
        assert result.exists()

    def test_export_custom_dpi(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test exporting with custom DPI."""
        output_low = tmp_path / "low_dpi.png"
        output_high = tmp_path / "high_dpi.png"

        config_low = ExportConfig(format=ExportFormat.PNG, dpi=72)
        config_high = ExportConfig(format=ExportFormat.PNG, dpi=300)

        result_low = exporter.export(sample_figure, output_low, config_low)
        result_high = exporter.export(sample_figure, output_high, config_high)

        # Higher DPI should produce larger file
        assert result_high.stat().st_size > result_low.stat().st_size

    def test_export_transparent(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test exporting with transparent background."""
        output = tmp_path / "transparent.png"
        config = ExportConfig(format=ExportFormat.PNG, transparent=True)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()

    def test_export_string_path(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test that string paths work."""
        output = str(tmp_path / "test.png")
        config = ExportConfig(format=ExportFormat.PNG)

        result = exporter.export(sample_figure, output, config)

        assert result.exists()

    def test_export_multiple_formats(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test exporting to multiple formats at once."""
        base_path = tmp_path / "output.png"
        formats = [ExportFormat.PNG, ExportFormat.SVG, ExportFormat.PDF]

        results = exporter.export_multiple(sample_figure, base_path, formats)

        assert len(results) == 3
        assert all(p.exists() for p in results)
        assert {p.suffix for p in results} == {".png", ".svg", ".pdf"}

    def test_export_returns_path(
        self, sample_figure: Figure, exporter: Exporter, tmp_path: Path
    ) -> None:
        """Test that export returns the output path."""
        output = tmp_path / "test.png"
        config = ExportConfig(format=ExportFormat.PNG)

        result = exporter.export(sample_figure, output, config)

        assert isinstance(result, Path)
        assert result == output


class TestExporterErrors:
    """Tests for exporter error handling."""

    def test_export_invalid_directory_raises_error(
        self, sample_figure: Figure, exporter: Exporter
    ) -> None:
        """Test that invalid directory raises ExportError."""
        # Try to write to a path that can't be created
        output = Path("/nonexistent_root_dir_12345/test.png")
        config = ExportConfig(format=ExportFormat.PNG)

        with pytest.raises(ExportError) as exc_info:
            exporter.export(sample_figure, output, config)

        error = exc_info.value
        assert "Cannot create directory" in error.message


# Cleanup matplotlib figures after tests
@pytest.fixture(autouse=True)
def cleanup_figures() -> Generator[None, None, None]:
    """Close all matplotlib figures after each test."""
    yield
    plt.close("all")
