"""Tests for UI state management."""

from __future__ import annotations

import numpy as np
import pytest

from plottini.config.schema import AlignmentConfig, DerivedColumnConfig, FilterConfig
from plottini.core.dataframe import Column, DataFrame
from plottini.core.plotter import ChartType, SeriesConfig
from plottini.ui.state import AppState, DataSource, UploadedFile, create_default_state


class TestUploadedFile:
    """Tests for UploadedFile dataclass."""

    def test_creation(self):
        """Test UploadedFile creation."""
        content = b"col1\tcol2\n1\t2\n"
        uf = UploadedFile(name="test.tsv", content=content)
        assert uf.name == "test.tsv"
        assert uf.content == content

    def test_get_file_object(self):
        """Test get_file_object returns seekable BytesIO."""
        content = b"col1\tcol2\n1\t2\n"
        uf = UploadedFile(name="test.tsv", content=content)
        file_obj = uf.get_file_object()

        # Should be readable
        data = file_obj.read()
        assert data == content

        # Should be seekable
        file_obj.seek(0)
        data2 = file_obj.read()
        assert data2 == content


class TestDataSource:
    """Tests for DataSource dataclass."""

    def test_display_name_without_block(self):
        """Test display_name for single-block file."""
        ds = DataSource(file_name="data.tsv")
        assert ds.display_name == "data.tsv"

    def test_display_name_with_block_index_zero(self):
        """Test display_name for first block (index 0)."""
        ds = DataSource(file_name="data.tsv", block_index=0)
        assert ds.display_name == "data.tsv (block 1)"

    def test_display_name_with_block_index_nonzero(self):
        """Test display_name for non-first block."""
        ds = DataSource(file_name="data.tsv", block_index=2)
        assert ds.display_name == "data.tsv (block 3)"

    def test_hash_equals_for_same_values(self):
        """Test DataSource hashing for dict keys."""
        ds1 = DataSource(file_name="data.tsv", block_index=0)
        ds2 = DataSource(file_name="data.tsv", block_index=0)
        assert ds1 == ds2
        assert hash(ds1) == hash(ds2)

    def test_hash_differs_for_different_blocks(self):
        """Test different blocks have different hashes."""
        ds1 = DataSource(file_name="data.tsv", block_index=0)
        ds2 = DataSource(file_name="data.tsv", block_index=1)
        assert ds1 != ds2
        assert hash(ds1) != hash(ds2)

    def test_hash_differs_for_different_files(self):
        """Test different files have different hashes."""
        ds1 = DataSource(file_name="data1.tsv", block_index=0)
        ds2 = DataSource(file_name="data2.tsv", block_index=0)
        assert ds1 != ds2
        assert hash(ds1) != hash(ds2)

    def test_equality_with_none_block_index(self):
        """Test equality when block_index is None."""
        ds1 = DataSource(file_name="data.tsv", block_index=None)
        ds2 = DataSource(file_name="data.tsv", block_index=None)
        assert ds1 == ds2

    def test_inequality_with_non_datasource(self):
        """Test inequality with non-DataSource objects."""
        ds = DataSource(file_name="data.tsv")
        assert ds != "data.tsv"
        assert ds != 42

    def test_can_be_used_as_dict_key(self):
        """Test DataSource can be used as dictionary key."""
        ds1 = DataSource(file_name="data.tsv", block_index=0)
        ds2 = DataSource(file_name="data.tsv", block_index=1)

        data: dict[DataSource, str] = {}
        data[ds1] = "first"
        data[ds2] = "second"

        assert data[ds1] == "first"
        assert data[ds2] == "second"
        assert len(data) == 2


class TestAppState:
    """Tests for AppState class."""

    def test_default_state_creation(self):
        """Test AppState creates with sensible defaults."""
        state = AppState()

        assert state.uploaded_files == {}
        assert state.data_sources == []
        assert state.parsed_data == {}
        assert state.derived_columns == []
        assert state.filters == []
        assert state.alignment is None
        assert state.series == []
        assert state.current_figure is None
        assert state.error_message is None

    def test_create_default_state_factory(self):
        """Test create_default_state factory function."""
        state = create_default_state()

        assert isinstance(state, AppState)
        assert state.plot_config.chart_type == ChartType.LINE
        assert state.plot_config.show_grid is True
        assert state.plot_config.show_legend is True

    def test_default_state_has_legend_loc(self):
        """Test default state includes legend_loc field."""
        state = create_default_state()

        assert hasattr(state.plot_config, "legend_loc")
        assert state.plot_config.legend_loc == "best"


