"""Data preview table component.

Displays parsed DataFrame data in a scrollable table format
with support for selecting which data source to preview.
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from plottini.ui.state import AppState, DataSource


class DataPreview:
    """Component for previewing loaded data in table format."""

    MAX_PREVIEW_ROWS = 100

    def __init__(self, state: AppState) -> None:
        """Initialize data preview.

        Args:
            state: Application state
        """
        self.state = state
        self.selected_source: DataSource | None = None
        self._create_ui()
        state.add_change_callback(self._on_state_change)

    def _create_ui(self) -> None:
        """Create the data preview UI."""
        with ui.card().classes("w-full h-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Data Preview").classes("text-lg font-semibold")
                self.source_select = ui.select(
                    [],
                    label="Data Source",
                    value=None,
                    on_change=self._on_source_select,
                ).classes("w-64")

            # Table container
            self.table_container = (
                ui.column().classes("w-full overflow-auto").style("max-height: 400px")
            )

            # Row count info
            self.row_info = ui.label("No data loaded").classes("text-sm text-gray-500 mt-2")

    def _on_source_select(self) -> None:
        """Handle data source selection change."""
        if self.source_select.value is not None:
            # Find the DataSource by index
            idx = self.source_select.value
            if 0 <= idx < len(self.state.data_sources):
                self.selected_source = self.state.data_sources[idx]
                self._update_table()

    def _on_state_change(self) -> None:
        """Handle state changes."""
        # Update source selector options - use index as value, display_name as label
        options = {i: ds.display_name for i, ds in enumerate(self.state.data_sources)}
        self.source_select.options = options

        # Auto-select first source if none selected
        if self.selected_source is None and self.state.data_sources:
            self.selected_source = self.state.data_sources[0]
            self.source_select.value = 0

        # Clear selection if selected source no longer exists
        if self.selected_source and self.selected_source not in self.state.data_sources:
            self.selected_source = None
            self.source_select.value = None

        self._update_table()

    def _update_table(self) -> None:
        """Update the preview table."""
        self.table_container.clear()

        if not self.selected_source or self.selected_source not in self.state.parsed_data:
            with self.table_container:
                ui.label("No data loaded").classes("text-gray-500 italic p-4")
            self.row_info.text = "No data loaded"
            return

        df = self.state.parsed_data[self.selected_source]
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
