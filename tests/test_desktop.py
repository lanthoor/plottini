"""Tests for desktop launcher module."""

from unittest.mock import MagicMock, patch

from plottini.desktop import find_free_port


class TestFindFreePort:
    """Tests for find_free_port function."""

    def test_returns_valid_port(self) -> None:
        """Test that find_free_port returns a valid port number."""
        port = find_free_port()
        assert isinstance(port, int)
        assert 1 <= port <= 65535

    def test_returns_different_ports(self) -> None:
        """Test that consecutive calls return different ports."""
        ports = {find_free_port() for _ in range(5)}
        # All 5 calls should return different ports
        assert len(ports) == 5

    def test_port_is_bindable(self) -> None:
        """Test that the returned port can be bound to localhost."""
        import socket

        port = find_free_port()
        # Try binding to the port on localhost
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # This should not raise an exception
            s.bind(("127.0.0.1", port))


class TestStartDesktop:
    """Tests for start_desktop function (mocked)."""

    def test_start_desktop_uses_provided_port(self) -> None:
        """Test that start_desktop uses the provided port."""
        mock_webview = MagicMock()
        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop._wait_for_server", return_value=True),
        ):
            from plottini.desktop import start_desktop

            start_desktop(port=9999)

            # Verify window was created with correct URL
            mock_webview.create_window.assert_called_once()
            call_args = mock_webview.create_window.call_args
            assert call_args[0][0] == "Plottini"  # title
            assert "localhost:9999" in call_args[0][1]  # URL
            mock_webview.start.assert_called_once()

    def test_start_desktop_finds_free_port_when_none_provided(self) -> None:
        """Test that start_desktop finds a free port when none provided."""
        mock_webview = MagicMock()
        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop._wait_for_server", return_value=True),
            patch("plottini.desktop.find_free_port", return_value=12345),
        ):
            from plottini.desktop import start_desktop

            start_desktop(port=None)

            call_args = mock_webview.create_window.call_args
            assert "localhost:12345" in call_args[0][1]
            mock_webview.start.assert_called_once()

    def test_start_desktop_creates_window_with_correct_size(self) -> None:
        """Test that start_desktop creates window with correct dimensions."""
        mock_webview = MagicMock()
        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop._wait_for_server", return_value=True),
        ):
            from plottini.desktop import start_desktop

            start_desktop(port=8080)

            call_kwargs = mock_webview.create_window.call_args[1]
            assert call_kwargs["width"] == 1400
            assert call_kwargs["height"] == 900
            assert call_kwargs["min_size"] == (800, 600)
            mock_webview.start.assert_called_once()

    def test_start_desktop_exits_if_window_is_none(self) -> None:
        """Test that start_desktop exits if window creation fails."""
        mock_webview = MagicMock()
        mock_webview.create_window.return_value = None

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop._wait_for_server", return_value=True),
            patch("plottini.desktop.sys.exit", side_effect=SystemExit(1)) as mock_exit,
        ):
            from plottini.desktop import start_desktop

            try:
                start_desktop(port=8080)
            except SystemExit:
                pass

            mock_exit.assert_called_once_with(1)
            mock_webview.start.assert_not_called()

    def test_start_desktop_exits_if_server_fails_to_start(self) -> None:
        """Test that start_desktop exits if Streamlit fails to start."""
        mock_webview = MagicMock()

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop._wait_for_server", return_value=False),
            patch("plottini.desktop.sys.exit", side_effect=SystemExit(1)) as mock_exit,
        ):
            from plottini.desktop import start_desktop

            try:
                start_desktop(port=8080)
            except SystemExit:
                pass

            mock_exit.assert_called_once_with(1)
            mock_webview.create_window.assert_not_called()
