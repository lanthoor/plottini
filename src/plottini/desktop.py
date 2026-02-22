"""Desktop launcher using PyWebView."""

from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path


def find_free_port() -> int:
    """Find an available port.

    Returns:
        An available port number
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


def _wait_for_server(url: str, max_retries: int = 5) -> bool:
    """Wait for server to be ready with exponential backoff.

    Args:
        url: URL to poll
        max_retries: Maximum number of retry attempts

    Returns:
        True if server is ready, False if timed out
    """
    delay = 0.5  # Initial delay in seconds
    for _ in range(max_retries):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(delay)
            delay *= 2  # Double the delay for next attempt
    return False


def start_desktop(port: int | None = None) -> None:
    """Launch Plottini desktop app.

    Args:
        port: Optional port number. If not provided, a free port will be found.
    """
    import webview

    port = port or find_free_port()
    url = f"http://localhost:{port}"

    # Store the streamlit process so we can terminate it on close
    streamlit_process: subprocess.Popen[bytes] | None = None

    def run_streamlit() -> None:
        nonlocal streamlit_process
        try:
            # Suppress all output by redirecting to devnull
            streamlit_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(Path(__file__).parent / "ui" / "app.py"),
                    "--server.port",
                    str(port),
                    "--server.headless",
                    "true",
                    "--server.runOnSave",
                    "false",
                    "--browser.gatherUsageStats",
                    "false",
                    "--global.developmentMode",
                    "false",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Failed to start Streamlit
            pass

    def on_closed() -> None:
        """Handle window close - terminate streamlit and exit."""
        if streamlit_process is not None:
            streamlit_process.terminate()
            try:
                streamlit_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()
        # Exit the process cleanly
        sys.exit(0)

    thread = threading.Thread(target=run_streamlit, daemon=True)
    thread.start()

    # Wait for Streamlit to be ready with exponential backoff
    if not _wait_for_server(url):
        print("Error: Failed to start Streamlit server", file=sys.stderr)
        sys.exit(1)

    window = webview.create_window(
        "Plottini",
        url,
        width=1400,
        height=900,
        min_size=(800, 600),
    )
    if window is None:
        print("Error: Failed to create window", file=sys.stderr)
        if streamlit_process is not None:
            streamlit_process.terminate()
        sys.exit(1)

    window.events.closed += on_closed
    webview.start()


__all__ = ["find_free_port", "start_desktop"]
