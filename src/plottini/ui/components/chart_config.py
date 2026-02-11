"""Chart configuration component.

Provides UI for selecting chart type and configuring plot appearance.
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from plottini.core.plotter import ChartType, PlotConfig
from plottini.ui.state import AppState

CHART_TYPE_OPTIONS = [
    (ChartType.LINE, "Line", "show_chart"),
    (ChartType.BAR, "Bar", "bar_chart"),
    (ChartType.PIE, "Pie", "pie_chart"),
    (ChartType.SCATTER, "Scatter", "scatter_plot"),
    (ChartType.HISTOGRAM, "Histogram", "equalizer"),
    (ChartType.POLAR, "Polar", "radar"),
    (ChartType.BOX, "Box", "candlestick_chart"),
    (ChartType.VIOLIN, "Violin", "stacked_line_chart"),
    (ChartType.AREA, "Area", "area_chart"),
    (ChartType.STEM, "Stem", "stacked_bar_chart"),
    (ChartType.STEP, "Step", "stair"),
    (ChartType.ERRORBAR, "Error Bar", "error"),
    (ChartType.BAR_HORIZONTAL, "H-Bar", "align_horizontal_left"),
]


class ChartConfigPanel:
    """Component for configuring chart type and appearance."""

    def __init__(self, state: AppState) -> None:
        """Initialize chart config panel.

        Args:
            state: Application state
        """
        self.state = state
        self._chart_buttons: dict[ChartType, ui.button] = {}
        self._create_ui()
        state.add_change_callback(self._update_y2_visibility)

    def _create_ui(self) -> None:
        """Create the chart config UI."""
        # Chart type selection
        with ui.card().classes("w-full"):
            ui.label("Chart Type").classes("text-lg font-semibold mb-2")
            with ui.row().classes("flex-wrap gap-1"):
                for chart_type, label, icon in CHART_TYPE_OPTIONS:
                    btn = ui.button(
                        label,
                        icon=icon,
                        on_click=lambda _e=None, ct=chart_type: self._set_chart_type(ct),
                    ).props("dense")
                    if self.state.plot_config.chart_type == chart_type:
                        btn.props("color=primary")
                    else:
                        btn.props("flat")
                    self._chart_buttons[chart_type] = btn

        # Plot settings
        with ui.card().classes("w-full mt-4"):
            ui.label("Plot Settings").classes("text-lg font-semibold mb-2")

            # Title
            ui.input(
                "Title",
                value=self.state.plot_config.title,
                on_change=lambda e: self._update_config("title", e.value),
            ).classes("w-full")

            # Axis labels
            with ui.row().classes("w-full gap-4"):
                ui.input(
                    "X Label",
                    value=self.state.plot_config.x_label,
                    on_change=lambda e: self._update_config("x_label", e.value),
                ).classes("flex-grow")
                ui.input(
                    "Y Label",
                    value=self.state.plot_config.y_label,
                    on_change=lambda e: self._update_config("y_label", e.value),
                ).classes("flex-grow")

            # Secondary Y label (show only if any series uses secondary axis)
            self.y2_input = ui.input(
                "Y2 Label (Secondary)",
                value=self.state.plot_config.y2_label,
                on_change=lambda e: self._update_config("y2_label", e.value),
            ).classes("w-full")
            self._update_y2_visibility()

            # Figure size
            ui.label("Figure Size").classes("mt-4 font-medium")
            with ui.row().classes("gap-4"):
                ui.number(
                    "Width (inches)",
                    value=self.state.plot_config.figure_width,
                    min=1.0,
                    max=30.0,
                    step=0.5,
                    on_change=lambda e: self._update_config("figure_width", e.value),
                ).classes("w-32")
                ui.number(
                    "Height (inches)",
                    value=self.state.plot_config.figure_height,
                    min=1.0,
                    max=30.0,
                    step=0.5,
                    on_change=lambda e: self._update_config("figure_height", e.value),
                ).classes("w-32")

            # Options
            with ui.row().classes("gap-4 mt-4"):
                ui.checkbox(
                    "Show Grid",
                    value=self.state.plot_config.show_grid,
                    on_change=lambda e: self._update_config("show_grid", e.value),
                )
                ui.checkbox(
                    "Show Legend",
                    value=self.state.plot_config.show_legend,
                    on_change=lambda e: self._update_config("show_legend", e.value),
                )

    def _set_chart_type(self, chart_type: ChartType) -> None:
        """Set the chart type.

        Args:
            chart_type: Chart type to set
        """
        # Update button styles
        for ct, btn in self._chart_buttons.items():
            if ct == chart_type:
                btn.props("color=primary")
                btn.props(remove="flat")
            else:
                btn.props("flat")
                btn.props(remove="color=primary")

        self._update_config("chart_type", chart_type)

    def _update_config(self, field: str, value: Any) -> None:
        """Update plot config field.

        Args:
            field: Field name to update
            value: New value
        """
        kwargs: dict[str, Any] = {
            "chart_type": self.state.plot_config.chart_type,
            "title": self.state.plot_config.title,
            "x_label": self.state.plot_config.x_label,
            "y_label": self.state.plot_config.y_label,
            "y2_label": self.state.plot_config.y2_label,
            "figure_width": self.state.plot_config.figure_width,
            "figure_height": self.state.plot_config.figure_height,
            "show_grid": self.state.plot_config.show_grid,
            "show_legend": self.state.plot_config.show_legend,
        }
        kwargs[field] = value
        self.state.plot_config = PlotConfig(**kwargs)
        self.state.notify_change()

    def _update_y2_visibility(self) -> None:
        """Show/hide Y2 label input based on series configuration."""
        has_secondary = any(s.use_secondary_y for s in self.state.series)
        self.y2_input.visible = has_secondary


def create_chart_config(state: AppState) -> ChartConfigPanel:
    """Factory function to create ChartConfigPanel component.

    Args:
        state: Application state

    Returns:
        ChartConfigPanel instance
    """
    return ChartConfigPanel(state)


__all__ = ["ChartConfigPanel", "create_chart_config"]
