"""TSV Parser module for reading and validating TSV files.

This module provides functionality to parse tab-separated value files
with support for headers, comments, and scientific notation.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from plottini.core.dataframe import Column, DataFrame, create_empty_dataframe
from plottini.utils.errors import ParseError


@dataclass
class ParserConfig:
    """Configuration for TSV parsing.

    Attributes:
        has_header: Whether the first non-comment line is a header row.
        comment_chars: List of characters that start comment lines.
        delimiter: Column delimiter (default: tab).
        encoding: File encoding (default: UTF-8).
    """

    has_header: bool = True
    comment_chars: list[str] = field(default_factory=lambda: ["#"])
    delimiter: str = "\t"
    encoding: str = "utf-8"


class TSVParser:
    """Parser for tab-separated value files.

    Reads TSV files and returns DataFrame objects. Handles headers,
    comments, whitespace trimming, and validates numeric values.

    Example:
        >>> config = ParserConfig(has_header=True)
        >>> parser = TSVParser(config)
        >>> df = parser.parse(Path("data.tsv"))
        >>> print(df.get_column_names())
        ['k_point', 'Energy_eV', 'DOS']
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize parser with configuration.

        Args:
            config: Parser configuration. Uses defaults if None.
        """
        self.config = config or ParserConfig()

    def parse(self, file_path: Path | str) -> DataFrame:
        """Parse a TSV file into a DataFrame.

        Args:
            file_path: Path to the TSV file.

        Returns:
            DataFrame containing the parsed data.

        Raises:
            FileNotFoundError: If file does not exist.
            ParseError: If file contains invalid data.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        lines = self._read_lines(path)
        data_lines = self._filter_lines(lines)

        if not data_lines:
            warnings.warn(
                f"File '{path}' is empty or contains only comments",
                stacklevel=2,
            )
            return create_empty_dataframe(path)

        # Extract headers or generate column names
        if self.config.has_header:
            header_line, header_line_num = data_lines[0]
            column_names = self._parse_header(header_line)
            # Validate that header column names are unique to prevent
            # silent overwriting when constructing the DataFrame.columns dict.
            seen: set[str] = set()
            for col_idx, name in enumerate(column_names, start=1):
                if name in seen:
                    raise ParseError(
                        file_path=path,
                        line_number=header_line_num,
                        column=col_idx,
                        message=f"Duplicate column name '{name}' in header",
                        raw_value=name,
                        context_line=header_line,
                    )
                seen.add(name)
            data_lines = data_lines[1:]
        else:
            # Determine column count from first data line
            first_line, _ = data_lines[0]
            num_cols = len(first_line.split(self.config.delimiter))
            column_names = [f"Column {i + 1}" for i in range(num_cols)]

        if not data_lines:
            # File had header only, no data
            warnings.warn(
                f"File '{path}' contains only a header row with no data",
                stacklevel=2,
            )
            return create_empty_dataframe(path)

        # Parse data rows
        num_cols = len(column_names)
        data_arrays: list[list[float]] = [[] for _ in range(num_cols)]

        for line, line_num in data_lines:
            values = line.split(self.config.delimiter)
            values = [v.strip() for v in values]

            # Validate column count
            if len(values) != num_cols:
                raise ParseError(
                    file_path=path,
                    line_number=line_num,
                    message=f"Inconsistent column count: expected {num_cols}, got {len(values)}",
                    context_line=line,
                )

            # Parse each value
            for col_idx, value in enumerate(values):
                try:
                    numeric_value = float(value)
                except ValueError:
                    raise ParseError(
                        file_path=path,
                        line_number=line_num,
                        column=col_idx + 1,
                        message="Invalid numeric value",
                        raw_value=value,
                        context_line=line,
                    ) from None

                data_arrays[col_idx].append(numeric_value)

        # Build DataFrame
        columns: dict[str, Column] = {}
        for idx, name in enumerate(column_names):
            columns[name] = Column(
                name=name,
                index=idx,
                data=np.array(data_arrays[idx], dtype=np.float64),
            )

        return DataFrame(
            columns=columns,
            source_file=path,
            row_count=len(data_arrays[0]),
            _column_order=column_names,
        )

    def parse_multiple(self, file_paths: Sequence[Path | str]) -> list[DataFrame]:
        """Parse multiple TSV files.

        Args:
            file_paths: List of paths to TSV files.

        Returns:
            List of DataFrames, one per file.

        Raises:
            FileNotFoundError: If any file does not exist.
            ParseError: If any file contains invalid data.
        """
        return [self.parse(path) for path in file_paths]

    def _read_lines(self, path: Path) -> list[str]:
        """Read all lines from file with proper encoding."""
        with open(path, encoding=self.config.encoding) as f:
            return f.readlines()

    def _filter_lines(self, lines: list[str]) -> list[tuple[str, int]]:
        """Filter out comment and empty lines.

        Returns list of (line_content, line_number) tuples.
        Line numbers are 1-based.
        """
        result: list[tuple[str, int]] = []

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip comment lines
            if any(stripped.startswith(char) for char in self.config.comment_chars):
                continue

            result.append((stripped, line_num))

        return result

    def _parse_header(self, line: str) -> list[str]:
        """Parse header line into column names."""
        names = line.split(self.config.delimiter)
        return [name.strip() for name in names]


__all__ = ["ParserConfig", "TSVParser"]