class TestAppStateDataMethods:
    """Tests for data-related methods."""

    @pytest.fixture
    def sample_dataframe(self) -> DataFrame:
        """Create a sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 2.0, 3.0])),
                "y": Column(name="y", index=1, data=np.array([4.0, 5.0, 6.0])),
            },
            source_file=Path("test.tsv"),
            row_count=3,
        )

    @pytest.fixture
    def sample_dataframe2(self) -> DataFrame:
        """Create another sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 2.0])),
                "z": Column(name="z", index=1, data=np.array([7.0, 8.0])),
            },
            source_file=Path("test2.tsv"),
            row_count=2,
        )

    def test_get_all_column_names_empty(self):
        """Test get_all_column_names with no data."""
        state = AppState()
        assert state.get_all_column_names() == []

    def test_get_all_column_names_single_file(self, sample_dataframe):
        """Test get_all_column_names with one file."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe

        columns = state.get_all_column_names()
        assert sorted(columns) == ["x", "y"]

    def test_get_all_column_names_multiple_files(self, sample_dataframe, sample_dataframe2):
        """Test get_all_column_names aggregates from multiple files."""
        state = AppState()
        ds1 = DataSource(file_name="test.tsv")
        ds2 = DataSource(file_name="test2.tsv")
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        columns = state.get_all_column_names()
        assert sorted(columns) == ["x", "y", "z"]

    def test_get_dataframes_list_ordered(self, sample_dataframe, sample_dataframe2):
        """Test get_dataframes_list returns in order of data_sources."""
        state = AppState()
        ds1 = DataSource(file_name="test.tsv")
        ds2 = DataSource(file_name="test2.tsv")
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        dfs = state.get_dataframes_list()
        assert len(dfs) == 2
        assert dfs[0] is sample_dataframe
        assert dfs[1] is sample_dataframe2

    def test_clear_data_resets_state(self, sample_dataframe):
        """Test clear_data removes all loaded data."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.uploaded_files["test.tsv"] = UploadedFile(name="test.tsv", content=b"data")
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe
        state.derived_columns.append(DerivedColumnConfig(name="d", expression="x+y"))
        state.filters.append(FilterConfig(column="x", min=0.0))
        state.alignment = AlignmentConfig(enabled=True, column="x")
        state.series.append(SeriesConfig(x_column="x", y_column="y"))
        state.error_message = "test error"

        state.clear_data()

        assert state.uploaded_files == {}
        assert state.data_sources == []
        assert state.parsed_data == {}
        assert state.derived_columns == []
        assert state.filters == []
        assert state.alignment is None
        assert state.series == []
        assert state.error_message is None


class TestAppStateErrorHandling:
    """Tests for error handling methods."""

    def test_set_error(self):
        """Test error setting."""
        state = AppState()

        state.set_error("Test error message")

        assert state.error_message == "Test error message"

    def test_clear_error_removes_message(self):
        """Test clear_error removes the error message."""
        state = AppState()
        state.error_message = "Test error"

        state.clear_error()

        assert state.error_message is None


