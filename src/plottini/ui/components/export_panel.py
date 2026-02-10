"""Export panel component.

Provides UI for configuring and executing figure export to
PNG, SVG, PDF, and EPS formats.
"""

from __future__ import annotations

from pathlib import Path

from nicegui import ui

from plottini.core.exporter import ExportConfig, Exporter, ExportFormat
from plottini.ui.state import AppState


class ExportPanel:
    """Component for exporting figures."""

    def __init__(self, state: AppState) -> None:
        """Initialize export panel.

        Args:
            state: Application state
        """
        self.state = state
        self.export_format = ExportFormat.PNG
        self.dpi = 300
        self.transparent = False
        self.output_path = ""
        self._format_buttons: dict[ExportFormat, ui.button] = {}
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the export panel UI."""
        with ui.card().classes("w-full"):
            ui.label("Export Settings").classes("text-lg font-semibold mb-2")

            # Format selection
            ui.label("Format").classes("font-medium mt-2")
            with ui.row().classes("gap-1"):
                for fmt in ExportFormat:
                    btn = ui.button(
                        fmt.value.upper(),
                        on_click=lambda _e=None, f=fmt: self._set_format(f),
                    ).props("dense")
                    if self.export_format == fmt:
                        btn.props("color=primary")
                    else:
                        btn.props("flat")
                    self._format_buttons[fmt] = btn

            # DPI (only for PNG)
            self.dpi_container = ui.row().classes("items-end gap-2 mt-4")
            with self.dpi_container:
                self.dpi_input = ui.number(
                    "DPI (resolution)",
                    value=self.dpi,
                    min=72,
                    max=600,
                    step=50,
                    on_change=lambda e: setattr(self, "dpi", int(e.value) if e.value else 300),
                ).classes("w-32")

            # Transparent background
            ui.checkbox(
                "Transparent background",
                value=self.transparent,
                on_change=lambda e: setattr(self, "transparent", bool(e.value)),
            ).classes("mt-2")

            ui.separator().classes("my-4")

            # Output path
            ui.label("Output File").classes("font-medium")
            self.path_input = ui.input(
                "Output path",
                value=self.output_path,
                placeholder="/path/to/output.png",
                on_change=lambda e: setattr(self, "output_path", str(e.value)),
            ).classes("w-full")

            # Export button
            ui.button(
                "Export",
                icon="download",
                on_click=self._export,
            ).classes("w-full mt-4").props("color=primary")

            # Status message
            self.status_label = ui.label("").classes("text-center mt-2")

    def _set_format(self, fmt: ExportFormat) -> None:
        """Set the export format.

        Args:
            fmt: Export format to set
        """
        self.export_format = fmt

        # Update button styles
        for f, btn in self._format_buttons.items():
            if f == fmt:
                btn.props("color=primary")
                btn.props(remove="flat")
            else:
                btn.props("flat")
                btn.props(remove="color=primary")

        # Show/hide DPI input based on format
        self.dpi_input.visible = fmt == ExportFormat.PNG

        # Update default extension in path
        if self.output_path:
            path = Path(self.output_path)
            new_path = path.with_suffix(f".{fmt.value}")
            self.path_input.value = str(new_path)
            self.output_path = str(new_path)

    async def _export(self) -> None:
        """Export the current figure."""
        if not self.state.current_figure:
            self.status_label.text = "No figure to export. Generate preview first."
            self.status_label.classes(remove="text-green-600", add="text-orange-500")
            ui.notify(
                "No figure to export. Switch to Export tab to generate preview.",
                type="warning",
            )
            return

        if not self.output_path:
            self.status_label.text = "Please specify an output path."
            self.status_label.classes(remove="text-green-600", add="text-orange-500")
            ui.notify("Please specify an output path.", type="warning")
            return

        try:
            exporter = Exporter()
            config = ExportConfig(
                format=self.export_format,
                dpi=self.dpi,
                transparent=self.transparent,
            )

            output = exporter.export(
                self.state.current_figure,
                Path(self.output_path),
                config,
            )

            self.status_label.text = f"Exported to: {output}"
            self.status_label.classes(remove="text-red-500 text-orange-500", add="text-green-600")
            ui.notify(f"Exported to: {output}", type="positive")

        except Exception as e:
            self.status_label.text = f"Export failed: {e}"
            self.status_label.classes(remove="text-green-600 text-orange-500", add="text-red-500")
            ui.notify(f"Export failed: {e}", type="negative")


def create_export_panel(state: AppState) -> ExportPanel:
    """Factory function to create ExportPanel component.

    Args:
        state: Application state

    Returns:
        ExportPanel instance
    """
    return ExportPanel(state)


__all__ = ["ExportPanel", "create_export_panel"]
