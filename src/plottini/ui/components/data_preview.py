"""Data preview table component.

Displays parsed DataFrame data in a scrollable table format
with support for selecting which file to preview.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nicegui import ui

from plottini.ui.state import AppState


class DataPreview:
    """Component for previewing loaded data in table format."""

    MAX_PREVIEW_ROWS = 100

    def __init__(self, state: AppState) -> None:
        """Initialize data preview.

        Args:
            state: Application state
        """
        self.state = state
        self.selected_file: Path | None = None
        self._create_ui()
        state.add_change_callback(self._on_state_change)

    def _create_ui(self) -> None:
        """Create the data preview UI."""
        with ui.card().classes("w-full h-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Data Preview").classes("text-lg font-semibold")
                self.file_select = ui.select(
                    [],
                    label="File",
                    value=None,
                    on_change=self._on_file_select,
                ).classes("w-48")

            # Table container
            self.table_container = (
                ui.column().classes("w-full overflow-auto").style("max-height: 400px")
            )

            # Row count info
            self.row_info = ui.label("No data loaded").classes("text-sm text-gray-500 mt-2")

    def _on_file_select(self) -> None:
        """Handle file selection change."""
        if self.file_select.value:
            self.selected_file = Path(self.file_select.value)
            self._update_table()

    def _on_state_change(self) -> None:
        """Handle state changes."""
        # Update file selector options
        options = {str(f): f.name for f in self.state.loaded_files}
        self.file_select.options = options

        # Auto-select first file if none selected
        if not self.selected_file and self.state.loaded_files:
            self.selected_file = self.state.loaded_files[0]
            self.file_select.value = str(self.selected_file)

        self._update_table()

    def _update_table(self) -> None:
        """Update the preview table."""
        self.table_container.clear()

        if not self.selected_file or self.selected_file not in self.state.parsed_data:
            with self.table_container:
                ui.label("No data loaded").classes("text-gray-500 italic p-4")
            self.row_info.text = "No data loaded"
            return

        df = self.state.parsed_data[self.selected_file]
        columns = df.get_column_names()

        if not columns:
            with self.table_container:
                ui.label("File has no columns").classes("text-gray-500 italic p-4")
            self.row_info.text = "No columns"
            return

        # Build table data
        rows: list[dict[str, Any]] = []
        num_rows = min(df.row_count, self.MAX_PREVIEW_ROWS)

        for i in range(num_rows):
            row: dict[str, Any] = {"_row": i + 1}
            for col in columns:
                value = df[col][i]
                # Format numbers nicely
                if isinstance(value, float):
                    if abs(value) < 0.001 or abs(value) > 10000:
                        row[col] = f"{value:.4e}"
                    else:
                        row[col] = f"{value:.6g}"
                else:
                    row[col] = str(value)
            rows.append(row)

        # Create table columns
        table_columns: list[dict[str, Any]] = [
            {"name": "_row", "label": "#", "field": "_row", "sortable": True}
        ]
        table_columns.extend(
            [{"name": col, "label": col, "field": col, "sortable": True} for col in columns]
        )

        # Create table using NiceGUI's table component
        with self.table_container:
            ui.table(
                columns=table_columns,
                rows=rows,
                row_key="_row",
            ).classes("w-full").props("dense flat")

        # Update row count info
        shown = min(df.row_count, self.MAX_PREVIEW_ROWS)
        if shown < df.row_count:
            self.row_info.text = f"Showing {shown} of {df.row_count} rows"
        else:
            self.row_info.text = f"Showing all {df.row_count} rows"


def create_data_preview(state: AppState) -> DataPreview:
    """Factory function to create DataPreview component.

    Args:
        state: Application state

    Returns:
        DataPreview instance
    """
    return DataPreview(state)


__all__ = ["DataPreview", "create_data_preview"]
