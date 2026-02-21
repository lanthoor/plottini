"""Data tab component for Streamlit UI.

This component handles:
- File upload (multiple TSV files)
- Parser configuration (delimiter, headers, comments)
- Data preview for each file/block
- File deletion with confirmation
- Alignment configuration for multi-file
"""

from __future__ import annotations

import streamlit as st

from plottini.core.parser import ParserConfig, TSVParser
from plottini.ui.state import AppState, DataSource, UploadedFile


def render_data_tab(state: AppState) -> None:
    """Render the Data tab content.

    Args:
        state: Application state
    """
    # Parser configuration (shown first, not collapsible)
    _render_parser_config(state)

    st.divider()

    # File upload section
    _render_file_upload(state)

    # Show loaded files
    if state.uploaded_files:
        _render_loaded_files(state)

    # Alignment configuration (only show if multiple data sources)
    if len(state.data_sources) > 1:
        with st.expander("Alignment", expanded=False):
            _render_alignment_config(state)


def _render_file_upload(state: AppState) -> None:
    """Render file upload widget."""
    uploaded_files = st.file_uploader(
        "Upload TSV files",
        type=["tsv", "txt", "dat"],
        accept_multiple_files=True,
        help="Upload one or more tab-separated value files",
        key="file_uploader",
    )

    if uploaded_files:
        # Process newly uploaded files
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in state.uploaded_files:
                _process_uploaded_file(state, uploaded_file)


def _process_uploaded_file(state: AppState, uploaded_file) -> None:
    """Process a newly uploaded file.

    Args:
        state: Application state
        uploaded_file: Streamlit UploadedFile object
    """
    try:
        # Read file content (seek to beginning first in case file was already read)
        uploaded_file.seek(0)
        content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset for potential re-read

        # Store in state
        uf = UploadedFile(name=uploaded_file.name, content=content)
        state.uploaded_files[uploaded_file.name] = uf

        # Parse the file
        parser = TSVParser(state.parser_config)
        blocks = parser.parse_blocks(uf.get_file_object(), source_name=uploaded_file.name)

        # Add data sources for each block
        for i, df in enumerate(blocks):
            if len(blocks) == 1:
                ds = DataSource(file_name=uploaded_file.name, block_index=None)
            else:
                ds = DataSource(file_name=uploaded_file.name, block_index=i)

            state.data_sources.append(ds)
            state.parsed_data[ds] = df

        st.success(f"Loaded {uploaded_file.name}")
        st.rerun()

    except Exception as e:
        st.error(f"Error loading {uploaded_file.name}: {e}")


def _render_parser_config(state: AppState) -> None:
    """Render parser configuration widgets."""
    col1, col2 = st.columns(2)

    with col1:
        delimiter_options = {
            "Tab": "\t",
            "Space": " ",
            "Comma": ",",
            "Semicolon": ";",
        }
        current_delim = next(
            (k for k, v in delimiter_options.items() if v == state.parser_config.delimiter),
            "Tab",
        )
        delimiter = st.selectbox(
            "Delimiter",
            options=list(delimiter_options.keys()),
            index=list(delimiter_options.keys()).index(current_delim),
            help="Character used to separate columns",
        )

        has_header = st.checkbox(
            "Has Header Row",
            value=state.parser_config.has_header,
            help="First row contains column names",
        )

    with col2:
        comment_char = st.text_input(
            "Comment Character",
            value=state.parser_config.comment_chars[0]
            if state.parser_config.comment_chars
            else "#",
            max_chars=1,
            help="Lines starting with this character are ignored",
        )

        encoding = st.selectbox(
            "File Encoding",
            options=["utf-8", "latin-1", "ascii"],
            index=0 if state.parser_config.encoding == "utf-8" else 1,
        )

    # Auto-apply parser settings when changed
    new_config = ParserConfig(
        has_header=has_header,
        comment_chars=[comment_char] if comment_char else ["#"],
        delimiter=delimiter_options[delimiter],
        encoding=encoding,
    )

    if new_config != state.parser_config:
        state.parser_config = new_config
        _reparse_all_files(state)
        st.rerun()


