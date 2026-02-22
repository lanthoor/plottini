"""Main Streamlit application for Plottini.

This module provides the main entry point for the Streamlit-based
graph builder UI with a UI5-style icon tab bar navigation.
"""

from __future__ import annotations

import streamlit as st

from plottini.ui.components import (
    generate_figure,
    render_data_tab,
    render_export_tab,
    render_preview_column,
    render_series_tab,
    render_settings_tab,
    render_transform_tab,
)
from plottini.ui.state import get_state


def inject_custom_css() -> None:
    """Inject custom CSS for UI5-style icon tab bar."""
    st.markdown(
        """
        <style>
        /* Hide default Streamlit elements */
        #MainMenu, footer, header[data-testid="stHeader"] {
            display: none;
        }

        /* Main content padding - reset all Streamlit wrapper padding */
        .main .block-container,
        div[data-testid="stMainBlockContainer"] {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 100%;
        }

        /* Reset padding on main vertical content blocks */
        .main .block-container > div[data-testid="stVerticalBlock"] {
            padding-top: 0 !important;
        }

        /* Restore specific padding where needed */
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1.5rem !important;
        }

        /* Hide sidebar completely */
        section[data-testid="stSidebar"] {
            display: none;
        }

        /* Streamlit tabs - UI5 style */
        .stTabs [data-baseweb="tab-list"] {
            background: #fff;
            border-bottom: 1px solid #e5e5e5;
            gap: 0;
            padding: 0;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 12px 24px;
            font-weight: 500;
            color: #666;
            border-radius: 0;
            border-bottom: 3px solid transparent;
            background: transparent;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: #f5f5f5;
            color: #0854a0;
        }

        .stTabs [aria-selected="true"] {
            color: #0854a0 !important;
            border-bottom-color: #0854a0 !important;
            background: transparent !important;
        }

        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #0854a0 !important;
        }

        .stTabs [data-baseweb="tab-border"] {
            display: none;
        }

        /* Tab panel padding */
        .stTabs [data-baseweb="tab-panel"] {
            padding: 1rem 0;
        }

        /* Legend position radio button grid - uses horizontal layout */
        div[data-testid="stRadio"]:has(input[aria-label^="↖"]) > div[role="radiogroup"],
        div[data-testid="stRadio"]:has(input[aria-label^="↑"]) > div[role="radiogroup"] {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main entry point for the Streamlit app."""
    # Page config
    st.set_page_config(
        page_title="Plottini",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Inject custom CSS
    inject_custom_css()

    # App title
    st.title("📊 Plottini")

    # Get or create app state
    state = get_state()

    # Store generate_figure in session state for on-demand generation by export tab
    if "regenerate_figure" not in st.session_state:
        st.session_state.regenerate_figure = lambda: generate_figure(state)

    # Main content with tabs
    col_main, col_preview = st.columns([7, 3])

    with col_main:
        # Actions row
        if state.has_data():
            _, col_btn = st.columns([8, 2])
            with col_btn:
                if st.button("Clear All", type="secondary", use_container_width=True):
                    state.clear_data()
                    st.rerun()

        # UI5-style tabs
        tab_data, tab_transform, tab_series, tab_settings, tab_export = st.tabs(
            ["📁 Data", "🔧 Transform", "📈 Series", "⚙️ Settings", "📥 Export"]
        )

        with tab_data:
            render_data_tab(state)

        with tab_transform:
            render_transform_tab(state)

        with tab_series:
            render_series_tab(state)

        with tab_settings:
            render_settings_tab(state)

        with tab_export:
            render_export_tab(state)

    with col_preview:
        render_preview_column(state)

    # Show errors
    if state.error_message:
        st.error(state.error_message)
        if st.button("Dismiss"):
            state.clear_error()
            st.rerun()


def start_app() -> None:
    """Start the Streamlit application."""
    main()


if __name__ == "__main__":
    main()


__all__ = ["main", "start_app"]
