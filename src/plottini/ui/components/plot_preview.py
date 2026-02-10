"""Live preview component for matplotlib figures.

Provides a live-updating preview of the current plot with
debounced updates for responsive UI.
"""

from __future__ import annotations

import asyncio
import base64
import io
from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
from nicegui import ui

from plottini.core.dataframe import align_dataframes
from plottini.core.plotter import COLORBLIND_PALETTE, Plotter, SeriesConfig
from plottini.ui.state import AppState

if TYPE_CHECKING:
    from matplotlib.figure import Figure

# Use non-interactive backend for thread safety
matplotlib.use("Agg")


class PlotPreview:
    """Component for live plot preview."""

    DEBOUNCE_MS = 300

    def __init__(self, state: AppState) -> None:
        """Initialize plot preview.

        Args:
            state: Application state
        """
        self.state = state
        self._debounce_task: asyncio.Task[None] | None = None
        self._create_ui()
        state.add_change_callback(self._schedule_update)

    def _create_ui(self) -> None:
        """Create the preview UI."""
        with ui.card().classes("w-full h-full"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label("Preview").classes("text-lg font-semibold")
                with ui.row().classes("gap-2 items-center"):
                    ui.button(
                        "Refresh",
                        icon="refresh",
                        on_click=self._render_preview,
                    ).props("flat dense")
                    ui.label("Zoom:")
                    self.zoom_slider = ui.slider(
                        min=50,
                        max=200,
                        value=100,
                        step=10,
                        on_change=self._on_zoom_change,
                    ).classes("w-32")
                    self.zoom_label = ui.label("100%").classes("w-12")

            # Plot image container
            self.plot_container = (
                ui.column().classes("w-full items-center justify-center").style("min-height: 400px")
            )

            # Error display
            self.error_display = ui.label("").classes("text-red-500 mt-2")

            # Initial placeholder
            self._show_placeholder("Load data and add series to see preview")

    def _on_zoom_change(self) -> None:
        """Handle zoom slider change."""
        self.zoom_label.text = f"{int(self.zoom_slider.value)}%"
        # Re-render with new zoom
        if self.state.current_figure:
            self._display_figure(self.state.current_figure)

    def _schedule_update(self) -> None:
        """Schedule a debounced preview update."""
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        self._debounce_task = asyncio.create_task(self._debounced_update())

    async def _debounced_update(self) -> None:
        """Wait for debounce period then update preview."""
        try:
            await asyncio.sleep(self.DEBOUNCE_MS / 1000)
            self._render_preview()
        except asyncio.CancelledError:
            pass

    def _render_preview(self) -> None:
        """Render the current plot configuration."""
        self.error_display.text = ""

        # Check if we have data and series
        if not self.state.parsed_data:
            self._show_placeholder("Load data files to see preview")
            return
        if not self.state.series:
            self._show_placeholder("Add series to see preview")
            return

        try:
            # Get DataFrames
            dataframes = self.state.get_dataframes_list()

            if not dataframes:
                self._show_placeholder("No data available")
                return

            # Apply filters
            for f in self.state.filters:
                if f.column and (f.min is not None or f.max is not None):
                    try:
                        dataframes = [df.filter_rows(f.column, f.min, f.max) for df in dataframes]
                    except KeyError:
                        # Column doesn't exist in some dataframes
                        pass

            # Apply alignment if enabled
            if (
                self.state.alignment
                and self.state.alignment.enabled
                and self.state.alignment.column
                and len(dataframes) > 1
            ):
                try:
                    aligned = align_dataframes(dataframes, self.state.alignment.column)
                    dataframes = aligned.dataframes
                except (KeyError, ValueError):
                    # Alignment column doesn't exist or other issue
                    pass

            # Expand series across all blocks
            expanded_series = self._expand_series_for_blocks(dataframes)

            # Create plotter and render
            plotter = Plotter(self.state.plot_config)
            fig = plotter.create_figure(dataframes, expanded_series)

            # Store figure in state
            self.state.current_figure = fig

            # Convert to image and display
            self._display_figure(fig)
            self.state.clear_error()

        except Exception as e:
            self.error_display.text = f"Error: {e}"
            self.state.set_error(str(e))
            self._show_placeholder(f"Rendering error: {e}")

    def _expand_series_for_blocks(self, dataframes: list) -> list[SeriesConfig]:
        """Expand series configurations to plot each block with different colors.

        For each series configuration, creates separate SeriesConfig entries
        for each DataFrame (block), assigning distinct colors from the palette.

        Args:
            dataframes: List of DataFrames to plot

        Returns:
            Expanded list of SeriesConfig with one entry per block per series
        """
        expanded: list[SeriesConfig] = []
        color_idx = 0

        for series in self.state.series:
            # For each user-defined series, create one line per block
            for df_idx, df in enumerate(dataframes):
                # Check if this DataFrame has the required columns
                if series.x_column not in df or series.y_column not in df:
                    continue

                # Create label with block info if multiple blocks
                if len(dataframes) > 1:
                    block_info = (
                        f" (block {df_idx + 1})"
                        if df.block_index is not None
                        else f" ({df_idx + 1})"
                    )
                    label = f"{series.label or series.y_column}{block_info}"
                else:
                    label = series.label

                # Assign color from palette (cycle through)
                color = COLORBLIND_PALETTE[color_idx % len(COLORBLIND_PALETTE)]
                color_idx += 1

                expanded.append(
                    SeriesConfig(
                        x_column=series.x_column,
                        y_column=series.y_column,
                        label=label,
                        color=color,
                        line_style=series.line_style,
                        marker=series.marker,
                        line_width=series.line_width,
                        use_secondary_y=series.use_secondary_y,
                        source_file_index=df_idx,
                    )
                )

        return expanded

    def _display_figure(self, fig: Figure) -> None:
        """Display matplotlib figure as image.

        Args:
            fig: Matplotlib figure to display
        """
        # Convert figure to PNG bytes
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        buf.seek(0)

        # Encode as base64
        img_data = base64.b64encode(buf.read()).decode("utf-8")

        # Update image
        self.plot_container.clear()
        with self.plot_container:
            zoom = self.zoom_slider.value / 100
            ui.image(f"data:image/png;base64,{img_data}").style(
                f"max-width: 100%; transform: scale({zoom}); transform-origin: top center;"
            )

        # Close figure to free memory
        plt.close(fig)

    def _show_placeholder(self, message: str) -> None:
        """Show placeholder message instead of plot.

        Args:
            message: Message to display
        """
        self.plot_container.clear()
        with self.plot_container:
            with ui.column().classes("items-center justify-center p-8"):
                ui.icon("image").classes("text-6xl text-gray-300")
                ui.label(message).classes("text-gray-500 text-lg mt-4")


def create_plot_preview(state: AppState) -> PlotPreview:
    """Factory function to create PlotPreview component.

    Args:
        state: Application state

    Returns:
        PlotPreview instance
    """
    return PlotPreview(state)


__all__ = ["PlotPreview", "create_plot_preview"]
