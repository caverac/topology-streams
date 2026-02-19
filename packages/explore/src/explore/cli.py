"""CLI entry point for the explore tool."""

from __future__ import annotations

import click
from explore.commands.catalog import catalog
from explore.commands.plot import plot
from explore.commands.recover import recover


@click.group()
@click.version_option(package_name="explore")
def cli() -> None:
    """Test persistent homology recovery of known stellar streams."""


cli.add_command(catalog)
cli.add_command(recover)
cli.add_command(plot)

# API-dependent commands (only work when TOPOSTREAMS_API_URL is set)
try:
    from explore.commands.jobs import jobs
    from explore.commands.status import status

    cli.add_command(status)
    cli.add_command(jobs)
except ImportError:
    pass
