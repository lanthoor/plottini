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

    def test_duplicate_column_names_raises_error(self, tmp_path: Path) -> None:
        """Test that duplicate column names raise ParseError."""
        file = tmp_path / "duplicate_headers.tsv"
        file.write_text("col_a\tcol_b\tcol_a\n1.0\t2.0\t3.0\n")

        parser = TSVParser()
        with pytest.raises(ParseError) as exc_info:
            parser.parse(file)

        error = exc_info.value
        assert "Duplicate column name" in error.message
        assert "col_a" in error.message
        assert error.column == 3  # Third column is the duplicate


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


class TestParseBlocks:
    """Tests for parse_blocks method for multi-block files."""

    def test_single_block_file(self, tmp_path: Path) -> None:
        """Test parse_blocks with single block returns one DataFrame."""
        file = tmp_path / "single_block.tsv"
        file.write_text("x\ty\n1.0\t2.0\n3.0\t4.0\n")

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 1
        assert dfs[0].row_count == 2
        assert dfs[0].block_index == 0

    def test_multiple_blocks_with_comments(self, tmp_path: Path) -> None:
        """Test parse_blocks with multiple blocks separated by comments."""
        file = tmp_path / "multi_block.tsv"
        content = """x\ty
1.0\t2.0
3.0\t4.0
# Block separator
x\ty
5.0\t6.0
7.0\t8.0
9.0\t10.0
"""
        file.write_text(content)

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 2
        assert dfs[0].row_count == 2
        assert dfs[0].block_index == 0
        assert dfs[1].row_count == 3
        assert dfs[1].block_index == 1

    def test_multiple_blocks_with_empty_lines(self, tmp_path: Path) -> None:
        """Test parse_blocks with blocks separated by empty lines."""
        file = tmp_path / "multi_block_empty.tsv"
        content = """x\ty
1.0\t2.0

x\ty
3.0\t4.0
"""
        file.write_text(content)

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 2
        assert dfs[0].row_count == 1
        assert dfs[1].row_count == 1

    def test_blocks_no_header(self, tmp_path: Path) -> None:
        """Test parse_blocks without headers."""
        file = tmp_path / "multi_block_no_header.tsv"
        content = """1.0\t2.0
3.0\t4.0
# separator
5.0\t6.0
"""
        file.write_text(content)

        config = ParserConfig(has_header=False)
        parser = TSVParser(config)
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 2
        assert dfs[0].get_column_names() == ["Column 1", "Column 2"]
        assert dfs[1].get_column_names() == ["Column 1", "Column 2"]

    def test_blocks_preserve_source_file(self, tmp_path: Path) -> None:
        """Test that all blocks reference the same source file."""
        file = tmp_path / "multi_block.tsv"
        file.write_text("x\ty\n1.0\t2.0\n# sep\nx\ty\n3.0\t4.0\n")

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 2
        assert dfs[0].source_file == file
        assert dfs[1].source_file == file

    def test_space_delimiter_multi_block(self, tmp_path: Path) -> None:
        """Test parse_blocks with space delimiter."""
        file = tmp_path / "space_multi.dat"
        content = """1.0  2.0  3.0
4.0  5.0  6.0
# block 2
7.0  8.0  9.0
"""
        file.write_text(content)

        config = ParserConfig(has_header=False, delimiter=" ")
        parser = TSVParser(config)
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 2
        assert dfs[0].row_count == 2
        assert dfs[1].row_count == 1


