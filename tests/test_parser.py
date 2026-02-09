"""Tests for TSV Parser module."""

from pathlib import Path

import numpy as np
import pytest

from plottini.core.parser import ParserConfig, TSVParser
from plottini.utils.errors import ParseError

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParserConfig:
    """Tests for ParserConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ParserConfig()
        assert config.has_header is True
        assert config.comment_chars == ["#"]
        assert config.delimiter == "\t"
        assert config.encoding == "utf-8"

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = ParserConfig(
            has_header=False,
            comment_chars=["#", "!"],
            delimiter=",",
            encoding="latin-1",
        )
        assert config.has_header is False
        assert config.comment_chars == ["#", "!"]
        assert config.delimiter == ","
        assert config.encoding == "latin-1"


class TestTSVParser:
    """Tests for TSVParser class."""

    def test_parse_simple_no_headers(self) -> None:
        """Test parsing file without headers."""
        config = ParserConfig(has_header=False)
        parser = TSVParser(config)
        df = parser.parse(FIXTURES_DIR / "simple.tsv")

        assert df.row_count == 11
        assert df.get_column_names() == ["Column 1", "Column 2", "Column 3"]
        np.testing.assert_almost_equal(df["Column 1"][0], 0.0)
        np.testing.assert_almost_equal(df["Column 2"][0], -5.2341)

    def test_parse_with_headers(self) -> None:
        """Test parsing file with headers."""
        parser = TSVParser(ParserConfig(has_header=True))
        df = parser.parse(FIXTURES_DIR / "with_headers.tsv")

        assert df.row_count == 11
        assert df.get_column_names() == ["k_point", "Energy_eV", "DOS_states_per_eV"]
        np.testing.assert_almost_equal(df["k_point"][0], 0.0)

    def test_parse_with_comments(self) -> None:
        """Test parsing file with comment lines."""
        parser = TSVParser()
        df = parser.parse(FIXTURES_DIR / "with_comments.tsv")

        # Comments should be skipped
        assert df.row_count == 10
        assert "Energy_eV" in df.get_column_names()
        # First data line after comments
        np.testing.assert_almost_equal(df["Energy_eV"][0], -10.0)

    def test_parse_scientific_notation(self) -> None:
        """Test parsing scientific notation values."""
        parser = TSVParser()
        df = parser.parse(FIXTURES_DIR / "scientific_notation.tsv")

        assert df.row_count == 10
        # Check scientific notation parsed correctly
        np.testing.assert_almost_equal(df["band_energy"][0], -1.234567e-05)
        np.testing.assert_almost_equal(df["weight"][0], 3.456789e02)

    def test_parse_whitespace_trimmed(self) -> None:
        """Test that whitespace is trimmed from values."""
        config = ParserConfig(has_header=False)
        parser = TSVParser(config)
        df = parser.parse(FIXTURES_DIR / "whitespace.tsv")

        assert df.row_count == 5
        # Values should be trimmed
        np.testing.assert_almost_equal(df["Column 1"][0], 0.0)
        np.testing.assert_almost_equal(df["Column 2"][0], -5.2341)

    def test_parse_large_file(self) -> None:
        """Test parsing large file for performance."""
        parser = TSVParser()
        df = parser.parse(FIXTURES_DIR / "large.tsv")

        assert df.row_count == 1000
        assert len(df.get_column_names()) == 3

    def test_parse_empty_file_returns_empty_dataframe(self) -> None:
        """Test that empty file returns empty DataFrame with warning."""
        parser = TSVParser()

        with pytest.warns(UserWarning, match="empty or contains only comments"):
            df = parser.parse(FIXTURES_DIR / "empty.tsv")

        assert df.is_empty()
        assert df.row_count == 0

    def test_parse_file_not_found(self) -> None:
        """Test that missing file raises FileNotFoundError."""
        parser = TSVParser()

        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(FIXTURES_DIR / "nonexistent.tsv")

        assert "nonexistent.tsv" in str(exc_info.value)

    def test_parse_non_numeric_raises_error(self) -> None:
        """Test that non-numeric values raise ParseError."""
        parser = TSVParser()

        with pytest.raises(ParseError) as exc_info:
            parser.parse(FIXTURES_DIR / "malformed" / "non_numeric.tsv")

        error = exc_info.value
        assert error.line_number == 3  # Line with "N/A"
        assert error.column == 3
        assert "N/A" in str(error.raw_value)

    def test_parse_inconsistent_columns_raises_error(self) -> None:
        """Test that inconsistent column count raises ParseError."""
        config = ParserConfig(has_header=False)
        parser = TSVParser(config)

        with pytest.raises(ParseError) as exc_info:
            parser.parse(FIXTURES_DIR / "malformed" / "inconsistent_columns.tsv")

        error = exc_info.value
        assert "Inconsistent column count" in error.message

    def test_parse_multiple_files(self) -> None:
        """Test parsing multiple files at once."""
        parser = TSVParser()
        paths = [
            FIXTURES_DIR / "with_headers.tsv",
            FIXTURES_DIR / "with_comments.tsv",
        ]

        dataframes = parser.parse_multiple(paths)

        assert len(dataframes) == 2
        assert dataframes[0].source_file == paths[0]
        assert dataframes[1].source_file == paths[1]

    def test_parse_string_path(self) -> None:
        """Test that string paths work as well as Path objects."""
        parser = TSVParser()
        df = parser.parse(str(FIXTURES_DIR / "with_headers.tsv"))

        assert df.row_count == 11

    def test_default_config_used_when_none(self) -> None:
        """Test that default config is used when None provided."""
        parser = TSVParser(None)
        assert parser.config.has_header is True
        assert parser.config.delimiter == "\t"


class TestParserEdgeCases:
    """Tests for parser edge cases."""

    def test_header_only_file(self, tmp_path: Path) -> None:
        """Test file with only header row."""
        file = tmp_path / "header_only.tsv"
        file.write_text("Col1\tCol2\tCol3\n")

        parser = TSVParser()
        with pytest.warns(UserWarning, match="contains only a header row"):
            df = parser.parse(file)

        assert df.is_empty()

    def test_comments_only_file(self, tmp_path: Path) -> None:
        """Test file with only comments."""
        file = tmp_path / "comments_only.tsv"
        file.write_text("# This is a comment\n# Another comment\n")

        parser = TSVParser()
        with pytest.warns(UserWarning, match="empty or contains only comments"):
            df = parser.parse(file)

        assert df.is_empty()

    def test_custom_comment_char(self, tmp_path: Path) -> None:
        """Test custom comment character."""
        file = tmp_path / "custom_comment.tsv"
        file.write_text("! Comment line\n1.0\t2.0\n3.0\t4.0\n")

        config = ParserConfig(has_header=False, comment_chars=["!"])
        parser = TSVParser(config)
        df = parser.parse(file)

        assert df.row_count == 2

    def test_multiple_comment_chars(self, tmp_path: Path) -> None:
        """Test multiple comment characters."""
        file = tmp_path / "multi_comment.tsv"
        file.write_text("# Hash comment\n! Bang comment\n1.0\t2.0\n")

        config = ParserConfig(has_header=False, comment_chars=["#", "!"])
        parser = TSVParser(config)
        df = parser.parse(file)

        assert df.row_count == 1

    def test_negative_scientific_exponent(self) -> None:
        """Test parsing negative exponents in scientific notation."""
        parser = TSVParser()
        df = parser.parse(FIXTURES_DIR / "scientific_notation.tsv")

        # Check values with negative exponents
        assert df["band_energy"][0] < 0.001  # -1.234567E-05

    def test_column_order_preserved(self) -> None:
        """Test that column order from file is preserved."""
        parser = TSVParser()
        df = parser.parse(FIXTURES_DIR / "with_headers.tsv")

        # Order should match file header order
        names = df.get_column_names()
        assert names[0] == "k_point"
        assert names[1] == "Energy_eV"
        assert names[2] == "DOS_states_per_eV"


class TestParseErrorFormat:
    """Tests for ParseError formatting in parser context."""

    def test_error_includes_file_path(self) -> None:
        """Test that error includes file path."""
        parser = TSVParser()

        with pytest.raises(ParseError) as exc_info:
            parser.parse(FIXTURES_DIR / "malformed" / "non_numeric.tsv")

        error_str = str(exc_info.value)
        assert "non_numeric.tsv" in error_str

    def test_error_includes_context_line(self) -> None:
        """Test that error includes context line."""
        parser = TSVParser()

        with pytest.raises(ParseError) as exc_info:
            parser.parse(FIXTURES_DIR / "malformed" / "non_numeric.tsv")

        error_str = str(exc_info.value)
        assert "Context:" in error_str
