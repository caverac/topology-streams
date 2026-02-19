"""``explore recover <stream-name>`` — end-to-end recovery pipeline."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import click
import numpy as np
from explore._api_client import ApiClient
from explore._console import console
from explore._constants import (
    CANDIDATE_MEMBERS_FILE,
    CANDIDATES_FILE,
    DEFAULT_N_NEIGHBORS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIGMA_THRESHOLD,
    GAIA_TABLE_FILE,
    METADATA_FILE,
    PERSISTENCE_FILE,
)
from explore._types import STREAM_CATALOG, KnownStream, RecoveryResult
from stream_finder.data import clean_phase_space, fetch_gaia_region, serialize_candidates
from stream_finder.streams import extract_stream_candidates
from stream_finder.topology import compute_density_filtration


def _is_api_mode() -> bool:
    """Check if the CLI is configured to use the AWS API backend."""
    return bool(os.environ.get("TOPOSTREAMS_API_URL"))


def _create_run_dir(output_dir: str, stream_key: str) -> tuple[Path, str]:
    """Create a timestamped run directory and return (run_dir, timestamp)."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(output_dir) / stream_key / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir, timestamp


def _poll_job(client: ApiClient, job_id: str, poll_interval: int = 10) -> None:
    """Poll an API job until it completes or fails.

    Parameters
    ----------
    client : ApiClient
        The API client instance.
    job_id : str
        The job ID to poll.
    poll_interval : int
        Seconds between polls.

    """
    console.print("Waiting for job to complete...")
    while True:
        status = client.get_job_status(job_id)
        job_status = status["status"]

        if job_status == "COMPLETED":
            console.print("  [green]Job completed![/green]")
            break
        if job_status == "FAILED":
            error = status.get("error", "Unknown error")
            raise click.ClickException(f"Job failed: {error}")
        console.print(f"  Status: {job_status} (polling every {poll_interval}s)")
        time.sleep(poll_interval)


def _download_results(client: ApiClient, job_id: str, run_dir: Path) -> dict[str, Any]:
    """Download job results and return the metadata dict."""
    console.print("Downloading results...")
    results = client.get_job_results(job_id)

    files = results.get("files", {})
    for filename, url in files.items():
        console.print(f"  Downloading {filename}...")
        with urlopen(url) as resp:
            data = resp.read()
        (run_dir / filename).write_bytes(data)

    metadata_path = run_dir / METADATA_FILE
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())

    return metadata


def _recover_via_api(
    stream_key: str,
    sigma_threshold: float,
    n_neighbors: int,
    output_dir: str,
) -> RecoveryResult:
    """Run recovery via the AWS API backend."""
    client = ApiClient()
    stream = STREAM_CATALOG[stream_key]

    # Submit job
    console.print(f"[bold]Submitting recovery job:[/bold] {stream.name}")
    result = client.submit_job(stream_key, n_neighbors, sigma_threshold)
    job_id = result["jobId"]
    console.print(f"  Job ID: [bold]{job_id}[/bold]")

    # Poll for completion
    _poll_job(client, job_id)

    # Download results
    run_dir, _ = _create_run_dir(output_dir, stream_key)
    metadata = _download_results(client, job_id, run_dir)

    console.print(f"\n[green]Done.[/green] Results saved to [bold]{run_dir}[/bold]")

    return RecoveryResult(
        stream=stream,
        n_stars=int(metadata.get("n_stars", 0)),
        n_clean=int(metadata.get("n_clean", 0)),
        n_candidates=int(metadata.get("n_candidates", 0)),
        run_dir=str(run_dir),
    )


