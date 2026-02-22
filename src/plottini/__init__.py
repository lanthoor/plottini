"""
Plottini - A user-friendly graph builder with matplotlib backend.

Plottini allows non-technical users to create publication-quality graphs
from TSV data files with an intuitive UI and powerful configuration options.
"""

__version__ = "2026.2.3"
__author__ = "Lallu Anthoor"
__email__ = "dev@spendly.co.in"
__license__ = "MIT"

# Core data handling
from plottini.core.dataframe import Column, DataFrame, create_empty_dataframe
from plottini.core.exporter import ExportConfig, Exporter, ExportFormat
from plottini.core.parser import ParserConfig, TSVParser

# Custom exceptions
from plottini.utils.errors import ExportError, ParseError, ValidationError

__all__ = [
    # Metadata
    "__version__",
    # Parser
    "TSVParser",
    "ParserConfig",
    # DataFrame
    "DataFrame",
    "Column",
    "create_empty_dataframe",
    # Exporter
    "Exporter",
    "ExportFormat",
    "ExportConfig",
    # Exceptions
    "ParseError",
    "ValidationError",
    "ExportError",
]
