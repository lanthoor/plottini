"""TOML configuration loader and saver.

This module provides functions to load and save Plottini configurations
in TOML format for reproducible workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

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


class ConfigError(Exception):
    """Error loading or saving configuration."""

    def __init__(self, message: str, path: Path | None = None) -> None:
        self.message = message
        self.path = path
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.path:
            return f"{self.message} (file: {self.path})"
        return self.message


def load_config(path: Path | str) -> GrapherConfig:
    """Load configuration from TOML file.

    Args:
        path: Path to TOML file

    Returns:
        GrapherConfig object

    Raises:
        FileNotFoundError: If file doesn't exist
        ConfigError: If TOML is invalid or missing required fields
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML format: {e}", path) from e

    return _dict_to_config(data, base_path=path.parent)


def save_config(config: GrapherConfig, path: Path | str) -> None:
    """Save configuration to TOML file.

    Args:
        config: Configuration to save
        path: Output path

    Raises:
        ConfigError: If unable to write file
    """
    path = Path(path)
    data = _config_to_dict(config)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
    except OSError as e:
        raise ConfigError(f"Unable to write configuration: {e}", path) from e


def _dict_to_config(data: dict[str, Any], base_path: Path) -> GrapherConfig:
    """Convert dictionary to GrapherConfig.

    Args:
        data: Dictionary from TOML file
        base_path: Base path for resolving relative file paths

    Returns:
        GrapherConfig instance
    """
    # Parse files
    files: list[FileConfig] = []
    for file_data in data.get("files", []):
        file_path = Path(file_data["path"])
        # Resolve relative paths against the config file's directory
        if not file_path.is_absolute():
            file_path = base_path / file_path
        files.append(
            FileConfig(
                path=file_path,
                has_header=file_data.get("has_header", True),
                comment_chars=file_data.get("comment_chars", ["#"]),
                delimiter=file_data.get("delimiter", "\t"),
                encoding=file_data.get("encoding", "utf-8"),
            )
        )

    # Parse alignment
    alignment: AlignmentConfig | None = None
    if "alignment" in data:
        alignment_data = data["alignment"]
        alignment = AlignmentConfig(
            enabled=alignment_data.get("enabled", False),
            column=alignment_data.get("column", ""),
        )

    # Parse derived columns
    derived_columns: list[DerivedColumnConfig] = []
    for dc_data in data.get("derived_columns", []):
        derived_columns.append(
            DerivedColumnConfig(
                name=dc_data["name"],
                expression=dc_data["expression"],
            )
        )

    # Parse filters
    filters: list[FilterConfig] = []
    for filter_data in data.get("filters", []):
        filters.append(
            FilterConfig(
                column=filter_data["column"],
                min=filter_data.get("min"),
                max=filter_data.get("max"),
            )
        )

    # Parse series
    series: list[SeriesConfigSchema] = []
    for series_data in data.get("series", []):
        series.append(
            SeriesConfigSchema(
                x=series_data["x"],
                y=series_data["y"],
                label=series_data.get("label"),
                color=series_data.get("color"),
                line_style=series_data.get("line_style", "-"),
                marker=series_data.get("marker"),
                line_width=series_data.get("line_width", 1.5),
                use_secondary_y=series_data.get("use_secondary_y", False),
                source_file_index=series_data.get("source_file_index", 0),
            )
        )

    # Parse plot config
    plot_data = data.get("plot", {})
    plot = PlotConfigSchema(
        type=plot_data.get("type", "line"),
        title=plot_data.get("title", ""),
        x_label=plot_data.get("x_label", ""),
        y_label=plot_data.get("y_label", ""),
        y2_label=plot_data.get("y2_label", ""),
        figure_width=plot_data.get("figure_width", 10.0),
        figure_height=plot_data.get("figure_height", 6.0),
        show_grid=plot_data.get("show_grid", True),
        show_legend=plot_data.get("show_legend", True),
        legend_loc=plot_data.get("legend_loc", "best"),
    )

    # Parse export config
    export_data = data.get("export", {})
    export = ExportConfigSchema(
        format=export_data.get("format", "png"),
        dpi=export_data.get("dpi", 300),
        transparent=export_data.get("transparent", False),
    )

    return GrapherConfig(
        files=files,
        alignment=alignment,
        derived_columns=derived_columns,
        filters=filters,
        series=series,
        plot=plot,
        export=export,
    )