class TestAppStateHelperMethods:
    """Tests for helper/convenience methods."""

    @pytest.fixture
    def sample_dataframe(self) -> DataFrame:
        """Create a sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 2.0, 3.0])),
                "y": Column(name="y", index=1, data=np.array([4.0, 5.0, 6.0])),
            },
            source_file=Path("test.tsv"),
            row_count=3,
        )

    def test_has_data_false_when_empty(self):
        """Test has_data returns False when no data loaded."""
        state = AppState()
        assert state.has_data() is False

    def test_has_data_true_when_data_loaded(self, sample_dataframe):
        """Test has_data returns True when data is loaded."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.parsed_data[ds] = sample_dataframe

        assert state.has_data() is True

    def test_has_series_false_when_empty(self):
        """Test has_series returns False when no series configured."""
        state = AppState()
        assert state.has_series() is False

    def test_has_series_true_when_configured(self):
        """Test has_series returns True when series exist."""
        state = AppState()
        state.series.append(SeriesConfig(x_column="x", y_column="y"))

        assert state.has_series() is True

    def test_can_render_false_without_data(self):
        """Test can_render returns False without data."""
        state = AppState()
        state.series.append(SeriesConfig(x_column="x", y_column="y"))

        assert state.can_render() is False

    def test_can_render_false_without_series(self, sample_dataframe):
        """Test can_render returns False without series."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.parsed_data[ds] = sample_dataframe

        assert state.can_render() is False

    def test_can_render_true_with_both(self, sample_dataframe):
        """Test can_render returns True with data and series."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.parsed_data[ds] = sample_dataframe
        state.series.append(SeriesConfig(x_column="x", y_column="y"))

        assert state.can_render() is True

    def test_get_file_info_not_loaded(self):
        """Test get_file_info for file not in parsed_data."""
        state = AppState()
        info = state.get_file_info("unknown.tsv")

        assert info == "(not loaded)"

    def test_get_file_info_loaded(self, sample_dataframe):
        """Test get_file_info for loaded file."""
        state = AppState()
        ds = DataSource(file_name="test.tsv")
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe

        info = state.get_file_info("test.tsv")
        assert info == "(2 columns, 3 rows)"

    def test_get_file_names_empty(self):
        """Test get_file_names with no files."""
        state = AppState()
        assert state.get_file_names() == []

    def test_get_file_names_with_files(self):
        """Test get_file_names returns uploaded file names."""
        state = AppState()
        state.uploaded_files["a.tsv"] = UploadedFile(name="a.tsv", content=b"")
        state.uploaded_files["b.tsv"] = UploadedFile(name="b.tsv", content=b"")

        names = state.get_file_names()
        assert "a.tsv" in names
        assert "b.tsv" in names


class TestAppStateMultiBlock:
    """Tests for multi-block file handling."""

    @pytest.fixture
    def sample_dataframe(self) -> DataFrame:
        """Create a sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 2.0, 3.0])),
                "y": Column(name="y", index=1, data=np.array([4.0, 5.0, 6.0])),
            },
            source_file=Path("test.tsv"),
            row_count=3,
        )

    @pytest.fixture
    def sample_dataframe2(self) -> DataFrame:
        """Create another sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([7.0, 8.0])),
                "y": Column(name="y", index=1, data=np.array([9.0, 10.0])),
            },
            source_file=Path("test.tsv"),
            row_count=2,
        )

    @pytest.fixture
    def sample_dataframe3(self) -> DataFrame:
        """Create a third sample DataFrame with different columns."""
        from pathlib import Path

        return DataFrame(
            columns={
                "a": Column(name="a", index=0, data=np.array([1.0])),
                "b": Column(name="b", index=1, data=np.array([2.0])),
            },
            source_file=Path("test.tsv"),
            row_count=1,
        )

    def test_get_file_info_multi_block(self, sample_dataframe, sample_dataframe2):
        """Test get_file_info shows block count for multi-block files."""
        state = AppState()
        ds1 = DataSource(file_name="multi.tsv", block_index=0)
        ds2 = DataSource(file_name="multi.tsv", block_index=1)
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        info = state.get_file_info("multi.tsv")
        assert "2 blocks" in info
        assert "2 columns" in info
        assert "5 rows" in info  # 3 + 2 rows

    def test_get_file_info_three_blocks(
        self, sample_dataframe, sample_dataframe2, sample_dataframe3
    ):
        """Test get_file_info with three blocks."""
        state = AppState()
        ds1 = DataSource(file_name="multi.tsv", block_index=0)
        ds2 = DataSource(file_name="multi.tsv", block_index=1)
        ds3 = DataSource(file_name="multi.tsv", block_index=2)
        state.data_sources.extend([ds1, ds2, ds3])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2
        state.parsed_data[ds3] = sample_dataframe3

        info = state.get_file_info("multi.tsv")
        assert "3 blocks" in info
        # Should aggregate unique columns: x, y from first two, a, b from third = 4 columns
        assert "4 columns" in info
        assert "6 rows" in info  # 3 + 2 + 1 rows

    def test_get_data_source_info_not_loaded(self):
        """Test get_data_source_info for source not in parsed_data."""
        state = AppState()
        ds = DataSource(file_name="unknown.tsv")
        assert state.get_data_source_info(ds) == "(not loaded)"

    def test_get_data_source_info_loaded(self, sample_dataframe):
        """Test get_data_source_info for loaded data source."""
        state = AppState()
        ds = DataSource(file_name="test.tsv", block_index=0)
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe

        info = state.get_data_source_info(ds)
        assert "2 columns" in info
        assert "3 rows" in info

    def test_get_dataframes_list_with_multiple_blocks(self, sample_dataframe, sample_dataframe2):
        """Test get_dataframes_list returns blocks in order."""
        state = AppState()
        ds1 = DataSource(file_name="multi.tsv", block_index=0)
        ds2 = DataSource(file_name="multi.tsv", block_index=1)
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        dfs = state.get_dataframes_list()
        assert len(dfs) == 2
        assert dfs[0] is sample_dataframe
        assert dfs[1] is sample_dataframe2

    def test_get_all_column_names_multi_block_same_columns(
        self, sample_dataframe, sample_dataframe2
    ):
        """Test get_all_column_names deduplicates columns from blocks."""
        state = AppState()
        ds1 = DataSource(file_name="multi.tsv", block_index=0)
        ds2 = DataSource(file_name="multi.tsv", block_index=1)
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        columns = state.get_all_column_names()
        # Both blocks have x and y, should be deduplicated
        assert sorted(columns) == ["x", "y"]

    def test_get_all_column_names_multi_block_different_columns(
        self, sample_dataframe, sample_dataframe3
    ):
        """Test get_all_column_names combines columns from different blocks."""
        state = AppState()
        ds1 = DataSource(file_name="multi.tsv", block_index=0)
        ds2 = DataSource(file_name="multi.tsv", block_index=1)
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe  # has x, y
        state.parsed_data[ds2] = sample_dataframe3  # has a, b

        columns = state.get_all_column_names()
        assert sorted(columns) == ["a", "b", "x", "y"]


