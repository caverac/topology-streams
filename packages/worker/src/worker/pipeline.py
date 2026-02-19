"""Full stream recovery pipeline — mirrors explore/commands/recover.py logic."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from stream_finder.data import clean_phase_space, fetch_gaia_region, serialize_candidates
from stream_finder.streams import extract_stream_candidates
from stream_finder.topology import compute_density_filtration
from worker.s3_io import save_npz_to_bytes, save_table_to_bytes, upload_results

logger = logging.getLogger(__name__)

# Stream catalog (mirrors explore._types.STREAM_CATALOG)
STREAM_CATALOG = {
    "gd-1": {"name": "GD-1", "l_min": 135.0, "l_max": 225.0, "b_min": 30.0, "b_max": 75.0, "expected_members": 1689},
    "palomar-5": {
        "name": "Palomar 5",
        "l_min": 0.0,
        "l_max": 10.0,
        "b_min": 40.0,
        "b_max": 50.0,
        "expected_members": 500,
    },
    "jhelum": {
        "name": "Jhelum",
        "l_min": 335.0,
        "l_max": 360.0,
        "b_min": -55.0,
        "b_max": -35.0,
        "expected_members": 300,
    },
    "orphan-chenab": {
        "name": "Orphan-Chenab",
        "l_min": 160.0,
        "l_max": 260.0,
        "b_min": 30.0,
        "b_max": 70.0,
        "expected_members": 800,
    },
    "atlas-aliqa-uma": {
        "name": "ATLAS-Aliqa Uma",
        "l_min": 225.0,
        "l_max": 270.0,
        "b_min": 25.0,
        "b_max": 55.0,
        "expected_members": 200,
    },
}


@dataclass
class _FetchResult:
    """Result of fetching and cleaning Gaia data."""

    table: Any
    points: NDArray[np.float64]
    clean_indices: NDArray[np.intp]
    n_stars: int
    n_clean: int


def _fetch_and_clean_data(stream: dict[str, Any]) -> _FetchResult:
    """Fetch a Gaia region and clean NaN rows from phase-space columns.

    Parameters
    ----------
    stream : dict
        Stream catalog entry with l_min, l_max, b_min, b_max keys.

    Returns
    -------
    _FetchResult
        Fetched table, cleaned point cloud, clean row indices, and counts.

    """
    logger.info(
        "Fetching Gaia DR3 region: l=[%s, %s], b=[%s, %s]",
        stream["l_min"],
        stream["l_max"],
        stream["b_min"],
        stream["b_max"],
    )
    table = fetch_gaia_region(stream["l_min"], stream["l_max"], stream["b_min"], stream["b_max"])
    n_stars = len(table)
    logger.info("Fetched %d stars", n_stars)

    points, clean_indices = clean_phase_space(table)
    n_clean = len(points)
    logger.info("%d stars after NaN removal", n_clean)

    return _FetchResult(
        table=table,
        points=points,
        clean_indices=clean_indices,
        n_stars=n_stars,
        n_clean=n_clean,
    )


def _compute_persistence(points: NDArray[np.float64], n_neighbors: int) -> Any:
    """Run density filtration on the cleaned point cloud.

    Parameters
    ----------
    points : NDArray
        Cleaned phase-space point cloud.
    n_neighbors : int
        kNN parameter for density estimation.

    Returns
    -------
    object
        Filtration result containing diagrams and point_cloud.

    """
    logger.info("Computing density filtration (n_neighbors=%d)", n_neighbors)
    return compute_density_filtration(points, n_neighbors=n_neighbors)


def _extract_and_serialize_candidates(
    result: Any,
    clean_indices: NDArray[np.intp],
    sigma_threshold: float,
) -> tuple[list[Any], str, bytes, bytes]:
    """Extract stream candidates and serialize to JSON and NPZ bytes.

    Parameters
    ----------
    result : object
        Filtration result from _compute_persistence.
    clean_indices : NDArray
        Indices of rows that survived NaN cleaning.
    sigma_threshold : float
        Sigma threshold for candidate extraction.

    Returns
    -------
    tuple
        (candidates list, candidates_json, persistence_bytes, members_bytes).

    """
    logger.info("Extracting candidates (sigma=%s)", sigma_threshold)
    candidates = extract_stream_candidates(result, sigma_threshold=sigma_threshold)
    n_candidates = len(candidates)
    logger.info("Found %d candidate(s)", n_candidates)

    diagrams_dict = {f"diagram_{i}": dgm for i, dgm in enumerate(result.diagrams)}
    persistence_arrays = {
        "point_cloud": result.point_cloud,
        "clean_indices": clean_indices,
        "n_diagrams": np.asarray(len(result.diagrams)),
        **diagrams_dict,
    }
    persistence_bytes = save_npz_to_bytes(**persistence_arrays)

    candidates_json = json.dumps(serialize_candidates(candidates), indent=2)

    members_dict = {f"candidate_{i}": c.member_indices for i, c in enumerate(candidates)}
    members_dict["n_candidates"] = np.asarray(n_candidates)
    members_bytes = save_npz_to_bytes(**members_dict)

    return candidates, candidates_json, persistence_bytes, members_bytes


@dataclass
class _PipelineContext:
    """Bundled pipeline parameters for metadata construction."""

    stream_key: str
    stream: dict[str, Any]
    job_id: str
    sigma_threshold: float
    n_neighbors: int


def _build_metadata(ctx: _PipelineContext, fetch_result: _FetchResult, n_candidates: int) -> str:
    """Build the metadata JSON string for the pipeline run.

    Parameters
    ----------
    ctx : _PipelineContext
        Pipeline parameters.
    fetch_result : _FetchResult
        Fetched data containing star counts.
    n_candidates : int
        Number of extracted candidates.

    Returns
    -------
    str
        JSON-encoded metadata string.

    """
    return json.dumps(
        {
            "stream": ctx.stream_key,
            "stream_name": ctx.stream["name"],
            "job_id": ctx.job_id,
            "n_stars": fetch_result.n_stars,
            "n_clean": fetch_result.n_clean,
            "n_candidates": n_candidates,
            "sigma_threshold": ctx.sigma_threshold,
            "n_neighbors": ctx.n_neighbors,
            "l_range": [ctx.stream["l_min"], ctx.stream["l_max"]],
            "b_range": [ctx.stream["b_min"], ctx.stream["b_max"]],
        },
        indent=2,
    )


def run_pipeline(
    bucket_name: str,
    job_id: str,
    stream_key: str,
    n_neighbors: int = 32,
    sigma_threshold: float = 3.0,
) -> None:
    """Run the full stream recovery pipeline and upload results to S3.

    Parameters
    ----------
    bucket_name : str
        S3 bucket for result storage.
    job_id : str
        Unique job identifier.
    stream_key : str
        Stream catalog key (e.g. "gd-1").
    n_neighbors : int
        kNN parameter.
    sigma_threshold : float
        Sigma threshold for candidate extraction.

    """
    stream = STREAM_CATALOG[stream_key]
    logger.info("Starting pipeline for %s (job=%s)", stream["name"], job_id)

    ctx = _PipelineContext(
        stream_key=stream_key,
        stream=stream,
        job_id=job_id,
        sigma_threshold=sigma_threshold,
        n_neighbors=n_neighbors,
    )

    # 1. Fetch and clean Gaia data
    fetch_result = _fetch_and_clean_data(stream)

    # 2. Compute persistence
    filtration = _compute_persistence(fetch_result.points, n_neighbors)

    # 3. Extract candidates and serialize
    candidates, candidates_json, persistence_bytes, members_bytes = _extract_and_serialize_candidates(
        filtration, fetch_result.clean_indices, sigma_threshold
    )

    # 4. Build metadata
    metadata = _build_metadata(ctx, fetch_result, len(candidates))

    # 5. Upload to S3
    table_bytes = save_table_to_bytes(fetch_result.table)
    upload_results(
        bucket_name,
        job_id,
        {
            "gaia_table.ecsv": table_bytes,
            "persistence.npz": persistence_bytes,
            "candidates.json": candidates_json,
            "candidate_members.npz": members_bytes,
            "metadata.json": metadata,
        },
    )

    logger.info("Pipeline complete for job %s", job_id)
