"""Export tab component for Streamlit UI.

This component handles:
- Export format selection (PNG, SVG, PDF, EPS)
- DPI/resolution settings
- Filename input
- Export button and download
"""

from __future__ import annotations

from io import BytesIO

import streamlit as st

from plottini.ui.state import AppState


def _ensure_figure(state: AppState) -> None:
    """Ensure figure is generated if possible."""
    if state.current_figure is None and state.can_render():
        # Generate figure on-demand
        if "regenerate_figure" in st.session_state:
            st.session_state.regenerate_figure()


def render_export_tab(state: AppState) -> None:
    """Render the Export tab content.

    Export data is generated when the tab renders (not on every app rerun),
    since Streamlit tabs only render their content when active.

    Args:
        state: Application state
    """
    if not state.can_render():
        st.info("Configure data and series first to enable export.")
        return

    # Ensure figure exists before rendering export options
    _ensure_figure(state)

    # Export format
    format_options = ["PNG", "SVG", "PDF", "EPS"]
    export_format = st.selectbox(
        "Export Format",
        options=format_options,
        index=0,
        help="PNG for web, SVG for scalable graphics, PDF/EPS for publications",
    )

    # Resolution (only for raster formats)
    if export_format == "PNG":
        dpi = st.slider(
            "Resolution (DPI)",
            min_value=50,
            max_value=600,
            value=300,
            step=10,
            help="300 DPI recommended for print, 150 for web",
        )
    else:
        dpi = 300  # Default for vector formats (affects rasterized elements)

    # Filename
    default_name = "plot"
    filename = st.text_input(
        "Filename",
        value=default_name,
        help="Filename without extension",
    )

    # Clean filename
    filename = filename.strip()
    if not filename:
        filename = default_name

    # Full filename with extension
    full_filename = f"{filename}.{export_format.lower()}"

    st.caption(f"Will save as: **{full_filename}**")

    # Export button
    st.divider()

    # Check if figure is available
    if state.current_figure is None:
        st.warning("No figure available. Configure data and series first.")
        return

    # Generate export data for download button
    export_data = _generate_export_data(state, export_format.lower(), dpi)
    if export_data is not None:
        mime_types = {
            "png": "image/png",
            "svg": "image/svg+xml",
            "pdf": "application/pdf",
            "eps": "application/postscript",
        }
        mime_type = mime_types.get(export_format.lower(), "application/octet-stream")

        st.download_button(
            label=f"Download {full_filename}",
            data=export_data,
            file_name=full_filename,
            mime=mime_type,
            type="primary",
        )


def _generate_export_data(state: AppState, format_str: str, dpi: int) -> BytesIO | None:
    """Generate the plot export data.

    Args:
        state: Application state
        format_str: Export format (png, svg, pdf, eps)
        dpi: Resolution in DPI

    Returns:
        Export data as BytesIO buffer, or None if export fails
    """
    if state.current_figure is None:
        return None

    try:
        # Export to buffer directly using matplotlib
        buffer = BytesIO()
        state.current_figure.savefig(
            buffer,
            format=format_str,
            dpi=dpi,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buffer.seek(0)
        return buffer

    except Exception as e:
        st.error(f"Export failed: {e}")
        return None


__all__ = ["render_export_tab"]
