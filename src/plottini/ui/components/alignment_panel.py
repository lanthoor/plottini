"""Alignment panel for multi-file alignment.

Provides UI for enabling alignment of multiple DataFrames
by a common column for consistent plotting.
"""

from __future__ import annotations

from nicegui import ui

from plottini.config.schema import AlignmentConfig
from plottini.ui.state import AppState


class AlignmentPanel:
    """Component for managing multi-file alignment."""

    def __init__(self, state: AppState) -> None:
        """Initialize alignment panel.

        Args:
            state: Application state
        """
        self.state = state
        self._create_ui()
        state.add_change_callback(self._update_column_options)

    def _create_ui(self) -> None:
        """Create the alignment panel UI."""
        with ui.card().classes("w-full"):
            ui.label("Multi-File Alignment").classes("text-lg font-semibold mb-2")
            with ui.row().classes("items-center gap-4"):
                self.enabled = ui.checkbox(
                    "Enable alignment",
                    value=(self.state.alignment.enabled if self.state.alignment else False),
                    on_change=self._on_alignment_change,
                )
                self.column_select = ui.select(
                    [],
                    label="Align by column",
                    value=(
                        self.state.alignment.column
                        if self.state.alignment and self.state.alignment.column
                        else None
                    ),
                    on_change=self._on_alignment_change,
                ).classes("w-48")

            # Info text
            self.info_label = ui.label("Load multiple files to enable alignment").classes(
                "text-sm text-gray-500 mt-2"
            )

    def _on_alignment_change(self) -> None:
        """Handle alignment settings change."""
        self.state.alignment = AlignmentConfig(
            enabled=bool(self.enabled.value),
            column=str(self.column_select.value) if self.column_select.value else "",
        )
        self.state.notify_change()

    def _update_column_options(self) -> None:
        """Update column options when data changes."""
        columns = self.state.get_all_column_names()
        self.column_select.options = columns

        # Update enabled state based on file count
        has_multiple = len(self.state.loaded_files) > 1
        self.enabled.enabled = has_multiple

        if has_multiple:
            self.info_label.text = "Align data from multiple files by a common column"
        else:
            self.info_label.text = "Load multiple files to enable alignment"


def create_alignment_panel(state: AppState) -> AlignmentPanel:
    """Factory function to create AlignmentPanel component.

    Args:
        state: Application state

    Returns:
        AlignmentPanel instance
    """
    return AlignmentPanel(state)


__all__ = ["AlignmentPanel", "create_alignment_panel"]
