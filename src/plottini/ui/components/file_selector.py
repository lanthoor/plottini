"""File selector component for loading TSV files.

Provides UI for selecting files, configuring parser settings,
and displaying loaded file information.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nicegui import ui

from plottini.core.parser import ParserConfig, TSVParser
from plottini.ui.state import AppState, DataSource


class FileSelector:
    """Component for selecting and loading TSV files."""

    def __init__(self, state: AppState) -> None:
        """Initialize file selector.

        Args:
            state: Application state
        """
        self.state = state
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the file selector UI."""
        # File list section
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Data Files").classes("text-lg font-semibold")
                ui.upload(
                    label="Add Files",
                    on_upload=self._handle_upload,
                    multiple=True,
                    auto_upload=True,
                ).props('accept=".tsv,.txt,.dat,.csv"').classes("max-w-xs")

            # File list container (updated dynamically)
            self.file_list = ui.column().classes("w-full gap-1")
            self._update_file_list()

        # Parser settings section
        with ui.card().classes("w-full mt-4"):
            ui.label("Parser Settings").classes("text-lg font-semibold mb-2")
            with ui.row().classes("gap-4 flex-wrap"):
                self.has_header = ui.checkbox(
                    "Has Header Row",
                    value=self.state.parser_config.has_header,
                    on_change=self._on_parser_change,
                )
                self.comment_chars = (
                    ui.input(
                        "Comment chars",
                        value=",".join(self.state.parser_config.comment_chars),
                        on_change=self._on_parser_change,
                    )
                    .classes("w-24")
                    .tooltip("Characters that indicate comment lines (comma-separated)")
                )
                self.delimiter = ui.select(
                    {"\t": "Tab", ",": "Comma", " ": "Space", ";": "Semicolon"},
                    label="Delimiter",
                    value=self.state.parser_config.delimiter,
                    on_change=self._on_parser_change,
                ).classes("w-28")

        # Register for state changes
        self.state.add_change_callback(self._on_state_change)

    async def _handle_upload(self, e: Any) -> None:
        """Handle file upload event.

        Args:
            e: Upload event with file content
        """
        # Save uploaded file to temp location and parse
        import tempfile
        import uuid

        # Create temp file with original name
        temp_dir = Path(tempfile.gettempdir()) / "plottini_uploads"
        temp_dir.mkdir(exist_ok=True)

        # Sanitize filename: extract just the name part and add UUID to prevent collisions
        safe_name = Path(e.file.name).name  # Strip any path components
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        file_path = temp_dir / unique_name
        await e.file.save(file_path)

        self._load_file(file_path)

    def _load_file(self, file_path: Path) -> None:
        """Load a file and add to state.

        Args:
            file_path: Path to file to load
        """
        if file_path in self.state.loaded_files:
            ui.notify(f"File already loaded: {file_path.name}", type="warning")
            return

        parser = TSVParser(self.state.parser_config)
        try:
            dataframes = parser.parse_blocks(file_path)
            self.state.loaded_files.append(file_path)

            # Add each block as a separate data source
            for df in dataframes:
                ds = DataSource(file_path=file_path, block_index=df.block_index)
                self.state.data_sources.append(ds)
                self.state.parsed_data[ds] = df

            self.state.clear_error()
            self.state.notify_change()
            self._update_file_list()

            n_blocks = len(dataframes)
            if n_blocks > 1:
                ui.notify(f"Loaded: {file_path.name} ({n_blocks} blocks)", type="positive")
            else:
                ui.notify(f"Loaded: {file_path.name}", type="positive")
        except Exception as e:
            self.state.set_error(str(e))
            ui.notify(f"Error loading file: {e}", type="negative")

    def _remove_file(self, file_path: Path) -> None:
        """Remove a file from the list.

        Args:
            file_path: Path to file to remove
        """
        if file_path in self.state.loaded_files:
            self.state.loaded_files.remove(file_path)

            # Remove all data sources for this file
            sources_to_remove = [ds for ds in self.state.data_sources if ds.file_path == file_path]
            for ds in sources_to_remove:
                self.state.data_sources.remove(ds)
                self.state.parsed_data.pop(ds, None)

            # Clear series when files change (series indices would be invalid)
            self.state.series.clear()

            self.state.notify_change()
            self._update_file_list()

    def _update_file_list(self) -> None:
        """Update the file list display."""
        self.file_list.clear()
        with self.file_list:
            if not self.state.loaded_files:
                ui.label("No files loaded").classes("text-gray-500 italic")
            else:
                for file_path in self.state.loaded_files:
                    info = self.state.get_file_info(file_path)
                    with ui.row().classes(
                        "w-full justify-between items-center p-2 bg-gray-50 "
                        "dark:bg-gray-700 rounded"
                    ):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("description").classes("text-blue-500")
                            ui.label(file_path.name).classes("font-medium")
                            ui.label(info).classes("text-sm text-gray-500")
                        ui.button(
                            icon="close",
                            on_click=lambda _e=None, p=file_path: self._remove_file(p),
                        ).props("flat dense round size=sm")

    def _on_parser_change(self) -> None:
        """Handle parser settings change."""
        comment_chars = [c.strip() for c in self.comment_chars.value.split(",") if c.strip()]
        if not comment_chars:
            comment_chars = ["#"]

        self.state.parser_config = ParserConfig(
            has_header=self.has_header.value,
            comment_chars=comment_chars,
            delimiter=str(self.delimiter.value) if self.delimiter.value else "\t",
        )
        # Re-parse files with new settings
        self._reparse_files()

    def _reparse_files(self) -> None:
        """Re-parse all files with current parser settings."""
        parser = TSVParser(self.state.parser_config)

        # Clear existing data sources, parsed data, and series
        # (series indices would be invalid after re-parsing)
        self.state.data_sources.clear()
        self.state.parsed_data.clear()
        self.state.series.clear()

        for file_path in list(self.state.loaded_files):
            try:
                dataframes = parser.parse_blocks(file_path)
                for df in dataframes:
                    ds = DataSource(file_path=file_path, block_index=df.block_index)
                    self.state.data_sources.append(ds)
                    self.state.parsed_data[ds] = df
                self.state.clear_error()
            except Exception as e:
                self.state.set_error(str(e))

        self.state.notify_change()
        self._update_file_list()

    def _on_state_change(self) -> None:
        """Handle state changes from other components."""
        # Update UI elements if needed
        pass


def create_file_selector(state: AppState) -> FileSelector:
    """Factory function to create FileSelector component.

    Args:
        state: Application state

    Returns:
        FileSelector instance
    """
    return FileSelector(state)


__all__ = ["FileSelector", "create_file_selector"]
