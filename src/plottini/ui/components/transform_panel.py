"""Transform panel for derived columns and data transformations.

Provides UI for creating derived columns using mathematical expressions
and displaying available functions.
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from plottini.config.schema import DerivedColumnConfig
from plottini.core.transforms import ALLOWED_FUNCTIONS
from plottini.ui.state import AppState


class TransformPanel:
    """Component for managing data transformations and derived columns."""

    def __init__(self, state: AppState) -> None:
        """Initialize transform panel.

        Args:
            state: Application state
        """
        self.state = state
        self._create_ui()
        state.add_change_callback(self._update_column_info)

    def _create_ui(self) -> None:
        """Create the transform panel UI."""
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Derived Columns").classes("text-lg font-semibold")
                ui.button(
                    "Add Column",
                    icon="add",
                    on_click=self._add_derived_column,
                ).props("flat dense")

            # Derived columns list
            self.columns_container = ui.column().classes("w-full gap-2")
            self._update_derived_columns()

            # Help text
            ui.separator().classes("my-2")
            self.column_info = ui.label("Available columns: (load files first)").classes(
                "text-sm text-gray-500"
            )
            ui.label(f"Functions: {', '.join(sorted(ALLOWED_FUNCTIONS))}").classes(
                "text-sm text-gray-500"
            )

    def _add_derived_column(self) -> None:
        """Add a new derived column entry."""
        self.state.derived_columns.append(DerivedColumnConfig(name="", expression=""))
        self._update_derived_columns()

    def _remove_derived_column(self, index: int) -> None:
        """Remove a derived column by index.

        Args:
            index: Index of column to remove
        """
        if 0 <= index < len(self.state.derived_columns):
            self.state.derived_columns.pop(index)
            self._update_derived_columns()
            self._apply_derived_columns()

    def _update_derived_columns(self) -> None:
        """Update the derived columns list UI."""
        self.columns_container.clear()
        with self.columns_container:
            if not self.state.derived_columns:
                ui.label("No derived columns").classes("text-gray-500 italic")
            else:
                for i, dc in enumerate(self.state.derived_columns):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.input(
                            "Name",
                            value=dc.name,
                            on_change=lambda e, idx=i: self._on_column_change(idx, "name", e.value),
                        ).classes("w-32")
                        ui.input(
                            "Expression",
                            value=dc.expression,
                            on_change=lambda e, idx=i: self._on_column_change(
                                idx, "expression", e.value
                            ),
                        ).classes("flex-grow")
                        ui.button(
                            icon="delete",
                            on_click=lambda _e=None, idx=i: self._remove_derived_column(idx),
                        ).props("flat dense round")

    def _on_column_change(self, index: int, field: str, value: Any) -> None:
        """Handle derived column field change.

        Args:
            index: Index of column being changed
            field: Field name ('name' or 'expression')
            value: New value
        """
        if 0 <= index < len(self.state.derived_columns):
            dc = self.state.derived_columns[index]
            if field == "name":
                self.state.derived_columns[index] = DerivedColumnConfig(
                    name=str(value), expression=dc.expression
                )
            elif field == "expression":
                self.state.derived_columns[index] = DerivedColumnConfig(
                    name=dc.name, expression=str(value)
                )
            self._apply_derived_columns()

    def _apply_derived_columns(self) -> None:
        """Apply derived columns to all DataFrames."""
        for df in self.state.parsed_data.values():
            for dc in self.state.derived_columns:
                if dc.name and dc.expression:
                    # Skip if column already exists
                    if dc.name in df:
                        continue
                    try:
                        df.add_derived_column(dc.name, dc.expression)
                        self.state.clear_error()
                    except Exception as e:
                        self.state.set_error(f"Expression error: {e}")
                        return
        self.state.notify_change()

    def _update_column_info(self) -> None:
        """Update available columns info."""
        columns = self.state.get_all_column_names()
        if columns:
            self.column_info.text = f"Available columns: {', '.join(columns)}"
        else:
            self.column_info.text = "Available columns: (load files first)"


def create_transform_panel(state: AppState) -> TransformPanel:
    """Factory function to create TransformPanel component.

    Args:
        state: Application state

    Returns:
        TransformPanel instance
    """
    return TransformPanel(state)


__all__ = ["TransformPanel", "create_transform_panel"]
