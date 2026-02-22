"""State management for Plottini UI (Streamlit version).

This module provides centralized state management using Streamlit's
session_state for reactive UI updates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
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
class UploadedFile:
    """Represents an uploaded file in Streamlit.

    Attributes:
        name: Original filename from the upload
        content: File content as bytes
    """

    name: str
    content: bytes

    def get_file_object(self) -> BytesIO:
        """Get a file-like object for parsing.

        Returns:
            BytesIO object containing the file content
        """
        return BytesIO(self.content)


@dataclass
class DataSource:
    """Identifier for a data source (file name + optional block index).

    Attributes:
        file_name: Name of the source file
        block_index: Index of data block within file (None for single-block files)
    """

    file_name: str
    block_index: int | None = None

    @property
    def display_name(self) -> str:
        """Get display name for this data source."""
        if self.block_index is not None:
            return f"{self.file_name} (block {self.block_index + 1})"
        return self.file_name

    def __hash__(self) -> int:
        return hash((self.file_name, self.block_index))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataSource):
            return False
        return self.file_name == other.file_name and self.block_index == other.block_index


@dataclass
class AppState:
    """Central application state.

    Attributes:
        uploaded_files: Dictionary of uploaded files by name
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
    """

    # Data state
    uploaded_files: dict[str, UploadedFile] = field(default_factory=dict)
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
        """Clear all loaded data and reset state to defaults."""
        self.uploaded_files.clear()
        self.data_sources.clear()
        self.parsed_data.clear()
        self.derived_columns.clear()
        self.filters.clear()
        self.alignment = None
        self.series.clear()
        self.current_figure = None
        self.error_message = None

        # Reset parser config to defaults
        self.parser_config = ParserConfig()

        # Reset plot config to defaults
        self.plot_config = PlotConfig(
            chart_type=ChartType.LINE,
            show_grid=True,
            show_legend=True,
        )

        try:
            import streamlit as st

            # Increment file uploader key to reset the widget
            if "file_uploader_key" not in st.session_state:
                st.session_state.file_uploader_key = 0
            st.session_state.file_uploader_key += 1

            # Explicitly set all settings widget keys to default values
            st.session_state["settings_chart_type"] = "Line"
            st.session_state["settings_title"] = ""
            st.session_state["settings_x_label"] = ""
            st.session_state["settings_y_label"] = ""
            st.session_state["settings_y2_label"] = ""
            st.session_state["settings_width"] = 10.0
            st.session_state["settings_height"] = 6.0
            st.session_state["settings_grid"] = True
            st.session_state["settings_legend"] = True
            st.session_state["settings_legend_best"] = True
            st.session_state["settings_legend_position"] = "upper right"
            st.session_state["settings_bar_width"] = 0.8
            st.session_state["settings_histogram_bins"] = 20
            st.session_state["settings_histogram_density"] = False
            st.session_state["settings_scatter_size"] = 50
            st.session_state["settings_area_alpha"] = 0.5
            st.session_state["settings_pie_explode"] = 0.0
            st.session_state["settings_pie_labels"] = True
            st.session_state["settings_box_outliers"] = True
            st.session_state["settings_violin_median"] = True
            st.session_state["settings_step_where"] = "mid"

        except Exception:
            # st.session_state may not be available outside Streamlit runtime (e.g., tests)
            pass

    def set_error(self, message: str) -> None:
        """Set error message.

        Args:
            message: Error message to display
        """
        self.error_message = message

    def clear_error(self) -> None:
        """Clear error message."""
        self.error_message = None

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

    def get_file_info(self, file_name: str) -> str:
        """Get display info for a loaded file.

        Args:
            file_name: Name of the file

        Returns:
            String with block count, column count and row count
        """
        # Find all data sources for this file
        sources = [ds for ds in self.data_sources if ds.file_name == file_name]
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

    def get_file_names(self) -> list[str]:
        """Get list of uploaded file names.

        Returns:
            List of file names in upload order
        """
        return list(self.uploaded_files.keys())

    def remove_file(self, file_name: str) -> list[int]:
        """Remove a file and its associated data.

        Args:
            file_name: Name of the file to remove

        Returns:
            List of series indices that were removed (for UI notification)
        """
        # Find series that depend on this file
        removed_series_indices: list[int] = []
        data_sources_to_remove = [ds for ds in self.data_sources if ds.file_name == file_name]

        # Identify series to remove (those using data sources from this file)
        for i, series in enumerate(self.series):
            source_ds = (
                self.data_sources[series.source_file_index]
                if series.source_file_index < len(self.data_sources)
                else None
            )
            if source_ds and source_ds.file_name == file_name:
                removed_series_indices.append(i)

        # Remove series (in reverse order to maintain indices)
        for i in reversed(removed_series_indices):
            self.series.pop(i)

        # Update series source_file_index for remaining series
        # First, identify which data_sources will be removed
        removed_ds_indices = [self.data_sources.index(ds) for ds in data_sources_to_remove]

        # Update source_file_index for remaining series
        for series in self.series:
            # Count how many removed indices are before this series' source
            offset = sum(1 for idx in removed_ds_indices if idx < series.source_file_index)
            series.source_file_index -= offset

        # Remove data sources and parsed data
        for ds in data_sources_to_remove:
            if ds in self.parsed_data:
                del self.parsed_data[ds]
            self.data_sources.remove(ds)

        # Remove uploaded file
        if file_name in self.uploaded_files:
            del self.uploaded_files[file_name]

        return removed_series_indices


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


def get_state() -> AppState:
    """Get or create the app state from Streamlit session state.

    This function should be called at the start of each Streamlit rerun
    to get the persistent application state.

    Returns:
        The AppState instance from session state
    """
    import streamlit as st

    if "app_state" not in st.session_state:
        st.session_state.app_state = create_default_state()

    state: AppState = st.session_state.app_state
    return state


__all__ = ["AppState", "DataSource", "UploadedFile", "create_default_state", "get_state"]
