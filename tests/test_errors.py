"""Tests for custom exceptions."""

from pathlib import Path

import pytest

from plottini.utils.errors import ExportError, ParseError, ValidationError


class TestParseError:
    """Tests for ParseError exception."""

    def test_basic_error_message(self) -> None:
        """Test basic error message formatting."""
        error = ParseError(
            file_path=Path("data.tsv"),
            line_number=42,
            message="Invalid numeric value",
        )
        error_str = str(error)
        assert "ParseError: Invalid numeric value" in error_str
        assert "File: data.tsv" in error_str
        assert "Line 42" in error_str

    def test_error_with_column(self) -> None:
        """Test error message includes column when provided."""
        error = ParseError(
            file_path=Path("data.tsv"),
            line_number=10,
            column=3,
            message="Expected number",
        )
        error_str = str(error)
        assert "Line 10, Column 3" in error_str

    def test_error_with_raw_value(self) -> None:
        """Test error message includes raw value when provided."""
        error = ParseError(
            file_path=Path("data.tsv"),
            line_number=5,
            column=2,
            message="Invalid value",
            raw_value="N/A",
        )
        error_str = str(error)
        assert "got 'N/A'" in error_str

    def test_error_with_context_and_pointer(self) -> None:
        """Test error message includes context line and pointer."""
        error = ParseError(
            file_path=Path("data.tsv"),
            line_number=42,
            column=3,
            message="Expected numeric value",
            raw_value="N/A",
            context_line="1.5\t2.3\tN/A\t4.1",
        )
        error_str = str(error)
        assert 'Context: "1.5\t2.3\tN/A\t4.1"' in error_str
        assert "^^^" in error_str  # Pointer for "N/A"

    def test_error_is_exception(self) -> None:
        """Test that ParseError can be raised and caught."""
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                file_path=Path("test.tsv"),
                line_number=1,
                message="Test error",
            )
        assert exc_info.value.line_number == 1


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_basic_validation_error(self) -> None:
        """Test basic validation error message."""
        error = ValidationError(message="Value out of range")
        error_str = str(error)
        assert "ValidationError: Value out of range" in error_str

    def test_validation_error_with_field(self) -> None:
        """Test validation error with field name."""
        error = ValidationError(
            message="Invalid value",
            field="dpi",
        )
        error_str = str(error)
        assert "Field: dpi" in error_str

    def test_validation_error_with_value(self) -> None:
        """Test validation error with value."""
        error = ValidationError(
            message="Must be positive",
            field="width",
            value="-5",
        )
        error_str = str(error)
        assert "Value: '-5'" in error_str
        assert "Field: width" in error_str

    def test_validation_error_is_exception(self) -> None:
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(message="Test validation error")
        assert "Test validation error" in exc_info.value.message


class TestExportError:
    """Tests for ExportError exception."""

    def test_basic_export_error(self) -> None:
        """Test basic export error message."""
        error = ExportError(message="Failed to write file")
        error_str = str(error)
        assert "ExportError: Failed to write file" in error_str

    def test_export_error_with_path(self) -> None:
        """Test export error with output path."""
        error = ExportError(
            message="Permission denied",
            output_path=Path("/readonly/output.png"),
        )
        error_str = str(error)
        assert "Output path: /readonly/output.png" in error_str

    def test_export_error_with_format(self) -> None:
        """Test export error with format."""
        error = ExportError(
            message="Unsupported format",
            format="gif",
        )
        error_str = str(error)
        assert "Format: gif" in error_str

    def test_export_error_full(self) -> None:
        """Test export error with all fields."""
        error = ExportError(
            message="Export failed",
            output_path=Path("output.pdf"),
            format="pdf",
        )
        error_str = str(error)
        assert "ExportError: Export failed" in error_str
        assert "Output path: output.pdf" in error_str
        assert "Format: pdf" in error_str

    def test_export_error_is_exception(self) -> None:
        """Test that ExportError can be raised and caught."""
        with pytest.raises(ExportError) as exc_info:
            raise ExportError(message="Test export error")
        assert "Test export error" in exc_info.value.message
