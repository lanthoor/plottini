"""Tests for UI state management."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from plottini.config.schema import AlignmentConfig, DerivedColumnConfig, FilterConfig
from plottini.core.dataframe import Column, DataFrame
from plottini.core.plotter import ChartType, SeriesConfig
from plottini.ui.state import AppState, DataSource, create_default_state


class TestAppState:
    """Tests for AppState class."""

    def test_default_state_creation(self):
        """Test AppState creates with sensible defaults."""
        state = AppState()

        assert state.loaded_files == []
        assert state.parsed_data == {}
        assert state.derived_columns == []
        assert state.filters == []
        assert state.alignment is None
        assert state.series == []
        assert state.current_figure is None
        assert state.error_message is None
        assert state.is_dirty is False

    def test_create_default_state_factory(self):
        """Test create_default_state factory function."""
        state = create_default_state()

        assert isinstance(state, AppState)
        assert state.plot_config.chart_type == ChartType.LINE
        assert state.plot_config.show_grid is True
        assert state.plot_config.show_legend is True

    def test_change_callback_notification(self):
        """Test callbacks are called when notify_change is invoked."""
        state = AppState()
        callback_count = [0]

        def callback() -> None:
            callback_count[0] += 1

        state.add_change_callback(callback)
        assert callback_count[0] == 0

        state.notify_change()
        assert callback_count[0] == 1

        state.notify_change()
        assert callback_count[0] == 2

    def test_multiple_callbacks(self):
        """Test multiple callbacks are all called."""
        state = AppState()
        results: list[str] = []

        state.add_change_callback(lambda: results.append("a"))
        state.add_change_callback(lambda: results.append("b"))
        state.add_change_callback(lambda: results.append("c"))

        state.notify_change()
        assert results == ["a", "b", "c"]

    def test_remove_change_callback(self):
        """Test removing a callback."""
        state = AppState()
        callback_count = [0]

        def callback() -> None:
            callback_count[0] += 1

        state.add_change_callback(callback)
        state.notify_change()
        assert callback_count[0] == 1

        state.remove_change_callback(callback)
        state.notify_change()
        assert callback_count[0] == 1  # Should not increment

    def test_callback_error_does_not_break_others(self):
        """Test that one failing callback doesn't prevent others."""
        state = AppState()
        results: list[str] = []

        def failing_callback() -> None:
            raise ValueError("Test error")

        state.add_change_callback(lambda: results.append("before"))
        state.add_change_callback(failing_callback)
        state.add_change_callback(lambda: results.append("after"))

        state.notify_change()  # Should not raise
        assert results == ["before", "after"]

    def test_is_dirty_flag(self):
        """Test is_dirty flag is set on notify_change."""
        state = AppState()
        assert state.is_dirty is False

        state.notify_change()
        assert state.is_dirty is True


class TestAppStateDataMethods:
    """Tests for data-related methods."""

    @pytest.fixture
    def sample_dataframe(self) -> DataFrame:
        """Create a sample DataFrame for testing."""
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
        path = Path("test.tsv")
        ds = DataSource(file_path=path)
        state.loaded_files.append(path)
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe

        columns = state.get_all_column_names()
        assert sorted(columns) == ["x", "y"]

    def test_get_all_column_names_multiple_files(self, sample_dataframe, sample_dataframe2):
        """Test get_all_column_names aggregates from multiple files."""
        state = AppState()
        path1 = Path("test.tsv")
        path2 = Path("test2.tsv")
        ds1 = DataSource(file_path=path1)
        ds2 = DataSource(file_path=path2)
        state.loaded_files.extend([path1, path2])
        state.data_sources.extend([ds1, ds2])
        state.parsed_data[ds1] = sample_dataframe
        state.parsed_data[ds2] = sample_dataframe2

        columns = state.get_all_column_names()
        assert sorted(columns) == ["x", "y", "z"]

    def test_get_dataframes_list_ordered(self, sample_dataframe, sample_dataframe2):
        """Test get_dataframes_list returns in order of data_sources."""
        state = AppState()
        path1 = Path("test.tsv")
        path2 = Path("test2.tsv")
        ds1 = DataSource(file_path=path1)
        ds2 = DataSource(file_path=path2)
        state.loaded_files.extend([path1, path2])
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
        path = Path("test.tsv")
        ds = DataSource(file_path=path)
        state.loaded_files.append(path)
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe
        state.derived_columns.append(DerivedColumnConfig(name="d", expression="x+y"))
        state.filters.append(FilterConfig(column="x", min=0.0))
        state.alignment = AlignmentConfig(enabled=True, column="x")
        state.series.append(SeriesConfig(x_column="x", y_column="y"))
        state.error_message = "test error"

        callback_called = [False]
        state.add_change_callback(lambda: callback_called.__setitem__(0, True))

        state.clear_data()

        assert state.loaded_files == []
        assert state.data_sources == []
        assert state.parsed_data == {}
        assert state.derived_columns == []
        assert state.filters == []
        assert state.alignment is None
        assert state.series == []
        assert state.error_message is None
        assert callback_called[0] is True


class TestAppStateErrorHandling:
    """Tests for error handling methods."""

    def test_set_error_notifies_callbacks(self):
        """Test error setting triggers callbacks."""
        state = AppState()
        callback_called = [False]
        state.add_change_callback(lambda: callback_called.__setitem__(0, True))

        state.set_error("Test error message")

        assert state.error_message == "Test error message"
        assert callback_called[0] is True

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
        path = Path("test.tsv")
        ds = DataSource(file_path=path)
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
        path = Path("test.tsv")
        ds = DataSource(file_path=path)
        state.parsed_data[ds] = sample_dataframe

        assert state.can_render() is False

    def test_can_render_true_with_both(self, sample_dataframe):
        """Test can_render returns True with data and series."""
        state = AppState()
        path = Path("test.tsv")
        ds = DataSource(file_path=path)
        state.parsed_data[ds] = sample_dataframe
        state.series.append(SeriesConfig(x_column="x", y_column="y"))

        assert state.can_render() is True

    def test_get_file_info_not_loaded(self):
        """Test get_file_info for file not in parsed_data."""
        state = AppState()
        info = state.get_file_info(Path("unknown.tsv"))

        assert info == "(not loaded)"

    def test_get_file_info_loaded(self, sample_dataframe):
        """Test get_file_info for loaded file."""
        state = AppState()
        path = Path("test.tsv")
        ds = DataSource(file_path=path)
        state.data_sources.append(ds)
        state.parsed_data[ds] = sample_dataframe

        info = state.get_file_info(path)
        assert info == "(2 columns, 3 rows)"
