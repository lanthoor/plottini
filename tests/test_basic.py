"""Basic tests for plottini package."""

import plottini


def test_version():
    """Test that version is accessible."""
    assert plottini.__version__ == "2026.2.3"


def test_license():
    """Test that license is set."""
    assert plottini.__license__ == "MIT"


def test_author():
    """Test that author is set."""
    assert plottini.__author__ == "Lallu Anthoor"
