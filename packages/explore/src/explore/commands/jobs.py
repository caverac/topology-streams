"""``explore jobs`` — list recent jobs (placeholder using catalog endpoint)."""

from __future__ import annotations

import click
from explore._api_client import ApiClient
from explore._console import console
from rich.table import Table


@click.command()
def jobs() -> None:
    """List recent recovery jobs.

    Requires TOPOSTREAMS_API_URL to be set. Shows available streams
    from the remote catalog.
    """
    client = ApiClient()
    result = client.get_catalog()

    streams = result.get("streams", [])
    if not streams:
        console.print("[yellow]No streams found in remote catalog.[/yellow]")
        return

    table = Table(title="Available Streams (Remote Catalog)")
    table.add_column("Key", style="bold")
    table.add_column("Name")
    table.add_column("l range")
    table.add_column("b range")
    table.add_column("Expected Members", justify="right")

    for s in streams:
        table.add_row(
            s["key"],
            s["name"],
            f"[{s['lMin']:.0f}, {s['lMax']:.0f}]",
            f"[{s['bMin']:.0f}, {s['bMax']:.0f}]",
            str(s["expectedMembers"]),
        )

    console.print(table)
