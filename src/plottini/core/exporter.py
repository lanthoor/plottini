"""Exporter module for saving figures to various formats.

This module provides functionality to export matplotlib figures
to PNG, SVG, PDF, and EPS formats with configurable settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from plottini.utils.errors import ExportError

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class ExportFormat(Enum):
    """Supported export formats.

    Attributes:
        PNG: Portable Network Graphics (raster)
        SVG: Scalable Vector Graphics (vector)
        PDF: Portable Document Format (vector)
        EPS: Encapsulated PostScript (vector)
    """

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    EPS = "eps"

    @classmethod
    def from_string(cls, value: str) -> ExportFormat:
        """Create ExportFormat from string value.

        Args:
            value: Format string (case-insensitive).

        Returns:
            Corresponding ExportFormat enum value.

        Raises:
            ValueError: If value is not a valid format.
        """
        value_lower = value.lower()
        for fmt in cls:
            if fmt.value == value_lower:
                return fmt
        valid = ", ".join(f.value for f in cls)
        raise ValueError(f"Invalid export format: '{value}'. Valid formats: {valid}")


@dataclass
class ExportConfig:
    """Configuration for figure export.

    Attributes:
        format: Export format (PNG, SVG, PDF, EPS).
        dpi: Resolution for raster formats (default: 300).
        transparent: Whether to use transparent background.
        bbox_inches: Bounding box setting (default: "tight").
        pad_inches: Padding around figure (default: 0.1).
    """

    format: ExportFormat
    dpi: int = 300
    transparent: bool = False
    bbox_inches: str = "tight"
    pad_inches: float = 0.1


class Exporter:
    """Export matplotlib figures to various formats.

    Example:
        >>> from matplotlib import pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> ax.plot([1, 2, 3], [1, 4, 9])
        >>> exporter = Exporter()
        >>> config = ExportConfig(format=ExportFormat.PNG, dpi=300)
        >>> exporter.export(fig, Path("output.png"), config)
    """

    def export(self, figure: Figure, path: Path | str, config: ExportConfig) -> Path:
        """Export a figure to a file.

        Args:
            figure: Matplotlib figure to export.
            path: Output file path.
            config: Export configuration.

        Returns:
            Path to the exported file.

        Raises:
            ExportError: If export fails.
        """
        output_path = Path(path)

        # Ensure correct file extension
        output_path = self._ensure_extension(output_path, config.format)

        # Create parent directory if needed
        self._ensure_directory(output_path)

        try:
            # Build savefig kwargs
            kwargs: dict[str, Any] = {
                "format": config.format.value,
                "bbox_inches": config.bbox_inches,
                "pad_inches": config.pad_inches,
                "transparent": config.transparent,
            }

            # DPI only matters for raster formats
            if config.format == ExportFormat.PNG:
                kwargs["dpi"] = config.dpi

            figure.savefig(output_path, **kwargs)

        except OSError as e:
            raise ExportError(
                message=f"Failed to write file: {e}",
                output_path=output_path,
                format=config.format.value,
            ) from e
        except Exception as e:
            raise ExportError(
                message=f"Export failed: {e}",
                output_path=output_path,
                format=config.format.value,
            ) from e

        return output_path

    def export_multiple(
        self,
        figure: Figure,
        base_path: Path | str,
        formats: list[ExportFormat],
    ) -> list[Path]:
        """Export a figure to multiple formats.

        Args:
            figure: Matplotlib figure to export.
            base_path: Base output path (extension will be replaced).
            formats: List of export formats.

        Returns:
            List of paths to exported files.

        Raises:
            ExportError: If any export fails.
        """
        base = Path(base_path)
        stem = base.stem
        parent = base.parent

        exported_paths: list[Path] = []

        for fmt in formats:
            output_path = parent / f"{stem}.{fmt.value}"
            config = ExportConfig(format=fmt)
            result_path = self.export(figure, output_path, config)
            exported_paths.append(result_path)

        return exported_paths

    def _ensure_extension(self, path: Path, fmt: ExportFormat) -> Path:
        """Ensure file has correct extension for format."""
        expected_ext = f".{fmt.value}"
        if path.suffix.lower() != expected_ext:
            return path.with_suffix(expected_ext)
        return path

    def _ensure_directory(self, path: Path) -> None:
        """Ensure parent directory exists."""
        parent = path.parent
        if parent and not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ExportError(
                    message=f"Cannot create directory '{parent}': {e}",
                    output_path=path,
                ) from e


__all__ = ["ExportFormat", "ExportConfig", "Exporter"]
