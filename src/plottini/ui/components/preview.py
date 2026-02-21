"""Preview component for Streamlit UI.

This component handles:
- Chart preview rendering
- Auto-update on state changes
- Preview in collapsible expander
"""

from __future__ import annotations

import streamlit as st

from plottini.core.plotter import Plotter
from plottini.ui.state import AppState


def render_preview(state: AppState) -> None:
    """Render the chart preview in an expander.

    Args:
        state: Application state
    """
    with st.expander("Preview", expanded=True):
        if not state.can_render():
            st.info("Upload data and configure series to see preview.")
            return

        try:
            # Generate the plot
            _generate_preview(state)

            # Display the figure
            if state.current_figure is not None:
                st.pyplot(state.current_figure, width="stretch")
            else:
                st.warning("Unable to generate preview.")

        except Exception as e:
            st.error(f"Preview error: {e}")


def _generate_preview(state: AppState) -> None:
    """Generate the preview figure.

    Args:
        state: Application state
    """
    # Get dataframes in order
    dataframes = state.get_dataframes_list()

    if not dataframes:
        return

    # Create plotter
    plotter = Plotter(state.plot_config)

    # Create figure
    fig = plotter.create_figure(dataframes, state.series)

    # Store for export
    state.current_figure = fig


def render_preview_column(state: AppState) -> None:
    """Render preview in right column layout.

    This function is called when using the 70/30 split layout.

    Args:
        state: Application state
    """
    st.subheader("Preview")

    if not state.can_render():
        st.info("Upload data and configure at least one series.")
        return

    try:
        _generate_preview(state)

        if state.current_figure is not None:
            st.pyplot(state.current_figure, width="stretch")

            # Show figure info
            with st.expander("Figure Info", expanded=False):
                st.caption(
                    f'Size: {state.plot_config.figure_width}" x {state.plot_config.figure_height}"'
                )
                st.caption(f"Chart Type: {state.plot_config.chart_type.value}")
                st.caption(f"Series: {len(state.series)}")
        else:
            st.warning("Unable to generate preview.")

    except Exception as e:
        st.error(f"Preview error: {e}")
        import traceback

        with st.expander("Error Details"):
            st.code(traceback.format_exc())


__all__ = ["render_preview", "render_preview_column"]
