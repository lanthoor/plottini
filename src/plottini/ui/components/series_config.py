"""Series configuration component.

Provides UI for configuring data series including column mapping,
colors, line styles, markers, and file source.
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from plottini.core.plotter import COLORBLIND_PALETTE, SeriesConfig
from plottini.ui.state import AppState

LINE_STYLE_OPTIONS = [
    ("-", "Solid"),
    ("--", "Dashed"),
    ("-.", "Dash-dot"),
    (":", "Dotted"),
]

MARKER_OPTIONS = [
    ("", "None"),
    ("o", "Circle"),
    ("s", "Square"),
    ("^", "Triangle"),
    ("D", "Diamond"),
    ("*", "Star"),
    ("+", "Plus"),
    ("x", "Cross"),
]


class SeriesConfigPanel:
    """Component for configuring data series."""

    def __init__(self, state: AppState) -> None:
        """Initialize series config panel.

        Args:
            state: Application state
        """
        self.state = state
        self._create_ui()
        state.add_change_callback(self._on_state_change)

    def _create_ui(self) -> None:
        """Create the series config UI."""
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Data Series").classes("text-lg font-semibold")
                ui.button(
                    "Add Series",
                    icon="add_chart",
                    on_click=self._add_series,
                ).props("flat dense")

            self.series_container = ui.column().classes("w-full gap-4")
            self._update_series()

    def _add_series(self) -> None:
        """Add a new series entry."""
        columns = self.state.get_all_column_names()
        x_col = columns[0] if columns else ""
        y_col = columns[1] if len(columns) > 1 else x_col

        # Auto-assign color from palette
        color_idx = len(self.state.series) % len(COLORBLIND_PALETTE)

        self.state.series.append(
            SeriesConfig(
                x_column=x_col,
                y_column=y_col,
                label=f"Series {len(self.state.series) + 1}",
                color=COLORBLIND_PALETTE[color_idx],
            )
        )
        self._update_series()
        self.state.notify_change()

    def _remove_series(self, index: int) -> None:
        """Remove a series by index.

        Args:
            index: Index of series to remove
        """
        if 0 <= index < len(self.state.series):
            self.state.series.pop(index)
            self._update_series()
            self.state.notify_change()

    def _update_series(self) -> None:
        """Update the series list UI."""
        columns = self.state.get_all_column_names()
        n_blocks = len(self.state.data_sources)

        self.series_container.clear()
        with self.series_container:
            if not self.state.series:
                ui.label("No series configured").classes("text-gray-500 italic")
                ui.label("Add a series to configure data for plotting").classes(
                    "text-sm text-gray-400"
                )
            else:
                # Show info about multi-block behavior
                if n_blocks > 1:
                    with ui.row().classes(
                        "w-full items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900 rounded mb-2"
                    ):
                        ui.icon("info").classes("text-blue-500")
                        ui.label(
                            f"Each series will plot {n_blocks} lines (one per data block) with different colors"
                        ).classes("text-sm text-blue-700 dark:text-blue-200")

                for i, s in enumerate(self.state.series):
                    with ui.card().classes("w-full p-4 bg-gray-50 dark:bg-gray-800"):
                        # Header row with title and delete
                        with ui.row().classes("w-full justify-between items-center mb-2"):
                            ui.label(f"Series {i + 1}").classes("font-semibold")
                            ui.button(
                                icon="delete",
                                on_click=lambda _e=None, idx=i: self._remove_series(idx),
                            ).props("flat dense round color=negative")

                        # Row 1: Column selection and label
                        with ui.row().classes("w-full items-end gap-2 flex-wrap"):
                            ui.select(
                                columns,
                                label="X Column",
                                value=s.x_column,
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "x_column", e.value
                                ),
                            ).classes("w-32")
                            ui.select(
                                columns,
                                label="Y Column",
                                value=s.y_column,
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "y_column", e.value
                                ),
                            ).classes("w-32")
                            ui.input(
                                "Label",
                                value=s.label or "",
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "label", e.value
                                ),
                            ).classes("flex-grow")

                        # Row 2: Style options
                        with ui.row().classes("w-full items-end gap-2 flex-wrap mt-2"):
                            ui.color_input(
                                "Color",
                                value=s.color or COLORBLIND_PALETTE[0],
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "color", e.value
                                ),
                            ).classes("w-28")
                            ui.select(
                                dict(LINE_STYLE_OPTIONS),
                                label="Line Style",
                                value=s.line_style,
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "line_style", e.value
                                ),
                            ).classes("w-28")
                            ui.select(
                                dict(MARKER_OPTIONS),
                                label="Marker",
                                value=s.marker or "",
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "marker", e.value or None
                                ),
                            ).classes("w-28")
                            ui.number(
                                "Line Width",
                                value=s.line_width,
                                min=0.5,
                                max=5.0,
                                step=0.5,
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "line_width", e.value
                                ),
                            ).classes("w-24")

                        # Row 3: Advanced options
                        with ui.row().classes("w-full items-center gap-4 mt-2"):
                            ui.checkbox(
                                "Secondary Y-axis",
                                value=s.use_secondary_y,
                                on_change=lambda e, idx=i: self._on_series_change(
                                    idx, "use_secondary_y", e.value
                                ),
                            )
                            # Note: Source file selector removed - series automatically
                            # plots across all blocks/files with the same column names

    def _on_series_change(self, index: int, field: str, value: Any) -> None:
        """Handle series field change.

        Args:
            index: Index of series being changed
            field: Field name
            value: New value
        """
        if 0 <= index < len(self.state.series):
            s = self.state.series[index]
            # Create new SeriesConfig with updated field
            kwargs: dict[str, Any] = {
                "x_column": s.x_column,
                "y_column": s.y_column,
                "label": s.label,
                "color": s.color,
                "line_style": s.line_style,
                "marker": s.marker,
                "line_width": s.line_width,
                "use_secondary_y": s.use_secondary_y,
                "source_file_index": s.source_file_index,
            }
            kwargs[field] = value
            self.state.series[index] = SeriesConfig(**kwargs)
            self.state.notify_change()

    def _on_state_change(self) -> None:
        """Handle state changes from other components.

        Refreshes the series UI when files/columns change.
        """
        self._update_series()


def create_series_config(state: AppState) -> SeriesConfigPanel:
    """Factory function to create SeriesConfigPanel component.

    Args:
        state: Application state

    Returns:
        SeriesConfigPanel instance
    """
    return SeriesConfigPanel(state)


__all__ = ["SeriesConfigPanel", "create_series_config"]
