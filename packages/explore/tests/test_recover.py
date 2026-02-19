"""Tests for the ``explore recover`` command (CLI arg parsing only, no network)."""

from click.testing import CliRunner
from explore.cli import cli


class TestRecoverArgParsing:
    """Tests for recover command argument validation."""

    def test_unknown_stream_fails(self) -> None:
        """An unknown stream name should produce an error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["recover", "nonexistent-stream"])
        assert result.exit_code != 0
        assert "Unknown stream" in result.output

    def test_help_shows_options(self) -> None:
        """``explore recover --help`` should list all options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["recover", "--help"])
        assert result.exit_code == 0
        assert "--sigma-threshold" in result.output
        assert "--n-neighbors" in result.output
        assert "--output-dir" in result.output
        assert "--force" in result.output

    def test_missing_stream_name_fails(self) -> None:
        """Omitting the stream name should produce a usage error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["recover"])
        assert result.exit_code != 0


class TestPlotArgParsing:
    """Tests for plot command argument validation."""

    def test_help_shows_options(self) -> None:
        """``explore plot --help`` should list all options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["plot", "--help"])
        assert result.exit_code == 0
        assert "--homology-dim" in result.output
        assert "--dpi" in result.output

    def test_missing_run_dir_fails(self) -> None:
        """Omitting the run directory should produce a usage error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["plot"])
        assert result.exit_code != 0