class TestParserEdgeCasesAdditional:
    """Additional edge case tests for parser."""

    def test_unicode_in_headers(self, tmp_path: Path) -> None:
        """Test parsing file with unicode characters in headers."""
        file = tmp_path / "unicode.tsv"
        file.write_text("Temperature_\u00b0C\tPressure_hPa\n25.0\t1013.0\n", encoding="utf-8")

        parser = TSVParser()
        df = parser.parse(file)

        assert "Temperature_\u00b0C" in df.get_column_names()
        assert "Pressure_hPa" in df.get_column_names()

    def test_very_long_header_names(self, tmp_path: Path) -> None:
        """Test parsing file with very long header names."""
        long_name = "a" * 200
        file = tmp_path / "long_header.tsv"
        file.write_text(f"{long_name}\ty\n1.0\t2.0\n")

        parser = TSVParser()
        df = parser.parse(file)

        assert long_name in df.get_column_names()

    def test_mixed_line_endings(self, tmp_path: Path) -> None:
        """Test parsing file with mixed line endings (\\r\\n and \\n)."""
        file = tmp_path / "mixed_endings.tsv"
        file.write_bytes(b"x\ty\r\n1.0\t2.0\n3.0\t4.0\r\n")

        parser = TSVParser()
        df = parser.parse(file)

        assert df.row_count == 2

    def test_trailing_delimiter(self, tmp_path: Path) -> None:
        """Test parsing file with trailing delimiter on lines."""
        file = tmp_path / "trailing.tsv"
        file.write_text("x\ty\t\n1.0\t2.0\t\n3.0\t4.0\t\n")

        parser = TSVParser()
        df = parser.parse(file)

        # Should handle trailing delimiters gracefully
        assert df.row_count == 2
        # Last column should be parsed (even if empty or dropped)

    def test_single_column_file(self, tmp_path: Path) -> None:
        """Test parsing file with only one column."""
        file = tmp_path / "single_col.tsv"
        file.write_text("values\n1.0\n2.0\n3.0\n")

        parser = TSVParser()
        df = parser.parse(file)

        assert df.row_count == 3
        assert df.get_column_names() == ["values"]

    def test_header_with_numbers(self, tmp_path: Path) -> None:
        """Test parsing file where headers start with numbers."""
        file = tmp_path / "num_headers.tsv"
        file.write_text("1st_column\t2nd_column\n1.0\t2.0\n")

        parser = TSVParser()
        df = parser.parse(file)

        assert "1st_column" in df.get_column_names()
        assert "2nd_column" in df.get_column_names()

    def test_very_large_numbers(self, tmp_path: Path) -> None:
        """Test parsing very large numbers."""
        file = tmp_path / "large_nums.tsv"
        file.write_text("x\ty\n1.0e308\t-1.0e308\n")

        parser = TSVParser()
        df = parser.parse(file)

        assert df["x"][0] == 1.0e308
        assert df["y"][0] == -1.0e308

    def test_very_small_numbers(self, tmp_path: Path) -> None:
        """Test parsing very small numbers."""
        file = tmp_path / "small_nums.tsv"
        file.write_text("x\ty\n1.0e-308\t-1.0e-308\n")

        parser = TSVParser()
        df = parser.parse(file)

        assert df["x"][0] == 1.0e-308
        assert df["y"][0] == -1.0e-308


class TestParseBlocksEdgeCases:
    """Edge cases for multi-block parsing."""

    def test_consecutive_separators(self, tmp_path: Path) -> None:
        """Test parsing with multiple consecutive separator lines."""
        file = tmp_path / "multi_sep.tsv"
        file.write_text("x\ty\n1.0\t2.0\n\n\n\nx\ty\n3.0\t4.0\n")

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        # Empty blocks should be skipped
        assert len(dfs) == 2

    def test_block_at_end_with_trailing_newlines(self, tmp_path: Path) -> None:
        """Test parsing block at end of file with trailing newlines."""
        file = tmp_path / "trailing.tsv"
        file.write_text("x\ty\n1.0\t2.0\n\n\n")

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 1
        assert dfs[0].row_count == 1

    def test_many_blocks(self, tmp_path: Path) -> None:
        """Test parsing file with many blocks."""
        content = ""
        for i in range(10):
            content += f"x\ty\n{float(i)}\t{float(i + 1)}\n\n"

        file = tmp_path / "many_blocks.tsv"
        file.write_text(content)

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 10
        for i, df in enumerate(dfs):
            assert df.block_index == i

    def test_blocks_with_different_column_counts(self, tmp_path: Path) -> None:
        """Test parsing blocks with different column counts."""
        content = """x\ty\n1.0\t2.0\n
x\ty\tz\n3.0\t4.0\t5.0\n"""

        file = tmp_path / "diff_cols.tsv"
        file.write_text(content)

        parser = TSVParser()
        dfs = parser.parse_blocks(file)

        assert len(dfs) == 2
        assert len(dfs[0].get_column_names()) == 2
        assert len(dfs[1].get_column_names()) == 3
