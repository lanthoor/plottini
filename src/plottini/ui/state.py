"""State management for Plottini UI.

This module provides centralized state management using dataclasses
with change callbacks for reactive UI updates.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from plottini.config.schema import (
    AlignmentConfig,
    DerivedColumnConfig,
    FilterConfig,
)
from plottini.core.parser import ParserConfig
from plottini.core.plotter import ChartType, PlotConfig, SeriesConfig

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plottini.core.dataframe import DataFrame


@dataclass
class DataSource:
    """Identifier for a data source (file + optional block index).

    Attributes:
        file_path: Path to the source file
        block_index: Index of data block within file (None for single-block files)
    """

    file_path: Path
    block_index: int | None = None

    @property
    def display_name(self) -> str:
        """Get display name for this data source."""
        if self.block_index is not None:
            return f"{self.file_path.name} (block {self.block_index + 1})"
        return self.file_path.name

    def __hash__(self) -> int:
        return hash((self.file_path, self.block_index))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataSource):
            return False
        return self.file_path == other.file_path and self.block_index == other.block_index


@dataclass
class AppState:
    """Central application state.

    Attributes:
        loaded_files: List of original file paths (for tracking unique files)
        data_sources: List of DataSource identifiers (file + block)
        parser_config: Configuration for TSV parsing
        parsed_data: Dictionary mapping DataSource to parsed DataFrames
        derived_columns: List of derived column configurations
        filters: List of filter configurations
        alignment: Alignment configuration for multi-file
        series: List of series configurations for plotting
        plot_config: Plot appearance configuration
        current_figure: Currently rendered matplotlib Figure
        error_message: Current error message (None if no error)
        is_dirty: Whether state has changed since last render
    """

    # Data state
    loaded_files: list[Path] = field(default_factory=list)
    data_sources: list[DataSource] = field(default_factory=list)
    parser_config: ParserConfig = field(default_factory=ParserConfig)
    parsed_data: dict[DataSource, DataFrame] = field(default_factory=dict)

    # Transformation state
    derived_columns: list[DerivedColumnConfig] = field(default_factory=list)
    filters: list[FilterConfig] = field(default_factory=list)
    alignment: AlignmentConfig | None = None

    # Plot state
    series: list[SeriesConfig] = field(default_factory=list)
    plot_config: PlotConfig = field(default_factory=PlotConfig)

    # UI state
    current_figure: Figure | None = None
    error_message: str | None = None
    is_dirty: bool = False

    # Callbacks (not serialized)
    _change_callbacks: list[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_change_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when state changes.

        Args:
            callback: Function to call on state change
        """
        self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[], None]) -> None:
        """Remove a registered callback.

        Args:
            callback: Function to remove
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def notify_change(self) -> None:
        """Notify all registered callbacks of state change."""
        self.is_dirty = True
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception:
                # Don't let one callback failure break others
                pass

    def get_all_column_names(self) -> list[str]:
        """Get all available column names from all loaded files.

        Returns:
            Sorted list of unique column names
        """
        columns: set[str] = set()
        for df in self.parsed_data.values():
            columns.update(df.get_column_names())
        return sorted(columns)

    def get_dataframes_list(self) -> list[DataFrame]:
        """Get DataFrames as a list ordered by data_sources.

        Returns:
            List of DataFrames in the order they were loaded
        """
        return [self.parsed_data[ds] for ds in self.data_sources if ds in self.parsed_data]

    def clear_data(self) -> None:
        """Clear all loaded data and reset state."""
        self.loaded_files.clear()
        self.data_sources.clear()
        self.parsed_data.clear()
        self.derived_columns.clear()
        self.filters.clear()
        self.alignment = None
        self.series.clear()
        self.current_figure = None
        self.error_message = None
        self.notify_change()

    def set_error(self, message: str) -> None:
        """Set error message and notify.

        Args:
            message: Error message to display
        """
        self.error_message = message
        self.notify_change()

    def clear_error(self) -> None:
        """Clear error message."""
        self.error_message = None
        # Don't notify here to avoid unnecessary updates

    def has_data(self) -> bool:
        """Check if any data is loaded.

        Returns:
            True if at least one file is loaded with data
        """
        return bool(self.parsed_data)

    def has_series(self) -> bool:
        """Check if any series are configured.

        Returns:
            True if at least one series is configured
        """
        return bool(self.series)

    def can_render(self) -> bool:
        """Check if the current state can produce a plot.

        Returns:
            True if data and series are configured
        """
        return self.has_data() and self.has_series()

    def get_file_info(self, file_path: Path) -> str:
        """Get display info for a loaded file.

        Args:
            file_path: Path to the file

        Returns:
            String with block count, column count and row count
        """
        # Find all data sources for this file
        sources = [ds for ds in self.data_sources if ds.file_path == file_path]
        if not sources:
            return "(not loaded)"

        total_rows = 0
        columns: set[str] = set()
        for ds in sources:
            if ds in self.parsed_data:
                df = self.parsed_data[ds]
                total_rows += df.row_count
                columns.update(df.get_column_names())

        n_blocks = len(sources)
        n_cols = len(columns)
        if n_blocks > 1:
            return f"({n_blocks} blocks, {n_cols} columns, {total_rows} rows)"
        return f"({n_cols} columns, {total_rows} rows)"

    def get_data_source_info(self, data_source: DataSource) -> str:
        """Get display info for a data source.

        Args:
            data_source: DataSource to get info for

        Returns:
            String with column count and row count
        """
        if data_source not in self.parsed_data:
            return "(not loaded)"
        df = self.parsed_data[data_source]
        n_cols = len(df.get_column_names())
        return f"({n_cols} columns, {df.row_count} rows)"


def create_default_state() -> AppState:
    """Create a new AppState with default values.

    Returns:
        Fresh AppState instance with defaults
    """
    return AppState(
        plot_config=PlotConfig(
            chart_type=ChartType.LINE,
            show_grid=True,
            show_legend=True,
        )
    )


__all__ = ["AppState", "DataSource", "create_default_state"]
