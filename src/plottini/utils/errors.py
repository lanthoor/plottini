"""Custom exceptions for Plottini.

This module provides user-friendly exceptions with detailed context
for parsing, validation, and export errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParseError(Exception):
    """Error raised when parsing a TSV file fails.

    Provides detailed context including file path, line number, column,
    and a visual pointer to the problematic value.

    Attributes:
        file_path: Path to the file being parsed
        line_number: 1-based line number where error occurred
        column: 1-based column number (None if not applicable)
        message: Human-readable error description
        raw_value: The problematic value that caused the error
        context_line: The full line of text for context display
    """

    file_path: Path
    line_number: int
    message: str
    column: int | None = None
    raw_value: str | None = None
    context_line: str | None = None

    def __str__(self) -> str:
        """Format error with context and visual pointer."""
        parts = [f"ParseError: {self.message}"]
        parts.append(f"  File: {self.file_path}")

        location = f"  Line {self.line_number}"
        if self.column is not None:
            location += f", Column {self.column}"
        if self.raw_value is not None:
            location += f": got '{self.raw_value}'"
        parts.append(location)

        if self.context_line is not None and self.column is not None:
            parts.append(f'  Context: "{self.context_line}"')
            # Create pointer to the error location
            pointer_offset = len('  Context: "') + self._find_value_position()
            pointer_length = len(self.raw_value) if self.raw_value else 1
            pointer = " " * pointer_offset + "^" * pointer_length
            parts.append(pointer)

        return "\n".join(parts)

    def _find_value_position(self) -> int:
        """Find the character position of the raw_value in the context line."""
        if self.context_line is None or self.raw_value is None:
            return 0

        # Split by tabs and find the column position
        columns = self.context_line.split("\t")
        if self.column is not None and 1 <= self.column <= len(columns):
            position = 0
            for i in range(self.column - 1):
                position += len(columns[i]) + 1  # +1 for tab
            return position
        return 0


@dataclass
class ValidationError(Exception):
    """Error raised when data validation fails.

    Attributes:
        message: Human-readable error description
        field: Name of the field that failed validation (optional)
        value: The value that failed validation (optional)
    """

    message: str
    field: str | None = None
    value: str | None = None

    def __str__(self) -> str:
        """Format validation error message."""
        parts = [f"ValidationError: {self.message}"]
        if self.field is not None:
            parts.append(f"  Field: {self.field}")
        if self.value is not None:
            parts.append(f"  Value: '{self.value}'")
        return "\n".join(parts)


@dataclass
class ExportError(Exception):
    """Error raised when exporting a figure fails.

    Attributes:
        message: Human-readable error description
        output_path: Path where export was attempted (optional)
        format: Export format that was attempted (optional)
    """

    message: str
    output_path: Path | None = None
    format: str | None = None

    def __str__(self) -> str:
        """Format export error message."""
        parts = [f"ExportError: {self.message}"]
        if self.output_path is not None:
            parts.append(f"  Output path: {self.output_path}")
        if self.format is not None:
            parts.append(f"  Format: {self.format}")
        return "\n".join(parts)


__all__ = ["ParseError", "ValidationError", "ExportError"]
