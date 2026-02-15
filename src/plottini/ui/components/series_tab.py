"""Series tab component for Streamlit UI.

This component handles:
- Series list with configuration
- Add/remove series
- Column selection (X, Y)
- Series appearance (color, line style, marker)
- Source data selection
- Secondary Y-axis toggle
"""

from __future__ import annotations

import streamlit as st

from plottini.core.plotter import COLORBLIND_PALETTE, SeriesConfig
from plottini.ui.state import AppState


def render_series_tab(state: AppState) -> None:
    """Render the Series tab content.

    Args:
        state: Application state
    """
    st.header("Series")

    if not state.has_data():
        st.info("Upload data files in the Data tab first.")
        return

    # Add series button
    if st.button("Add Series", type="primary"):
        _add_new_series(state)
        st.rerun()

    # Show existing series
    if state.series:
        for i, series in enumerate(state.series):
            _render_series_config(state, i, series)
    else:
        st.info("No series configured. Click 'Add Series' to create one.")


def _add_new_series(state: AppState) -> None:
    """Add a new series with default configuration."""
    # Get default columns from first available data source
    columns = state.get_all_column_names()
    x_col = columns[0] if columns else "x"
    y_col = columns[1] if len(columns) > 1 else columns[0] if columns else "y"

    # Pick next color from palette
    color_idx = len(state.series) % len(COLORBLIND_PALETTE)
    color = COLORBLIND_PALETTE[color_idx]

    series = SeriesConfig(
        x_column=x_col,
        y_column=y_col,
        label=f"Series {len(state.series) + 1}",
        color=color,
        source_file_index=0,
    )
    state.series.append(series)


def _render_series_config(state: AppState, index: int, series: SeriesConfig) -> None:
    """Render configuration for a single series.

    Args:
        state: Application state
        index: Index of series in state.series
        series: Series configuration
    """
    with st.expander(f"Series {index + 1}: {series.label or 'Untitled'}", expanded=index == 0):
        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("Remove", key=f"remove_series_{index}", type="secondary"):
                state.series.pop(index)
                st.rerun()

        # Get available columns
        columns = state.get_all_column_names()
        if not columns:
            st.warning("No columns available")
            return

        # Data source selection
        data_source_options = [ds.display_name for ds in state.data_sources]
        if data_source_options:
            current_source_idx = min(series.source_file_index, len(data_source_options) - 1)
            source_idx = st.selectbox(
                "Data Source",
                options=range(len(data_source_options)),
                format_func=lambda x: data_source_options[x],
                index=current_source_idx,
                key=f"source_{index}",
            )
            if source_idx != series.source_file_index:
                series.source_file_index = source_idx

        # Column selection
        col_x, col_y = st.columns(2)

        with col_x:
            x_idx = columns.index(series.x_column) if series.x_column in columns else 0
            x_column = st.selectbox(
                "X Column",
                options=columns,
                index=x_idx,
                key=f"x_col_{index}",
            )
            if x_column != series.x_column:
                series.x_column = x_column

        with col_y:
            y_idx = columns.index(series.y_column) if series.y_column in columns else 0
            y_column = st.selectbox(
                "Y Column",
                options=columns,
                index=y_idx,
                key=f"y_col_{index}",
            )
            if y_column != series.y_column:
                series.y_column = y_column

        # Series label
        label = st.text_input(
            "Label",
            value=series.label or "",
            key=f"label_{index}",
            help="Legend label for this series",
        )
        if label != series.label:
            series.label = label if label else None

        # Appearance settings
        st.subheader("Appearance")

        col_color, col_style, col_marker = st.columns(3)

        with col_color:
            color = st.color_picker(
                "Color",
                value=series.color or COLORBLIND_PALETTE[index % len(COLORBLIND_PALETTE)],
                key=f"color_{index}",
            )
            if color != series.color:
                series.color = color

        with col_style:
            line_styles = {
                "Solid": "-",
                "Dashed": "--",
                "Dash-dot": "-.",
                "Dotted": ":",
            }
            current_style = next(
                (k for k, v in line_styles.items() if v == series.line_style), "Solid"
            )
            line_style = st.selectbox(
                "Line Style",
                options=list(line_styles.keys()),
                index=list(line_styles.keys()).index(current_style),
                key=f"line_style_{index}",
            )
            if line_styles[line_style] != series.line_style:
                series.line_style = line_styles[line_style]

        with col_marker:
            markers = {
                "None": None,
                "Circle": "o",
                "Square": "s",
                "Triangle": "^",
                "Diamond": "D",
                "Plus": "+",
                "X": "x",
            }
            current_marker = next((k for k, v in markers.items() if v == series.marker), "None")
            marker = st.selectbox(
                "Marker",
                options=list(markers.keys()),
                index=list(markers.keys()).index(current_marker),
                key=f"marker_{index}",
            )
            if markers[marker] != series.marker:
                series.marker = markers[marker]

        # Line width
        line_width = st.slider(
            "Line Width",
            min_value=0.5,
            max_value=5.0,
            value=series.line_width,
            step=0.5,
            key=f"line_width_{index}",
        )
        if line_width != series.line_width:
            series.line_width = line_width

        # Secondary Y-axis
        use_secondary = st.checkbox(
            "Use Secondary Y-Axis",
            value=series.use_secondary_y,
            key=f"secondary_y_{index}",
            help="Plot this series on the right y-axis",
        )
        if use_secondary != series.use_secondary_y:
            series.use_secondary_y = use_secondary


__all__ = ["render_series_tab"]