class TestAppStateFileRemoval:
    """Tests for file removal functionality."""

    @pytest.fixture
    def sample_dataframe(self) -> DataFrame:
        """Create a sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "x": Column(name="x", index=0, data=np.array([1.0, 2.0, 3.0])),
                "y": Column(name="y", index=1, data=np.array([4.0, 5.0, 6.0])),
            },
            source_file=Path("test.tsv"),
            row_count=3,
        )

    @pytest.fixture
    def sample_dataframe2(self) -> DataFrame:
        """Create another sample DataFrame for testing."""
        from pathlib import Path

        return DataFrame(
            columns={
                "a": Column(name="a", index=0, data=np.array([1.0, 2.0])),
                "b": Column(name="b", index=1, data=np.array([3.0, 4.0])),
            },
            source_file=Path("test2.tsv"),
            row_count=2,
        )

    def test_remove_file_clears_data(self, sample_dataframe):
        """Test remove_file removes file and associated data."""
        state = AppState()
        state.uploaded_files["test.tsv"] = UploadedFile(name="test.tsv", content=b"data")
        ds = DataSource(file_name="test.tsv")
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe

        state.remove_file("test.tsv")

        assert "test.tsv" not in state.uploaded_files
        assert ds not in state.data_sources
        assert ds not in state.parsed_data

    def test_remove_file_removes_associated_series(self, sample_dataframe):
        """Test remove_file removes series that depend on the file."""
        state = AppState()
        state.uploaded_files["test.tsv"] = UploadedFile(name="test.tsv", content=b"data")
        ds = DataSource(file_name="test.tsv")
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe
        state.series.append(SeriesConfig(x_column="x", y_column="y", source_file_index=0))

        removed = state.remove_file("test.tsv")

        assert removed == [0]
        assert len(state.series) == 0

    def test_remove_file_updates_series_indices(self, sample_dataframe, sample_dataframe2):
        """Test remove_file updates source_file_index for remaining series."""
        state = AppState()
        # Add two files
        state.uploaded_files["test.tsv"] = UploadedFile(name="test.tsv", content=b"data")
        state.uploaded_files["test2.tsv"] = UploadedFile(name="test2.tsv", content=b"data2")
        ds1 = DataSource(file_name="test.tsv")
        ds2 = DataSource(file_name="test2.tsv")
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        # Add series for second file (index 1)
        state.series.append(SeriesConfig(x_column="a", y_column="b", source_file_index=1))

        # Remove first file
        state.remove_file("test.tsv")

        # Series index should be updated from 1 to 0
        assert len(state.series) == 1
        assert state.series[0].source_file_index == 0
