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


def render_export_tab(state: AppState) -> None:
    """Render the Export tab content.

    Args:
        state: Application state
    """
    st.header("Export")

    if not state.can_render():
        st.info("Configure data and series first to enable export.")
        return

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
            min_value=72,
            max_value=600,
            value=300,
            step=72,
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

    if st.button("Generate Export", type="primary"):
        _generate_export(state, export_format.lower(), dpi, full_filename)


def _generate_export(state: AppState, format_str: str, dpi: int, filename: str) -> None:
    """Generate and offer the plot export for download.

    Args:
        state: Application state
        format_str: Export format (png, svg, pdf, eps)
        dpi: Resolution in DPI
        filename: Output filename
    """
    if state.current_figure is None:
        st.error("No figure to export. Please ensure the preview is generated.")
        return

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

        # Determine MIME type
        mime_types = {
            "png": "image/png",
            "svg": "image/svg+xml",
            "pdf": "application/pdf",
            "eps": "application/postscript",
        }
        mime_type = mime_types.get(format_str, "application/octet-stream")

        # Offer download
        st.download_button(
            label=f"Download {filename}",
            data=buffer,
            file_name=filename,
            mime=mime_type,
        )

        st.success("Export ready! Click above to download.")

    except Exception as e:
        st.error(f"Export failed: {e}")


def render_config_export(state: AppState) -> None:
    """Render configuration save/load section.

    Args:
        state: Application state
    """
    st.subheader("Configuration")

    col_save, col_load = st.columns(2)

    with col_save:
        st.caption("Save current configuration")
        config_name = st.text_input(
            "Config Name",
            value="plot_config",
            key="config_save_name",
        )
        if st.button("Save Config"):
            _save_config(state, config_name)

    with col_load:
        st.caption("Load configuration file")
        uploaded_config = st.file_uploader(
            "Upload Config",
            type=["toml"],
            key="config_upload",
        )
        if uploaded_config:
            _load_config(state, uploaded_config)


def _save_config(state: AppState, name: str) -> None:
    """Save current configuration to downloadable TOML file."""
    # Configuration save/load is a future feature
    st.info("Configuration save functionality coming soon.")


def _load_config(state: AppState, uploaded_file) -> None:
    """Load configuration from uploaded TOML file."""
    # Configuration save/load is a future feature
    st.info("Configuration load functionality coming soon.")


__all__ = ["render_export_tab", "render_config_export"]
