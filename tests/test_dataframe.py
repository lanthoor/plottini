"""Tests for DataFrame module."""

from pathlib import Path

import numpy as np
import pytest

from plottini.core.dataframe import Column, DataFrame, create_empty_dataframe


class TestColumn:
    """Tests for Column dataclass."""

    def test_column_creation(self) -> None:
        """Test basic column creation."""
        data = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        col = Column(name="Energy", index=0, data=data)

        assert col.name == "Energy"
        assert col.index == 0
        assert len(col) == 3
        assert col.is_derived is False

    def test_column_derived_flag(self) -> None:
        """Test column with is_derived flag."""
        data = np.array([1.0, 2.0], dtype=np.float64)
        col = Column(name="computed", index=2, data=data, is_derived=True)

        assert col.is_derived is True


class TestDataFrame:
    """Tests for DataFrame class."""

    @pytest.fixture
    def sample_dataframe(self) -> DataFrame:
        """Create a sample DataFrame for testing."""
        col1 = Column(
            name="k_point",
            index=0,
            data=np.array([0.0, 0.1, 0.2], dtype=np.float64),
        )
        col2 = Column(
            name="Energy_eV",
            index=1,
            data=np.array([-5.0, -4.5, -4.0], dtype=np.float64),
        )
        col3 = Column(
            name="DOS",
            index=2,
            data=np.array([0.001, 0.002, 0.003], dtype=np.float64),
        )
        return DataFrame(
            columns={"k_point": col1, "Energy_eV": col2, "DOS": col3},
            source_file=Path("test.tsv"),
            row_count=3,
        )

    def test_dataframe_creation(self, sample_dataframe: DataFrame) -> None:
        """Test DataFrame creation with columns."""
        assert sample_dataframe.row_count == 3
        assert sample_dataframe.source_file == Path("test.tsv")
        assert len(sample_dataframe.columns) == 3

    def test_get_column_names(self, sample_dataframe: DataFrame) -> None:
        """Test getting ordered column names."""
        names = sample_dataframe.get_column_names()
        assert names == ["k_point", "Energy_eV", "DOS"]

    def test_get_column_by_name(self, sample_dataframe: DataFrame) -> None:
        """Test retrieving column by name."""
        col = sample_dataframe.get_column("Energy_eV")
        assert col.name == "Energy_eV"
        assert col.index == 1
        np.testing.assert_array_equal(col.data, [-5.0, -4.5, -4.0])

    def test_subscript_access(self, sample_dataframe: DataFrame) -> None:
        """Test accessing column data via subscript."""
        data = sample_dataframe["k_point"]
        np.testing.assert_array_equal(data, [0.0, 0.1, 0.2])

    def test_len_returns_row_count(self, sample_dataframe: DataFrame) -> None:
        """Test that len() returns row count."""
        assert len(sample_dataframe) == 3

    def test_iteration_over_columns(self, sample_dataframe: DataFrame) -> None:
        """Test iterating over column names."""
        names = list(sample_dataframe)
        assert names == ["k_point", "Energy_eV", "DOS"]

    def test_column_membership(self, sample_dataframe: DataFrame) -> None:
        """Test 'in' operator for column names."""
        assert "Energy_eV" in sample_dataframe
        assert "nonexistent" not in sample_dataframe

    def test_invalid_column_raises_keyerror(self, sample_dataframe: DataFrame) -> None:
        """Test that invalid column name raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            sample_dataframe.get_column("nonexistent")

        error_msg = str(exc_info.value)
        assert "nonexistent" in error_msg
        assert "Available columns" in error_msg

    def test_subscript_invalid_column_raises_keyerror(self, sample_dataframe: DataFrame) -> None:
        """Test that subscript with invalid name raises KeyError."""
        with pytest.raises(KeyError):
            _ = sample_dataframe["nonexistent"]

    def test_is_empty_false(self, sample_dataframe: DataFrame) -> None:
        """Test is_empty returns False for non-empty DataFrame."""
        assert sample_dataframe.is_empty() is False

    def test_add_derived_column_not_implemented(self, sample_dataframe: DataFrame) -> None:
        """Test that add_derived_column raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            sample_dataframe.add_derived_column("velocity", "col1 / col2")

        assert "not yet implemented" in str(exc_info.value)

    def test_filter_rows_not_implemented(self, sample_dataframe: DataFrame) -> None:
        """Test that filter_rows raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            sample_dataframe.filter_rows("Energy_eV", min_val=-5.0, max_val=-4.0)

        assert "not yet implemented" in str(exc_info.value)


class TestEmptyDataFrame:
    """Tests for empty DataFrame handling."""

    def test_create_empty_dataframe(self) -> None:
        """Test creating an empty DataFrame."""
        df = create_empty_dataframe(Path("empty.tsv"))

        assert df.row_count == 0
        assert df.source_file == Path("empty.tsv")
        assert len(df.columns) == 0
        assert df.get_column_names() == []

    def test_empty_dataframe_is_empty(self) -> None:
        """Test is_empty returns True for empty DataFrame."""
        df = create_empty_dataframe(Path("empty.tsv"))
        assert df.is_empty() is True

    def test_empty_dataframe_len(self) -> None:
        """Test len() returns 0 for empty DataFrame."""
        df = create_empty_dataframe(Path("empty.tsv"))
        assert len(df) == 0

    def test_empty_dataframe_iteration(self) -> None:
        """Test iterating over empty DataFrame yields nothing."""
        df = create_empty_dataframe(Path("empty.tsv"))
        assert list(df) == []


class TestDataFrameColumnOrder:
    """Tests for column ordering preservation."""

    def test_column_order_preserved(self) -> None:
        """Test that column order is determined by index."""
        # Create columns in non-index order
        col3 = Column(name="C", index=2, data=np.array([1.0], dtype=np.float64))
        col1 = Column(name="A", index=0, data=np.array([1.0], dtype=np.float64))
        col2 = Column(name="B", index=1, data=np.array([1.0], dtype=np.float64))

        df = DataFrame(
            columns={"C": col3, "A": col1, "B": col2},
            source_file=Path("test.tsv"),
            row_count=1,
        )

        # Column order should be by index, not by insertion order
        assert df.get_column_names() == ["A", "B", "C"]

    def test_explicit_column_order(self) -> None:
        """Test explicitly providing column order."""
        col1 = Column(name="X", index=0, data=np.array([1.0], dtype=np.float64))
        col2 = Column(name="Y", index=1, data=np.array([2.0], dtype=np.float64))

        df = DataFrame(
            columns={"X": col1, "Y": col2},
            source_file=Path("test.tsv"),
            row_count=1,
            _column_order=["Y", "X"],  # Explicit custom order
        )

        assert df.get_column_names() == ["Y", "X"]
