"""Tests for the ``explore catalog`` command."""

from click.testing import CliRunner
from explore.cli import cli


class TestCatalogCommand:
    """CLI integration tests for the catalog command."""

    def test_exits_zero(self) -> None:
        """``explore catalog`` should exit with code 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["catalog"])
        assert result.exit_code == 0, result.output

    def test_lists_all_streams(self) -> None:
        """Output should mention all five stream names."""
        runner = CliRunner()
        result = runner.invoke(cli, ["catalog"])
        assert "GD-1" in result.output
        assert "Palomar 5" in result.output
        assert "Jhelum" in result.output
        assert "Orphan-Chenab" in result.output
        assert "ATLAS-Aliqa" in result.output

    def test_shows_coordinate_ranges(self) -> None:
        """Output should contain coordinate information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["catalog"])
        # GD-1 l range: 135 – 225
        assert "135" in result.output
        assert "225" in result.output
