"""Transform tab component for Streamlit UI.

This component handles:
- Derived columns creation from mathematical expressions
- List of existing derived columns with delete option
- Help text for available functions and operators
"""

from __future__ import annotations

import streamlit as st

from plottini.core.transforms import ALLOWED_FUNCTIONS
from plottini.ui.state import AppState, DataSource
from plottini.utils.errors import ExpressionError


def render_transform_tab(state: AppState) -> None:
    """Render the Transform tab content.

    Args:
        state: Application state
    """
    if not state.has_data():
        st.info("Upload data files in the Data tab first.")
        return

    # Derived columns section
    st.subheader("Derived Columns")
    st.caption("Create new columns computed from mathematical expressions.")

    # Show existing derived columns
    _render_derived_columns_list(state)

    st.divider()

    # Add derived column form
    _render_add_derived_column_form(state)

    # Help section
    with st.expander("Expression Help", expanded=False):
        _render_expression_help()


def _render_derived_columns_list(state: AppState) -> None:
    """Render list of existing derived columns with delete option.

    Args:
        state: Application state
    """
    # Find all derived columns across all data sources
    derived_columns: list[tuple[DataSource, str]] = []
    for ds in state.data_sources:
        if ds in state.parsed_data:
            df = state.parsed_data[ds]
            for col_name in df.get_column_names():
                col = df.get_column(col_name)
                if col.is_derived:
                    derived_columns.append((ds, col_name))

    if not derived_columns:
        st.info("No derived columns yet. Use the form below to create one.")
        return

    st.write(f"**{len(derived_columns)} derived column(s):**")

    for ds, col_name in derived_columns:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"• **{col_name}** ({ds.display_name})")

        with col2:
            # Create a unique key for the delete button
            key = f"delete_derived_{ds.file_name}_{ds.block_index}_{col_name}"
            if st.button("Delete", key=key, type="secondary"):
                _delete_derived_column(state, ds, col_name)
                st.rerun()


def _delete_derived_column(state: AppState, ds: DataSource, col_name: str) -> None:
    """Delete a derived column from a data source.

    Args:
        state: Application state
        ds: Data source containing the column
        col_name: Name of the derived column to delete
    """
    if ds not in state.parsed_data:
        return

    df = state.parsed_data[ds]
    if col_name in df.columns:
        df.remove_column(col_name)

    # NOTE: We intentionally do not modify state.derived_columns here.
    # DerivedColumnConfig does not track which data source a derived column
    # belongs to, so removing entries by name alone could accidentally delete
    # configurations for the same-named column in other data sources.

    # Invalidate current figure
    state.current_figure = None


def _render_add_derived_column_form(state: AppState) -> None:
    """Render form to add a new derived column.

    Args:
        state: Application state
    """
    st.subheader("Add Derived Column")

    # Data source selector
    data_source_options = [ds.display_name for ds in state.data_sources]
    if not data_source_options:
        st.warning("No data sources available")
        return

    source_idx = st.selectbox(
        "Data Source",
        options=range(len(data_source_options)),
        format_func=lambda x: data_source_options[x],
        index=0,
        key="derived_source",
        help="Select which data source to add the column to",
    )

    ds = state.data_sources[source_idx]
    df = state.parsed_data.get(ds)

    if df is None:
        st.error("Selected data source has no data")
        return

    # Show available columns for this data source
    available_cols = [name for name in df.get_column_names() if not df.get_column(name).is_derived]
    st.caption(f"Available columns: {', '.join(available_cols)}")

    # Column name input
    col_name = st.text_input(
        "Column Name",
        key="derived_col_name",
        help="Name for the new derived column",
        placeholder="e.g., velocity",
    )

    # Expression input
    expression = st.text_input(
        "Expression",
        key="derived_expression",
        help="Mathematical expression using column names and functions",
        placeholder="e.g., distance / time",
    )

    # Add button
    if st.button("Add Column", type="primary", key="add_derived_btn"):
        if not col_name:
            st.error("Please enter a column name")
        elif not expression:
            st.error("Please enter an expression")
        elif col_name in df.columns:
            st.error(f"Column '{col_name}' already exists in this data source")
        else:
            _add_derived_column(state, ds, col_name, expression)


def _add_derived_column(
    state: AppState,
    ds: DataSource,
    col_name: str,
    expression: str,
) -> None:
    """Add a derived column to a data source.

    Args:
        state: Application state
        ds: Data source to add the column to
        col_name: Name for the new column
        expression: Mathematical expression to evaluate
    """
    if ds not in state.parsed_data:
        st.error("Data source not found")
        return

    df = state.parsed_data[ds]

    try:
        df.add_derived_column(col_name, expression)
        st.success(f"Added derived column '{col_name}'")
        # Invalidate current figure
        state.current_figure = None
        st.rerun()
    except ExpressionError as e:
        st.error(f"Expression error: {e.message}")
        if e.detail:
            st.caption(e.detail)
    except Exception as e:
        st.error(f"Error adding column: {e}")


def _render_expression_help() -> None:
    """Render help text for expressions."""
    st.markdown("**Available Functions:**")
    func_list = ", ".join(f"`{name}`" for name in sorted(ALLOWED_FUNCTIONS.keys()))
    st.write(func_list)

    st.markdown("**Available Operators:**")
    st.write("`+` (add), `-` (subtract), `*` (multiply), `/` (divide), `**` (power), `%` (modulo)")

    st.markdown("**Examples:**")
    st.code(
        """# Basic arithmetic (with named columns)
velocity = distance / time
kinetic_energy = 0.5 * mass * velocity ** 2

# Using functions
log_value = log10(concentration)
magnitude = sqrt(x**2 + y**2)
phase = sin(2 * angle)

# Headerless files (auto-generated Column 1, Column 2, etc.)
ratio = "Column 1" / "Column 2"
normalized = "Column 3" / 100

# Column names with spaces (use quotes)
total = "Flow Rate" * "Time Elapsed"
log_conc = log10("Sample Concentration")""",
        language="python",
    )

    st.markdown("**Notes:**")
    st.write("• Column names are case-sensitive")
    st.write("• For simple names (no spaces): use directly, e.g., `distance / time`")
    st.write('• For names with spaces or auto-generated names: use quotes, e.g., `"Column 1" * 2`')
    st.write("• Numeric constants can be used in expressions")


__all__ = ["render_transform_tab"]
