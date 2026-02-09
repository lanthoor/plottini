"""Tests for CLI functionality."""

from click.testing import CliRunner

from plottini.cli import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Plottini" in result.output
    assert "User-friendly graph builder" in result.output


def test_version_command():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "Plottini version 0.3.0" in result.output


def test_render_help():
    """Test render command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["render", "--help"])
    assert result.exit_code == 0
    assert "Render graph without UI" in result.output
    assert "--config" in result.output
    assert "--output" in result.output
