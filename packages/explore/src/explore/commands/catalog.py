"""``explore catalog`` — list available streams."""

from __future__ import annotations

import click
from explore._console import console
from explore._types import STREAM_CATALOG
from rich.table import Table


@click.command()
def catalog() -> None:
    """List available streams with coordinates and metadata."""
    table = Table(title="Known Stellar Streams")
    table.add_column("Key", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("l range (deg)")
    table.add_column("b range (deg)")
    table.add_column("Expected members", justify="right")

    for stream in STREAM_CATALOG.values():
        table.add_row(
            stream.key,
            stream.name,
            f"{stream.l_min:.0f} – {stream.l_max:.0f}",
            f"{stream.b_min:.0f} – {stream.b_max:.0f}",
            f"~{stream.expected_members:,}",
        )

    console.print(table)
