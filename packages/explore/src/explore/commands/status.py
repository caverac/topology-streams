"""``explore status <job-id>`` — check job status."""

from __future__ import annotations

import click
from explore._api_client import ApiClient
from explore._console import console


@click.command()
@click.argument("job_id")
def status(job_id: str) -> None:
    """Check the status of a recovery job.

    JOB_ID is the UUID returned by ``explore recover``.
    """
    client = ApiClient()
    result = client.get_job_status(job_id)

    console.print(f"[bold]Job:[/bold] {result['jobId']}")
    console.print(f"[bold]Stream:[/bold] {result.get('streamKey', 'N/A')}")
    console.print(f"[bold]Status:[/bold] {result['status']}")
    console.print(f"[bold]Created:[/bold] {result.get('createdAt', 'N/A')}")
    console.print(f"[bold]Updated:[/bold] {result.get('updatedAt', 'N/A')}")

    if result.get("error"):
        console.print(f"[bold red]Error:[/bold red] {result['error']}")