def _fetch_and_prepare_data(stream: KnownStream, run_dir: Path) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Fetch Gaia data, save it, and prepare the phase-space point cloud.

    Returns
    -------
    tuple
        (points, clean_indices, n_stars, n_clean)

    """
    console.print(f"Fetching Gaia DR3 region: l=[{stream.l_min}, {stream.l_max}], b=[{stream.b_min}, {stream.b_max}]")
    table = fetch_gaia_region(stream.l_min, stream.l_max, stream.b_min, stream.b_max)
    n_stars = len(table)
    console.print(f"  fetched {n_stars:,} stars")

    # Save table as ECSV
    table.write(str(run_dir / GAIA_TABLE_FILE), format="ascii.ecsv", overwrite=True)

    # Convert to phase space using shared helper
    points, clean_indices = clean_phase_space(table)
    n_clean = len(points)
    console.print(f"  {n_clean:,} stars after NaN removal ({n_stars - n_clean} dropped)")

    return points, clean_indices, n_stars, n_clean


def _run_persistence_and_extract(
    points: np.ndarray,
    clean_indices: np.ndarray,
    n_neighbors: int,
    sigma_threshold: float,
    run_dir: Path,
) -> int:
    """Compute persistence, extract candidates, and save all outputs.

    Returns
    -------
    int
        Number of candidates found.

    """
    console.print(f"Computing density filtration (n_neighbors={n_neighbors}) ...")
    result = compute_density_filtration(points, n_neighbors=n_neighbors)

    # Save persistence data
    diagrams_dict: dict[str, Any] = {f"diagram_{i}": dgm for i, dgm in enumerate(result.diagrams)}
    save_arrays: dict[str, Any] = {
        "point_cloud": result.point_cloud,
        "clean_indices": clean_indices,
        "n_diagrams": np.asarray(len(result.diagrams)),
        **diagrams_dict,
    }
    np.savez(str(run_dir / PERSISTENCE_FILE), **save_arrays)

    # Extract candidates
    console.print(f"Extracting candidates (sigma={sigma_threshold}) ...")
    candidates = extract_stream_candidates(result, sigma_threshold=sigma_threshold)
    n_candidates = len(candidates)
    console.print(f"  found {n_candidates} candidate(s)")

    # Save candidates using shared serializer
    (run_dir / CANDIDATES_FILE).write_text(json.dumps(serialize_candidates(candidates), indent=2))

    members_arrays: dict[str, Any] = {f"candidate_{i}": c.member_indices for i, c in enumerate(candidates)}
    members_arrays["n_candidates"] = np.asarray(n_candidates)
    np.savez(str(run_dir / CANDIDATE_MEMBERS_FILE), **members_arrays)

    return n_candidates


def _recover_local(
    stream_key: str,
    sigma_threshold: float,
    n_neighbors: int,
    output_dir: str,
    force: bool,
) -> RecoveryResult:
    """Run recovery locally (original behavior)."""
    stream = STREAM_CATALOG[stream_key]
    console.print(f"[bold]Recovering stream:[/bold] {stream.name}")

    # Prepare run directory
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(output_dir) / stream_key / timestamp
    if run_dir.exists() and not force:
        raise click.ClickException(f"Run directory already exists: {run_dir}  (use --force to overwrite)")
    run_dir.mkdir(parents=True, exist_ok=True)

    # Fetch and prepare data
    points, clean_indices, n_stars, n_clean = _fetch_and_prepare_data(stream, run_dir)

    # Compute persistence and extract candidates
    n_candidates = _run_persistence_and_extract(points, clean_indices, n_neighbors, sigma_threshold, run_dir)

    # Save metadata
    metadata = {
        "stream": stream_key,
        "stream_name": stream.name,
        "timestamp": timestamp,
        "n_stars": n_stars,
        "n_clean": n_clean,
        "n_candidates": n_candidates,
        "sigma_threshold": sigma_threshold,
        "n_neighbors": n_neighbors,
        "l_range": [stream.l_min, stream.l_max],
        "b_range": [stream.b_min, stream.b_max],
    }
    (run_dir / METADATA_FILE).write_text(json.dumps(metadata, indent=2))

    console.print(f"\n[green]Done.[/green] Results saved to [bold]{run_dir}[/bold]")

    return RecoveryResult(
        stream=stream,
        n_stars=n_stars,
        n_clean=n_clean,
        n_candidates=n_candidates,
        run_dir=str(run_dir),
    )


@click.command()
@click.argument("stream_name")
@click.option(
    "--sigma-threshold",
    default=DEFAULT_SIGMA_THRESHOLD,
    show_default=True,
    help="Sigma threshold for candidate extraction.",
)
@click.option(
    "--n-neighbors",
    default=DEFAULT_N_NEIGHBORS,
    show_default=True,
    help="Number of nearest neighbors for density estimation.",
)
@click.option(
    "--output-dir", default=str(DEFAULT_OUTPUT_DIR), show_default=True, type=click.Path(), help="Root output directory."
)
@click.option("--force", is_flag=True, help="Overwrite existing run directory.")
def recover(
    stream_name: str,
    sigma_threshold: float,
    n_neighbors: int,
    output_dir: str,
    force: bool,
) -> None:
    """Run the end-to-end recovery pipeline for STREAM_NAME.

    STREAM_NAME must match a key from ``explore catalog`` (e.g. gd-1).

    When TOPOSTREAMS_API_URL is set, submits the job to the AWS backend.
    Otherwise, runs the pipeline locally.
    """
    key = stream_name.lower()
    if key not in STREAM_CATALOG:
        available = ", ".join(STREAM_CATALOG)
        raise click.BadParameter(f"Unknown stream {stream_name!r}. Available: {available}", param_hint="STREAM_NAME")

    if _is_api_mode():
        _recover_via_api(key, sigma_threshold, n_neighbors, output_dir)
    else:
        _recover_local(key, sigma_threshold, n_neighbors, output_dir, force)
