"""Settings tab component for Streamlit UI.

This component handles:
- Chart type selection
- Plot labels (title, x-axis, y-axis)
- Figure dimensions
- Grid and legend toggles
- Chart-type specific options
"""

from __future__ import annotations

import streamlit as st

from plottini.core.plotter import ChartType, PlotConfig
from plottini.ui.state import AppState


def render_settings_tab(state: AppState) -> None:
    """Render the Settings tab content.

    Args:
        state: Application state
    """
    config = state.plot_config

    # Initialize session state with current config values if not set
    _init_settings_state(config)

    # Chart type selection
    chart_types = {
        "Line": ChartType.LINE,
        "Bar": ChartType.BAR,
        "Scatter": ChartType.SCATTER,
        "Area": ChartType.AREA,
        "Step": ChartType.STEP,
        "Stem": ChartType.STEM,
        "Histogram": ChartType.HISTOGRAM,
        "Pie": ChartType.PIE,
        "Box": ChartType.BOX,
        "Violin": ChartType.VIOLIN,
        "Horizontal Bar": ChartType.BAR_HORIZONTAL,
        "Polar": ChartType.POLAR,
    }
    chart_type_names = list(chart_types.keys())

    chart_type = st.selectbox(
        "Chart Type",
        options=chart_type_names,
        key="settings_chart_type",
    )
    config.chart_type = chart_types[chart_type]

    # Labels section
    config.title = st.text_input("Title", key="settings_title")

    col_x, col_y = st.columns(2)
    with col_x:
        config.x_label = st.text_input("X-Axis Label", key="settings_x_label")

    with col_y:
        config.y_label = st.text_input("Y-Axis Label", key="settings_y_label")

    # Secondary Y-axis label (if any series uses it)
    has_secondary = any(s.use_secondary_y for s in state.series)
    if has_secondary:
        config.y2_label = st.text_input("Secondary Y-Axis Label", key="settings_y2_label")

    # Figure dimensions
    col_w, col_h = st.columns(2)
    with col_w:
        config.figure_width = st.number_input(
            "Width (inches)",
            min_value=4.0,
            max_value=20.0,
            step=0.5,
            key="settings_width",
        )

    with col_h:
        config.figure_height = st.number_input(
            "Height (inches)",
            min_value=3.0,
            max_value=15.0,
            step=0.5,
            key="settings_height",
        )

    # Display options
    col_grid, col_legend = st.columns(2)
    with col_grid:
        config.show_grid = st.checkbox("Show Grid", key="settings_grid")

    with col_legend:
        config.show_legend = st.checkbox("Show Legend", key="settings_legend")

    # Legend position selector (only show when legend is enabled)
    if config.show_legend:
        # "Best" checkbox
        use_best = st.checkbox(
            "Auto position (best)",
            help="Let matplotlib choose the best position",
            key="settings_legend_best",
        )
        if use_best:
            config.legend_loc = "best"

        # 3x3 grid of legend positions (disabled when "best" is checked)
        legend_options = {
            "upper left": "↖ Upper Left",
            "upper center": "↑ Upper",
            "upper right": "↗ Upper Right",
            "center left": "← Left",
            "center": "● Center",
            "center right": "→ Right",
            "lower left": "↙ Lower Left",
            "lower center": "↓ Lower",
            "lower right": "↘ Lower Right",
        }
        options_list = list(legend_options.keys())

        legend_loc = st.radio(
            "Legend Position",
            options=options_list,
            format_func=lambda x: legend_options[x],
            horizontal=True,
            key="settings_legend_position",
            disabled=use_best,
        )
        if not use_best:
            config.legend_loc = legend_loc

    # Chart-type specific options
    _render_chart_specific_options(config)