def _config_to_dict(config: GrapherConfig) -> dict[str, Any]:
    """Convert GrapherConfig to dictionary for TOML serialization.

    Args:
        config: Configuration to convert

    Returns:
        Dictionary suitable for TOML serialization
    """
    result: dict[str, Any] = {}

    # Serialize files
    if config.files:
        result["files"] = [
            {
                "path": str(f.path),
                "has_header": f.has_header,
                "comment_chars": f.comment_chars,
                "delimiter": f.delimiter,
                "encoding": f.encoding,
            }
            for f in config.files
        ]

    # Serialize alignment
    if config.alignment and config.alignment.enabled:
        result["alignment"] = {
            "enabled": config.alignment.enabled,
            "column": config.alignment.column,
        }

    # Serialize derived columns
    if config.derived_columns:
        result["derived_columns"] = [
            {"name": dc.name, "expression": dc.expression} for dc in config.derived_columns
        ]

    # Serialize filters
    if config.filters:
        filters_list = []
        for f in config.filters:
            filter_dict: dict[str, Any] = {"column": f.column}
            if f.min is not None:
                filter_dict["min"] = f.min
            if f.max is not None:
                filter_dict["max"] = f.max
            filters_list.append(filter_dict)
        result["filters"] = filters_list

    # Serialize series
    if config.series:
        series_list = []
        for s in config.series:
            series_dict: dict[str, Any] = {"x": s.x, "y": s.y}
            if s.label:
                series_dict["label"] = s.label
            if s.color:
                series_dict["color"] = s.color
            if s.line_style != "-":
                series_dict["line_style"] = s.line_style
            if s.marker:
                series_dict["marker"] = s.marker
            if s.line_width != 1.5:
                series_dict["line_width"] = s.line_width
            if s.use_secondary_y:
                series_dict["use_secondary_y"] = s.use_secondary_y
            if s.source_file_index != 0:
                series_dict["source_file_index"] = s.source_file_index
            series_list.append(series_dict)
        result["series"] = series_list

    # Serialize plot config (only non-default values)
    plot_dict: dict[str, Any] = {}
    if config.plot.type != "line":
        plot_dict["type"] = config.plot.type
    if config.plot.title:
        plot_dict["title"] = config.plot.title
    if config.plot.x_label:
        plot_dict["x_label"] = config.plot.x_label
    if config.plot.y_label:
        plot_dict["y_label"] = config.plot.y_label
    if config.plot.y2_label:
        plot_dict["y2_label"] = config.plot.y2_label
    if config.plot.figure_width != 10.0:
        plot_dict["figure_width"] = config.plot.figure_width
    if config.plot.figure_height != 6.0:
        plot_dict["figure_height"] = config.plot.figure_height
    if not config.plot.show_grid:
        plot_dict["show_grid"] = config.plot.show_grid
    if not config.plot.show_legend:
        plot_dict["show_legend"] = config.plot.show_legend
    if config.plot.legend_loc != "best":
        plot_dict["legend_loc"] = config.plot.legend_loc
    if plot_dict:
        result["plot"] = plot_dict

    # Serialize export config (only non-default values)
    export_dict: dict[str, Any] = {}
    if config.export.format != "png":
        export_dict["format"] = config.export.format
    if config.export.dpi != 300:
        export_dict["dpi"] = config.export.dpi
    if config.export.transparent:
        export_dict["transparent"] = config.export.transparent
    if export_dict:
        result["export"] = export_dict

    return result


__all__ = ["ConfigError", "load_config", "save_config"]
