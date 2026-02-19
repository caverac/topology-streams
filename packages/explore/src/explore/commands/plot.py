"""``explore plot <run-dir>`` — generate plots from a saved recovery run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
import matplotlib.pyplot as plt
import numpy as np
from astropy.table import Table as AstropyTable
from explore._console import console
from explore._constants import (
    CANDIDATE_MEMBERS_FILE,
    CANDIDATES_FILE,
    GAIA_TABLE_FILE,
    PERSISTENCE_DIAGRAM_FILE,
    PERSISTENCE_FILE,
    SKY_MAP_FILE,
)
from sklearn.preprocessing import StandardScaler
from stream_finder.streams import StreamCandidate
from stream_finder.topology import PersistenceResult
from stream_finder.visualization import plot_persistence_diagram, plot_sky_candidates


def _load_persistence_data(run: Path, homology_dim: int) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Load persistence diagrams, point cloud, and clean indices from a run directory.

    Returns
    -------
    tuple
        (diagrams, point_cloud, clean_indices)

    """
    persistence_path = run / PERSISTENCE_FILE
    if not persistence_path.exists():
        raise click.ClickException(f"Missing {PERSISTENCE_FILE} in {run}")

    npz = np.load(str(persistence_path))
    n_diagrams = int(npz["n_diagrams"])
    diagrams = [npz[f"diagram_{i}"] for i in range(n_diagrams)]
    point_cloud = npz["point_cloud"]
    clean_indices = npz["clean_indices"]

    if homology_dim >= n_diagrams:
        raise click.ClickException(f"Requested H{homology_dim} but only H0..H{n_diagrams - 1} available.")

    return diagrams, point_cloud, clean_indices


def _load_candidates(
    run: Path,
) -> tuple[list[dict[str, Any]], list[np.ndarray]]:
    """Load candidate metadata and member index arrays from a run directory.

    Returns
    -------
    tuple
        (candidates_meta, member_arrays)

    """
    candidates_json_path = run / CANDIDATES_FILE
    members_path = run / CANDIDATE_MEMBERS_FILE

    candidates_meta: list[dict[str, Any]] = []
    member_arrays: list[np.ndarray] = []
    if candidates_json_path.exists() and members_path.exists():
        candidates_meta = json.loads(candidates_json_path.read_text())
        members_npz = np.load(str(members_path))
        n_cand = int(members_npz["n_candidates"])
        member_arrays = [members_npz[f"candidate_{i}"] for i in range(n_cand)]

    return candidates_meta, member_arrays


def _build_persistence_result(diagrams: list[np.ndarray], point_cloud: np.ndarray) -> PersistenceResult:
    """Reconstruct a PersistenceResult with a dummy scaler for plotting."""
    scaler = StandardScaler()
    scaler.mean_ = np.zeros(point_cloud.shape[1])
    scaler.scale_ = np.ones(point_cloud.shape[1])
    scaler.var_ = np.ones(point_cloud.shape[1])
    scaler.n_features_in_ = point_cloud.shape[1]
    return PersistenceResult(diagrams=diagrams, point_cloud=point_cloud, scaler=scaler)


def _build_stream_candidates(
    candidates_meta: list[dict[str, Any]],
    member_arrays: list[np.ndarray],
) -> list[StreamCandidate]:
    """Reconstruct StreamCandidate objects from saved metadata and member arrays."""
    return [
        StreamCandidate(
            member_indices=member_arrays[i],
            persistence=float(cm["persistence"]),
            birth=float(cm["birth"]),
            death=float(cm["death"]),
            homology_dim=int(cm["homology_dim"]),
        )
        for i, cm in enumerate(candidates_meta)
        if i < len(member_arrays)
    ]


def _save_sky_map(
    run: Path,
    candidates: list[StreamCandidate],
    clean_indices: np.ndarray,
    dpi: int,
) -> None:
    """Generate and save the sky map if the Gaia table and candidates are available."""
    table_path = run / GAIA_TABLE_FILE
    if table_path.exists() and candidates:
        gaia_table = AstropyTable.read(str(table_path), format="ascii.ecsv")
        ra = np.asarray(gaia_table["ra"], dtype=np.float64)
        dec = np.asarray(gaia_table["dec"], dtype=np.float64)

        mapped_candidates = [
            StreamCandidate(
                member_indices=clean_indices[c.member_indices],
                persistence=c.persistence,
                birth=c.birth,
                death=c.death,
                homology_dim=c.homology_dim,
            )
            for c in candidates
        ]

        fig_sky, _ = plot_sky_candidates(ra, dec, mapped_candidates)
        sky_path = run / SKY_MAP_FILE
        fig_sky.savefig(str(sky_path), dpi=dpi, bbox_inches="tight")
        console.print(f"Saved sky map → [bold]{sky_path}[/bold]")
    elif not table_path.exists():
        console.print(f"[yellow]Skipping sky map:[/yellow] {GAIA_TABLE_FILE} not found")
    else:
        console.print("[yellow]Skipping sky map:[/yellow] no candidates to plot")


@click.command()
@click.argument("run_dir", type=click.Path(exists=True))
@click.option("--homology-dim", default=0, show_default=True, help="Homology dimension to plot.")
@click.option("--dpi", default=150, show_default=True, help="DPI for saved figures.")
def plot(run_dir: str, homology_dim: int, dpi: int) -> None:
    """Generate persistence diagram and sky map from a saved run.

    RUN_DIR is the path to a recovery run directory (e.g. runs/gd-1/<timestamp>/).
    """
    run = Path(run_dir)

    diagrams, point_cloud, clean_indices = _load_persistence_data(run, homology_dim)
    candidates_meta, member_arrays = _load_candidates(run)

    result = _build_persistence_result(diagrams, point_cloud)
    candidates = _build_stream_candidates(candidates_meta, member_arrays)

    # Persistence diagram
    fig_pd, _ = plot_persistence_diagram(result, homology_dim=homology_dim)
    pd_path = run / PERSISTENCE_DIAGRAM_FILE
    fig_pd.savefig(str(pd_path), dpi=dpi, bbox_inches="tight")
    console.print(f"Saved persistence diagram → [bold]{pd_path}[/bold]")

    # Sky map
    _save_sky_map(run, candidates, clean_indices, dpi)

    # Close figures
    plt.close("all")
