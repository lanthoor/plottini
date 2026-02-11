"""Main NiceGUI application for Plottini.

This module provides the entry point for the web UI and defines
the main application layout with tabbed navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from nicegui import ui

from plottini import __version__
from plottini.config.loader import load_config, save_config
from plottini.config.schema import (
    ExportConfigSchema,
    FileConfig,
    GrapherConfig,
    PlotConfigSchema,
    SeriesConfigSchema,
)
from plottini.core.parser import ParserConfig, TSVParser
from plottini.core.plotter import ChartType, PlotConfig, SeriesConfig
from plottini.ui.state import DataSource, create_default_state

if TYPE_CHECKING:
    pass


class PlottiniApp:
    """Main Plottini application class.

    Manages the application state and UI structure with tabbed layout.
    """

    def __init__(self, config_file: Path | None = None) -> None:
        """Initialize the application.

        Args:
            config_file: Optional config file to load on startup
        """
        self.state = create_default_state()
        self._setup_ui()

        # Load config if provided
        if config_file:
            self._load_config_file(config_file)

    def _setup_ui(self) -> None:
        """Set up the main UI structure."""
        # Apply dark mode toggle support
        ui.dark_mode().auto()

        # Header with logo and config buttons
        with ui.header().classes("items-center justify-between px-4 py-2 bg-blue-600"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("bar_chart").classes("text-2xl text-white")
                ui.label("Plottini").classes("text-xl font-bold text-white")
                ui.label(f"v{__version__}").classes("text-sm text-blue-200")

            with ui.row().classes("gap-2"):
                ui.button(
                    "Load Config",
                    icon="folder_open",
                    on_click=self._show_load_dialog,
                ).props("flat color=white")
                ui.button(
                    "Save Config",
                    icon="save",
                    on_click=self._show_save_dialog,
                ).props("flat color=white")

        # Main content with tabs
        with ui.column().classes("w-full flex-grow p-4"):
            with ui.tabs().classes("w-full") as self.tabs:
                self.data_tab = ui.tab("Data", icon="table_chart")
                self.series_tab = ui.tab("Series", icon="show_chart")
                self.settings_tab = ui.tab("Settings", icon="settings")
                self.export_tab = ui.tab("Export", icon="download")

            with ui.tab_panels(self.tabs, value=self.data_tab).classes("w-full flex-grow"):
                with ui.tab_panel(self.data_tab).classes("p-0"):
                    self._create_data_tab()
                with ui.tab_panel(self.series_tab).classes("p-0"):
                    self._create_series_tab()
                with ui.tab_panel(self.settings_tab).classes("p-0"):
                    self._create_settings_tab()
                with ui.tab_panel(self.export_tab).classes("p-0"):
                    self._create_export_tab()

        # Status bar / footer
        with ui.footer().classes("bg-gray-100 dark:bg-gray-800 px-4 py-2 flex justify-between"):
            self.status_label = ui.label("Ready").classes(
                "text-sm text-gray-600 dark:text-gray-300"
            )
            self.info_label = ui.label("").classes("text-sm text-gray-500 dark:text-gray-400")
            self.state.add_change_callback(self._update_status)

    def _create_data_tab(self) -> None:
        """Create the Data tab content."""
        # Import here to avoid circular imports
        from plottini.ui.components.data_tab import create_data_tab

        create_data_tab(self.state)

    def _create_series_tab(self) -> None:
        """Create the Series tab content."""
        from plottini.ui.components.series_tab import create_series_tab

        create_series_tab(self.state)

    def _create_settings_tab(self) -> None:
        """Create the Settings tab content."""
        from plottini.ui.components.settings_tab import create_settings_tab

        create_settings_tab(self.state)

    def _create_export_tab(self) -> None:
        """Create the Export tab content."""
        from plottini.ui.components.export_tab import create_export_tab

        create_export_tab(self.state)

    def _update_status(self) -> None:
        """Update the status bar."""
        n_files = len(self.state.loaded_files)
        n_series = len(self.state.series)

        if self.state.error_message:
            self.status_label.text = f"Error: {self.state.error_message}"
            self.status_label.classes(
                remove="text-gray-600 dark:text-gray-300",
                add="text-red-600 dark:text-red-400",
            )
        else:
            self.status_label.text = "Ready"
            self.status_label.classes(
                remove="text-red-600 dark:text-red-400",
                add="text-gray-600 dark:text-gray-300",
            )

        self.info_label.text = f"Files: {n_files} | Series: {n_series}"

    async def _show_load_dialog(self) -> None:
        """Show file picker dialog for loading config."""
        # Create a dialog for file path input
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Load Configuration").classes("text-lg font-semibold")
            path_input = ui.input(
                "Config file path (.toml)",
                placeholder="/path/to/config.toml",
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Load",
                    on_click=lambda: self._do_load_config(path_input.value, dialog),
                ).props("color=primary")

        dialog.open()

    async def _show_save_dialog(self) -> None:
        """Show file picker dialog for saving config."""
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Save Configuration").classes("text-lg font-semibold")
            path_input = ui.input(
                "Output file path (.toml)",
                placeholder="/path/to/config.toml",
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Save",
                    on_click=lambda: self._do_save_config(path_input.value, dialog),
                ).props("color=primary")

        dialog.open()

    def _do_load_config(self, path_str: str, dialog: ui.dialog) -> None:
        """Load configuration from file.

        Args:
            path_str: Path to config file
            dialog: Dialog to close on success
        """
        if not path_str:
            ui.notify("Please enter a file path", type="warning")
            return

        path = Path(path_str)
        if not path.exists():
            ui.notify(f"File not found: {path}", type="negative")
            return

        try:
            self._load_config_file(path)
            dialog.close()
            ui.notify(f"Loaded configuration from {path.name}", type="positive")
        except Exception as e:
            ui.notify(f"Error loading config: {e}", type="negative")

    def _do_save_config(self, path_str: str, dialog: ui.dialog) -> None:
        """Save configuration to file.

        Args:
            path_str: Path to save config to
            dialog: Dialog to close on success
        """
        if not path_str:
            ui.notify("Please enter a file path", type="warning")
            return

        path = Path(path_str)
        if not path.suffix:
            path = path.with_suffix(".toml")

        try:
            config = self._state_to_config()
            save_config(config, path)
            dialog.close()
            ui.notify(f"Saved configuration to {path.name}", type="positive")
        except Exception as e:
            ui.notify(f"Error saving config: {e}", type="negative")

    def _load_config_file(self, path: Path) -> None:
        """Load configuration from file and update state.

        Args:
            path: Path to config file
        """
        config = load_config(path)
        self._config_to_state(config)

    def _config_to_state(self, config: GrapherConfig) -> None:
        """Update state from a loaded configuration.

        Args:
            config: Configuration to load
        """
        # Clear existing state
        self.state.clear_data()

        # Load parser config from first file (or use defaults)
        if config.files:
            first_file = config.files[0]
            self.state.parser_config = ParserConfig(
                has_header=first_file.has_header,
                comment_chars=first_file.comment_chars,
                delimiter=first_file.delimiter,
                encoding=first_file.encoding,
            )

            # Parse files using parse_blocks to handle multi-block files
            parser = TSVParser(self.state.parser_config)
            for file_config in config.files:
                try:
                    dataframes = parser.parse_blocks(file_config.path)
                    self.state.loaded_files.append(file_config.path)
                    for df in dataframes:
                        ds = DataSource(file_path=file_config.path, block_index=df.block_index)
                        self.state.data_sources.append(ds)
                        self.state.parsed_data[ds] = df
                except Exception as e:
                    self.state.set_error(f"Error loading {file_config.path}: {e}")

        # Load derived columns
        self.state.derived_columns = list(config.derived_columns)

        # Apply derived columns to DataFrames
        for dc in self.state.derived_columns:
            if dc.name and dc.expression:
                for df in self.state.parsed_data.values():
                    try:
                        df.add_derived_column(dc.name, dc.expression)
                    except Exception as e:
                        # Log error but continue loading - don't fail entire config
                        self.state.set_error(f"Error adding derived column '{dc.name}': {e}")

        # Load filters
        self.state.filters = list(config.filters)

        # Load alignment
        self.state.alignment = config.alignment

        # Load series (convert schema to SeriesConfig)
        self.state.series = [
            SeriesConfig(
                x_column=s.x,
                y_column=s.y,
                label=s.label,
                color=s.color,
                line_style=s.line_style,
                marker=s.marker,
                line_width=s.line_width,
                use_secondary_y=s.use_secondary_y,
                source_file_index=s.source_file_index,
            )
            for s in config.series
        ]

        # Load plot config
        chart_type = ChartType.LINE
        for ct in ChartType:
            if ct.value == config.plot.type:
                chart_type = ct
                break

        self.state.plot_config = PlotConfig(
            chart_type=chart_type,
            title=config.plot.title,
            x_label=config.plot.x_label,
            y_label=config.plot.y_label,
            y2_label=config.plot.y2_label,
            figure_width=config.plot.figure_width,
            figure_height=config.plot.figure_height,
            show_grid=config.plot.show_grid,
            show_legend=config.plot.show_legend,
        )

        self.state.notify_change()

    def _state_to_config(self) -> GrapherConfig:
        """Convert current state to a GrapherConfig.

        Returns:
            Configuration representing current state
        """
        # Create file configs
        files = [
            FileConfig(
                path=f,
                has_header=self.state.parser_config.has_header,
                comment_chars=self.state.parser_config.comment_chars,
                delimiter=self.state.parser_config.delimiter,
                encoding=self.state.parser_config.encoding,
            )
            for f in self.state.loaded_files
        ]

        # Convert series to schema format
        series = [
            SeriesConfigSchema(
                x=s.x_column,
                y=s.y_column,
                label=s.label,
                color=s.color,
                line_style=s.line_style,
                marker=s.marker,
                line_width=s.line_width,
                use_secondary_y=s.use_secondary_y,
                source_file_index=s.source_file_index,
            )
            for s in self.state.series
        ]

        # Create plot config schema
        plot = PlotConfigSchema(
            type=self.state.plot_config.chart_type.value,
            title=self.state.plot_config.title,
            x_label=self.state.plot_config.x_label,
            y_label=self.state.plot_config.y_label,
            y2_label=self.state.plot_config.y2_label,
            figure_width=self.state.plot_config.figure_width,
            figure_height=self.state.plot_config.figure_height,
            show_grid=self.state.plot_config.show_grid,
            show_legend=self.state.plot_config.show_legend,
        )

        return GrapherConfig(
            files=files,
            alignment=self.state.alignment,
            derived_columns=list(self.state.derived_columns),
            filters=list(self.state.filters),
            series=series,
            plot=plot,
            export=ExportConfigSchema(),
        )


def start_app(
    port: int = 8050,
    open_browser: bool = True,
    config_file: Path | None = None,
) -> None:
    """Start the Plottini web application.

    Args:
        port: Port to run the server on
        open_browser: Whether to open browser automatically
        config_file: Optional config file to load on startup
    """

    @ui.page("/")
    def main_page() -> None:
        PlottiniApp(config_file=config_file)

    ui.run(
        port=port,
        title="Plottini - Graph Builder",
        favicon="",
        show=open_browser,
        reload=False,
    )


__all__ = ["PlottiniApp", "start_app"]
