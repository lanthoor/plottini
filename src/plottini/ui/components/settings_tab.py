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
    st.header("Settings")

    config = state.plot_config

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

    current_type = next((k for k, v in chart_types.items() if v == config.chart_type), "Line")
    chart_type = st.selectbox(
        "Chart Type",
        options=list(chart_types.keys()),
        index=list(chart_types.keys()).index(current_type),
    )
    if chart_types[chart_type] != config.chart_type:
        config.chart_type = chart_types[chart_type]

    # Labels section
    st.subheader("Labels")

    title = st.text_input("Title", value=config.title)
    if title != config.title:
        config.title = title

    col_x, col_y = st.columns(2)
    with col_x:
        x_label = st.text_input("X-Axis Label", value=config.x_label)
        if x_label != config.x_label:
            config.x_label = x_label

    with col_y:
        y_label = st.text_input("Y-Axis Label", value=config.y_label)
        if y_label != config.y_label:
            config.y_label = y_label

    # Secondary Y-axis label (if any series uses it)
    has_secondary = any(s.use_secondary_y for s in state.series)
    if has_secondary:
        y2_label = st.text_input("Secondary Y-Axis Label", value=config.y2_label)
        if y2_label != config.y2_label:
            config.y2_label = y2_label

    # Figure dimensions
    st.subheader("Figure Size")
    col_w, col_h = st.columns(2)
    with col_w:
        width = st.number_input(
            "Width (inches)",
            min_value=4.0,
            max_value=20.0,
            value=config.figure_width,
            step=0.5,
        )
        if width != config.figure_width:
            config.figure_width = width

    with col_h:
        height = st.number_input(
            "Height (inches)",
            min_value=3.0,
            max_value=15.0,
            value=config.figure_height,
            step=0.5,
        )
        if height != config.figure_height:
            config.figure_height = height

    # Display options
    st.subheader("Display Options")
    col_grid, col_legend = st.columns(2)
    with col_grid:
        show_grid = st.checkbox("Show Grid", value=config.show_grid)
        if show_grid != config.show_grid:
            config.show_grid = show_grid

    with col_legend:
        show_legend = st.checkbox("Show Legend", value=config.show_legend)
        if show_legend != config.show_legend:
            config.show_legend = show_legend

    # Chart-type specific options
    _render_chart_specific_options(config)


def _render_chart_specific_options(config: PlotConfig) -> None:
    """Render options specific to the selected chart type."""
    if config.chart_type == ChartType.BAR or config.chart_type == ChartType.BAR_HORIZONTAL:
        st.subheader("Bar Chart Options")
        bar_width = st.slider(
            "Bar Width",
            min_value=0.1,
            max_value=1.0,
            value=config.bar_width,
            step=0.1,
        )
        if bar_width != config.bar_width:
            config.bar_width = bar_width

    elif config.chart_type == ChartType.HISTOGRAM:
        st.subheader("Histogram Options")
        col1, col2 = st.columns(2)
        with col1:
            bins = st.number_input(
                "Number of Bins",
                min_value=5,
                max_value=100,
                value=config.histogram_bins,
                step=5,
            )
            if bins != config.histogram_bins:
                config.histogram_bins = bins
        with col2:
            density = st.checkbox("Show Density", value=config.histogram_density)
            if density != config.histogram_density:
                config.histogram_density = density

    elif config.chart_type == ChartType.SCATTER:
        st.subheader("Scatter Plot Options")
        scatter_size = st.slider(
            "Marker Size",
            min_value=10,
            max_value=200,
            value=config.scatter_size,
            step=10,
        )
        if scatter_size != config.scatter_size:
            config.scatter_size = scatter_size

    elif config.chart_type == ChartType.AREA:
        st.subheader("Area Chart Options")
        alpha = st.slider(
            "Fill Transparency",
            min_value=0.1,
            max_value=1.0,
            value=config.area_alpha,
            step=0.1,
        )
        if alpha != config.area_alpha:
            config.area_alpha = alpha

    elif config.chart_type == ChartType.PIE:
        st.subheader("Pie Chart Options")
        col1, col2 = st.columns(2)
        with col1:
            explode = st.slider(
                "Explode Factor",
                min_value=0.0,
                max_value=0.5,
                value=config.pie_explode,
                step=0.05,
            )
            if explode != config.pie_explode:
                config.pie_explode = explode
        with col2:
            show_labels = st.checkbox("Show Labels", value=config.pie_show_labels)
            if show_labels != config.pie_show_labels:
                config.pie_show_labels = show_labels

    elif config.chart_type == ChartType.BOX:
        st.subheader("Box Plot Options")
        show_outliers = st.checkbox("Show Outliers", value=config.box_show_outliers)
        if show_outliers != config.box_show_outliers:
            config.box_show_outliers = show_outliers

    elif config.chart_type == ChartType.VIOLIN:
        st.subheader("Violin Plot Options")
        show_median = st.checkbox("Show Median Line", value=config.violin_show_median)
        if show_median != config.violin_show_median:
            config.violin_show_median = show_median

    elif config.chart_type == ChartType.STEP:
        st.subheader("Step Chart Options")
        step_options = ["pre", "mid", "post"]
        step_where = st.selectbox(
            "Step Position",
            options=step_options,
            index=step_options.index(config.step_where) if config.step_where in step_options else 1,
        )
        if step_where != config.step_where:
            config.step_where = step_where


__all__ = ["render_settings_tab"]
