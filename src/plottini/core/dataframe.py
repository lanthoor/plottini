"""DataFrame module for storing and manipulating parsed data.

This module provides a simple DataFrame-like structure for storing
columnar numeric data from TSV files.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass
class Column:
    """A single column of numeric data.

    Attributes:
        name: Column name (from header or "Column N" for headerless files)
        index: 0-based column index in the original file
        data: Numpy array of float64 values
        is_derived: Whether this column was computed from an expression
    """

    name: str
    index: int
    data: NDArray[np.float64]
    is_derived: bool = False

    def __len__(self) -> int:
        """Return the number of rows in this column."""
        return len(self.data)


@dataclass
class DataFrame:
    """Container for columnar numeric data from a TSV file.

    Provides dict-like access to columns by name and maintains
    column ordering for consistent iteration.

    Attributes:
        columns: Dictionary mapping column names to Column objects
        source_file: Path to the original TSV file
        row_count: Number of data rows
    """

    columns: dict[str, Column]
    source_file: Path
    row_count: int
    _column_order: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize column order if not provided."""
        if not self._column_order and self.columns:
            # Sort by column index to maintain original order
            self._column_order = sorted(
                self.columns.keys(), key=lambda name: self.columns[name].index
            )

    def get_column_names(self) -> list[str]:
        """Return ordered list of column names.

        Returns:
            List of column names in their original order.
        """
        return list(self._column_order)

    def get_column(self, name: str) -> Column:
        """Retrieve a column by name.

        Args:
            name: Column name to retrieve.

        Returns:
            The Column object.

        Raises:
            KeyError: If column name does not exist.
        """
        if name not in self.columns:
            available = ", ".join(f"'{n}'" for n in self._column_order)
            raise KeyError(f"Column '{name}' not found. Available columns: {available}")
        return self.columns[name]

    def __getitem__(self, name: str) -> NDArray[np.float64]:
        """Get column data by name using subscript notation.

        Args:
            name: Column name to retrieve.

        Returns:
            Numpy array of column data.

        Raises:
            KeyError: If column name does not exist.
        """
        return self.get_column(name).data

    def __len__(self) -> int:
        """Return the number of rows."""
        return self.row_count

    def __iter__(self) -> Iterator[str]:
        """Iterate over column names in order."""
        return iter(self._column_order)

    def __contains__(self, name: str) -> bool:
        """Check if a column name exists."""
        return name in self.columns

    def is_empty(self) -> bool:
        """Check if the DataFrame has no data rows.

        Returns:
            True if row_count is 0, False otherwise.
        """
        return self.row_count == 0

    def add_derived_column(self, name: str, expression: str) -> None:
        """Add a column computed from an expression.

        Args:
            name: Name for the new column.
            expression: Mathematical expression to evaluate.

        Raises:
            ExpressionError: If expression is invalid or evaluation fails.
        """
        from plottini.core.transforms import evaluate_expression

        # Build columns dict for expression evaluation
        column_data = {col_name: self[col_name] for col_name in self.columns}

        # Evaluate expression
        result = evaluate_expression(expression, column_data)

        # Create new derived column
        new_column = Column(
            name=name,
            index=len(self.columns),
            data=result,
            is_derived=True,
        )

        # Add to DataFrame
        self.columns[name] = new_column
        self._column_order.append(name)

    def filter_rows(
        self,
        column: str,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> DataFrame:
        """Filter rows by value range in a column.

        Args:
            column: Column name to filter on.
            min_val: Minimum value (inclusive), or None for no lower bound.
            max_val: Maximum value (inclusive), or None for no upper bound.

        Returns:
            New DataFrame with filtered rows.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError(
            "Row filtering is not yet implemented. "
            "This feature will be available in a future release."
        )


def create_empty_dataframe(source_file: Path) -> DataFrame:
    """Create an empty DataFrame for a file with no data.

    Args:
        source_file: Path to the source file.

    Returns:
        An empty DataFrame with no columns and zero rows.
    """
    return DataFrame(
        columns={},
        source_file=source_file,
        row_count=0,
        _column_order=[],
    )


__all__ = ["Column", "DataFrame", "create_empty_dataframe"]
