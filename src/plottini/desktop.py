"""Desktop launcher using PyWebView."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


def find_free_port() -> int:
    """Find an available port.

    Returns:
        An available port number
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port: int = s.getsockname()[1]
        return port


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

    def on_closed() -> None:
        """Handle window close - terminate streamlit and exit."""
        if streamlit_process is not None:
            streamlit_process.terminate()
            try:
                streamlit_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()
        # Force exit the process
        os._exit(0)

    thread = threading.Thread(target=run_streamlit, daemon=True)
    thread.start()
    time.sleep(2)  # Wait for Streamlit to start

    window = webview.create_window(
        "Plottini",
        url,
        width=1400,
        height=900,
        min_size=(800, 600),
    )
    if window is not None:
        window.events.closed += on_closed
    webview.start()


__all__ = ["find_free_port", "start_desktop"]
