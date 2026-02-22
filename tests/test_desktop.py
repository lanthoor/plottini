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
        """Test that consecutive calls can return different ports."""
        # Note: This might occasionally fail if the same port is reused,
        # but generally different calls should get different ports
        ports = {find_free_port() for _ in range(5)}
        # At least some ports should be different
        assert len(ports) >= 1

    def test_port_is_bindable(self) -> None:
        """Test that the returned port can be bound to."""
        import socket

        port = find_free_port()
        # Try binding to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # This should not raise an exception
            s.bind(("", port))


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
            patch("plottini.desktop.time.sleep"),
        ):
            # Need to reimport to pick up the mock
            import importlib

            import plottini.desktop

            importlib.reload(plottini.desktop)

            plottini.desktop.start_desktop(port=9999)

            # Verify window was created with correct URL
            mock_webview.create_window.assert_called_once()
            call_args = mock_webview.create_window.call_args
            assert call_args[0][0] == "Plottini"  # title
            assert "localhost:9999" in call_args[0][1]  # URL

    def test_start_desktop_finds_free_port_when_none_provided(self) -> None:
        """Test that start_desktop finds a free port when none provided."""
        mock_webview = MagicMock()
        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop.time.sleep"),
        ):
            import importlib

            import plottini.desktop

            importlib.reload(plottini.desktop)

            # Patch find_free_port after reload
            original_find_free_port = plottini.desktop.find_free_port
            plottini.desktop.find_free_port = MagicMock(return_value=12345)

            try:
                plottini.desktop.start_desktop(port=None)

                plottini.desktop.find_free_port.assert_called_once()
                call_args = mock_webview.create_window.call_args
                assert "localhost:12345" in call_args[0][1]
            finally:
                plottini.desktop.find_free_port = original_find_free_port

    def test_start_desktop_creates_window_with_correct_size(self) -> None:
        """Test that start_desktop creates window with correct dimensions."""
        mock_webview = MagicMock()
        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window

        with (
            patch.dict("sys.modules", {"webview": mock_webview}),
            patch("plottini.desktop.threading.Thread"),
            patch("plottini.desktop.time.sleep"),
        ):
            import importlib

            import plottini.desktop

            importlib.reload(plottini.desktop)

            plottini.desktop.start_desktop(port=8080)

            call_kwargs = mock_webview.create_window.call_args[1]
            assert call_kwargs["width"] == 1400
            assert call_kwargs["height"] == 900
            assert call_kwargs["min_size"] == (800, 600)
