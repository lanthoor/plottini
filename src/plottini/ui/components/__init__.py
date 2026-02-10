"""UI components for NiceGUI application."""

from plottini.ui.components.alignment_panel import AlignmentPanel, create_alignment_panel
from plottini.ui.components.chart_config import ChartConfigPanel, create_chart_config
from plottini.ui.components.data_preview import DataPreview, create_data_preview
from plottini.ui.components.data_tab import create_data_tab
from plottini.ui.components.export_panel import ExportPanel, create_export_panel
from plottini.ui.components.export_tab import create_export_tab
from plottini.ui.components.file_selector import FileSelector, create_file_selector
from plottini.ui.components.filter_panel import FilterPanel, create_filter_panel
from plottini.ui.components.plot_preview import PlotPreview, create_plot_preview
from plottini.ui.components.series_config import SeriesConfigPanel, create_series_config
from plottini.ui.components.series_tab import create_series_tab
from plottini.ui.components.settings_tab import create_settings_tab
from plottini.ui.components.transform_panel import TransformPanel, create_transform_panel

__all__ = [
    # Panels
    "AlignmentPanel",
    "ChartConfigPanel",
    "DataPreview",
    "ExportPanel",
    "FileSelector",
    "FilterPanel",
    "PlotPreview",
    "SeriesConfigPanel",
    "TransformPanel",
    # Factory functions
    "create_alignment_panel",
    "create_chart_config",
    "create_data_preview",
    "create_data_tab",
    "create_export_panel",
    "create_export_tab",
    "create_file_selector",
    "create_filter_panel",
    "create_plot_preview",
    "create_series_config",
    "create_series_tab",
    "create_settings_tab",
    "create_transform_panel",
]
