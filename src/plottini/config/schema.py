"""Configuration schema for Plottini.

This module defines the dataclasses used for UI state management.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AlignmentConfig:
    """Configuration for multi-file alignment.

    Attributes:
        enabled: Whether alignment is enabled
        column: Column name to align on
    """

    enabled: bool = False
    column: str = ""


@dataclass
class DerivedColumnConfig:
    """Configuration for a derived column.

    Attributes:
        name: Name for the new column
        expression: Mathematical expression to evaluate
    """

    name: str
    expression: str


@dataclass
class FilterConfig:
    """Configuration for row filtering.

    Attributes:
        column: Column name to filter on
        min: Minimum value (inclusive), or None for no lower bound
        max: Maximum value (inclusive), or None for no upper bound
    """

    column: str
    min: float | None = None
    max: float | None = None


__all__ = [
    "AlignmentConfig",
    "DerivedColumnConfig",
    "FilterConfig",
]