def _reparse_all_files(state: AppState) -> None:
    """Re-parse all uploaded files with current parser config.

    Preserves series configurations by matching on (file_name, block_index).
    """
    # Store old data sources to preserve series mappings
    old_data_sources = list(state.data_sources)

    # Clear parsed data but keep uploaded files
    state.data_sources.clear()
    state.parsed_data.clear()

    parser = TSVParser(state.parser_config)

    for file_name, uf in state.uploaded_files.items():
        try:
            blocks = parser.parse_blocks(uf.get_file_object(), source_name=file_name)

            for i, df in enumerate(blocks):
                if len(blocks) == 1:
                    ds = DataSource(file_name=file_name, block_index=None)
                else:
                    ds = DataSource(file_name=file_name, block_index=i)

                state.data_sources.append(ds)
                state.parsed_data[ds] = df

        except Exception as e:
            st.error(f"Error re-parsing {file_name}: {e}")

    # Update series source_file_index to match new data_sources order
    for series in state.series:
        if series.source_file_index < len(old_data_sources):
            old_ds = old_data_sources[series.source_file_index]
            # Try to find matching data source in new list
            for new_idx, new_ds in enumerate(state.data_sources):
                if new_ds == old_ds:
                    series.source_file_index = new_idx
                    break


def _render_loaded_files(state: AppState) -> None:
    """Render list of loaded files with preview and delete options."""
    for file_name in list(state.uploaded_files.keys()):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                info = state.get_file_info(file_name)
                st.write(f"**{file_name}** {info}")

            with col2:
                # Show preview button
                if st.button("Preview", key=f"preview_{file_name}"):
                    st.session_state[f"show_preview_{file_name}"] = not st.session_state.get(
                        f"show_preview_{file_name}", False
                    )

            with col3:
                # Delete button with confirmation
                if st.button("Delete", key=f"delete_{file_name}", type="secondary"):
                    st.session_state[f"confirm_delete_{file_name}"] = True

            # Show confirmation dialog
            if st.session_state.get(f"confirm_delete_{file_name}", False):
                # Count affected series
                affected_count = sum(
                    1
                    for s in state.series
                    if s.source_file_index < len(state.data_sources)
                    and state.data_sources[s.source_file_index].file_name == file_name
                )

                st.warning(
                    f"Deleting '{file_name}' will also remove {affected_count} series. Continue?"
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, delete", key=f"confirm_yes_{file_name}"):
                        state.remove_file(file_name)
                        st.session_state[f"confirm_delete_{file_name}"] = False
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key=f"confirm_no_{file_name}"):
                        st.session_state[f"confirm_delete_{file_name}"] = False
                        st.rerun()

            # Show data preview if toggled
            if st.session_state.get(f"show_preview_{file_name}", False):
                _render_file_preview(state, file_name)

            st.divider()


def _render_file_preview(state: AppState, file_name: str) -> None:
    """Render data preview for a file."""
    # Get all data sources for this file
    sources = [ds for ds in state.data_sources if ds.file_name == file_name]

    for ds in sources:
        if ds in state.parsed_data:
            df = state.parsed_data[ds]
            block_label = f" (Block {ds.block_index + 1})" if ds.block_index is not None else ""

            st.caption(f"{file_name}{block_label} - {df.row_count} rows")

            # Convert to pandas for display (limited rows)
            import pandas as pd

            preview_data = {}
            for col_name in df.get_column_names():
                col = df.get_column(col_name)
                preview_data[col_name] = col.data[:10]  # First 10 rows

            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, width="stretch", hide_index=True)


def _render_alignment_config(state: AppState) -> None:
    """Render alignment configuration for multi-file data."""
    from plottini.config.schema import AlignmentConfig

    st.caption("Align data from multiple files on a common column")

    enabled = st.checkbox(
        "Enable Alignment",
        value=state.alignment.enabled if state.alignment else False,
    )

    if enabled:
        # Get common columns across all data sources
        common_columns = state.get_all_column_names()

        if common_columns:
            current_col = state.alignment.column if state.alignment else common_columns[0]
            column = st.selectbox(
                "Alignment Column",
                options=common_columns,
                index=common_columns.index(current_col) if current_col in common_columns else 0,
            )

            # Auto-apply alignment when changed
            new_alignment = AlignmentConfig(enabled=True, column=column)
            if state.alignment != new_alignment:
                state.alignment = new_alignment
        else:
            st.warning("No common columns found across data sources")
    else:
        if state.alignment and state.alignment.enabled:
            state.alignment = AlignmentConfig(enabled=False)


__all__ = ["render_data_tab"]