def _init_settings_state(config: PlotConfig) -> None:
    """Initialize session state for settings widgets if not already set.

    Args:
        config: Current plot configuration
    """
    # Chart type - need to convert enum to display name
    chart_type_to_name = {
        ChartType.LINE: "Line",
        ChartType.BAR: "Bar",
        ChartType.SCATTER: "Scatter",
        ChartType.AREA: "Area",
        ChartType.STEP: "Step",
        ChartType.STEM: "Stem",
        ChartType.HISTOGRAM: "Histogram",
        ChartType.PIE: "Pie",
        ChartType.BOX: "Box",
        ChartType.VIOLIN: "Violin",
        ChartType.BAR_HORIZONTAL: "Horizontal Bar",
        ChartType.POLAR: "Polar",
    }
    if "settings_chart_type" not in st.session_state:
        st.session_state["settings_chart_type"] = chart_type_to_name.get(config.chart_type, "Line")
    if "settings_title" not in st.session_state:
        st.session_state["settings_title"] = config.title
    if "settings_x_label" not in st.session_state:
        st.session_state["settings_x_label"] = config.x_label
    if "settings_y_label" not in st.session_state:
        st.session_state["settings_y_label"] = config.y_label
    if "settings_y2_label" not in st.session_state:
        st.session_state["settings_y2_label"] = config.y2_label
    if "settings_width" not in st.session_state:
        st.session_state["settings_width"] = config.figure_width
    if "settings_height" not in st.session_state:
        st.session_state["settings_height"] = config.figure_height
    if "settings_grid" not in st.session_state:
        st.session_state["settings_grid"] = config.show_grid
    if "settings_legend" not in st.session_state:
        st.session_state["settings_legend"] = config.show_legend
    if "settings_legend_best" not in st.session_state:
        st.session_state["settings_legend_best"] = config.legend_loc == "best"
    if "settings_legend_position" not in st.session_state:
        st.session_state["settings_legend_position"] = (
            config.legend_loc if config.legend_loc != "best" else "upper right"
        )
    # Chart-specific options
    if "settings_bar_width" not in st.session_state:
        st.session_state["settings_bar_width"] = config.bar_width
    if "settings_histogram_bins" not in st.session_state:
        st.session_state["settings_histogram_bins"] = config.histogram_bins
    if "settings_histogram_density" not in st.session_state:
        st.session_state["settings_histogram_density"] = config.histogram_density
    if "settings_scatter_size" not in st.session_state:
        st.session_state["settings_scatter_size"] = config.scatter_size
    if "settings_area_alpha" not in st.session_state:
        st.session_state["settings_area_alpha"] = config.area_alpha
    if "settings_pie_explode" not in st.session_state:
        st.session_state["settings_pie_explode"] = config.pie_explode
    if "settings_pie_labels" not in st.session_state:
        st.session_state["settings_pie_labels"] = config.pie_show_labels
    if "settings_box_outliers" not in st.session_state:
        st.session_state["settings_box_outliers"] = config.box_show_outliers
    if "settings_violin_median" not in st.session_state:
        st.session_state["settings_violin_median"] = config.violin_show_median
    if "settings_step_where" not in st.session_state:
        st.session_state["settings_step_where"] = config.step_where


def _render_chart_specific_options(config: PlotConfig) -> None:
    """Render options specific to the selected chart type."""
    if config.chart_type == ChartType.BAR or config.chart_type == ChartType.BAR_HORIZONTAL:
        config.bar_width = st.slider(
            "Bar Width",
            min_value=0.1,
            max_value=1.0,
            step=0.1,
            key="settings_bar_width",
        )

    elif config.chart_type == ChartType.HISTOGRAM:
        col1, col2 = st.columns(2)
        with col1:
            config.histogram_bins = st.number_input(
                "Number of Bins",
                min_value=5,
                max_value=100,
                step=5,
                key="settings_histogram_bins",
            )
        with col2:
            config.histogram_density = st.checkbox("Show Density", key="settings_histogram_density")

    elif config.chart_type == ChartType.SCATTER:
        config.scatter_size = st.slider(
            "Marker Size",
            min_value=10,
            max_value=200,
            step=10,
            key="settings_scatter_size",
        )

    elif config.chart_type == ChartType.AREA:
        config.area_alpha = st.slider(
            "Fill Transparency",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            key="settings_area_alpha",
        )

    elif config.chart_type == ChartType.PIE:
        col1, col2 = st.columns(2)
        with col1:
            config.pie_explode = st.slider(
                "Explode Factor",
                min_value=0.0,
                max_value=0.5,
                step=0.05,
                key="settings_pie_explode",
            )
        with col2:
            config.pie_show_labels = st.checkbox("Show Labels", key="settings_pie_labels")

    elif config.chart_type == ChartType.BOX:
        config.box_show_outliers = st.checkbox("Show Outliers", key="settings_box_outliers")

    elif config.chart_type == ChartType.VIOLIN:
        config.violin_show_median = st.checkbox("Show Median Line", key="settings_violin_median")

    elif config.chart_type == ChartType.STEP:
        step_options = ["pre", "mid", "post"]
        config.step_where = st.selectbox(
            "Step Position",
            options=step_options,
            key="settings_step_where",
        )


__all__ = ["render_settings_tab"]
