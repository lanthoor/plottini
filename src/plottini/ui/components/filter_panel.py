"""Filter panel component for row filtering.

Provides UI for filtering DataFrame rows by value ranges on specific columns.
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from plottini.config.schema import FilterConfig
from plottini.ui.state import AppState


class FilterPanel:
    """Component for managing data filters."""

    def __init__(self, state: AppState) -> None:
        """Initialize filter panel.

        Args:
            state: Application state
        """
        self.state = state
        self._create_ui()
        state.add_change_callback(self._update_column_options)

    def _create_ui(self) -> None:
        """Create the filter panel UI."""
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Data Filters").classes("text-lg font-semibold")
                ui.button(
                    "Add Filter",
                    icon="filter_list",
                    on_click=self._add_filter,
                ).props("flat dense")

            self.filters_container = ui.column().classes("w-full gap-2")
            self._update_filters()

    def _add_filter(self) -> None:
        """Add a new filter entry."""
        columns = self.state.get_all_column_names()
        default_column = columns[0] if columns else ""
        self.state.filters.append(FilterConfig(column=default_column, min=None, max=None))
        self._update_filters()

    def _remove_filter(self, index: int) -> None:
        """Remove a filter by index.

        Args:
            index: Index of filter to remove
        """
        if 0 <= index < len(self.state.filters):
            self.state.filters.pop(index)
            self._update_filters()
            self.state.notify_change()

    def _update_filters(self) -> None:
        """Update the filters list UI."""
        columns = self.state.get_all_column_names()
        self.filters_container.clear()
        with self.filters_container:
            if not self.state.filters:
                ui.label("No filters").classes("text-gray-500 italic")
            else:
                for i, f in enumerate(self.state.filters):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.select(
                            columns,
                            label="Column",
                            value=f.column,
                            on_change=lambda e, idx=i: self._on_filter_change(
                                idx, "column", e.value
                            ),
                        ).classes("w-32")
                        ui.number(
                            "Min",
                            value=f.min,
                            on_change=lambda e, idx=i: self._on_filter_change(idx, "min", e.value),
                        ).classes("w-24")
                        ui.number(
                            "Max",
                            value=f.max,
                            on_change=lambda e, idx=i: self._on_filter_change(idx, "max", e.value),
                        ).classes("w-24")
                        ui.button(
                            icon="delete",
                            on_click=lambda _e=None, idx=i: self._remove_filter(idx),
                        ).props("flat dense round")

    def _on_filter_change(self, index: int, field: str, value: Any) -> None:
        """Handle filter field change.

        Args:
            index: Index of filter being changed
            field: Field name ('column', 'min', or 'max')
            value: New value
        """
        if 0 <= index < len(self.state.filters):
            f = self.state.filters[index]
            if field == "column":
                self.state.filters[index] = FilterConfig(
                    column=str(value) if value else "",
                    min=f.min,
                    max=f.max,
                )
            elif field == "min":
                self.state.filters[index] = FilterConfig(
                    column=f.column,
                    min=float(value) if value is not None else None,
                    max=f.max,
                )
            elif field == "max":
                self.state.filters[index] = FilterConfig(
                    column=f.column,
                    min=f.min,
                    max=float(value) if value is not None else None,
                )
            self.state.notify_change()

    def _update_column_options(self) -> None:
        """Update column options when data changes."""
        self._update_filters()


def create_filter_panel(state: AppState) -> FilterPanel:
    """Factory function to create FilterPanel component.

    Args:
        state: Application state

    Returns:
        FilterPanel instance
    """
    return FilterPanel(state)


__all__ = ["FilterPanel", "create_filter_panel"]
