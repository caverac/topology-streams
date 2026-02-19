"""Data ingestion from Gaia DR3 and pre-processed stream catalogs."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from astropy.table import Table


# Phase-space columns used for persistent homology
PHASE_SPACE_COLS = ["ra", "dec", "pmra", "pmdec", "parallax"]


@dataclass(frozen=True)
class GaiaQualityFilter:
    """Quality filters for Gaia DR3 queries.

    Attributes
    ----------
    parallax_over_error_min : float
        Minimum parallax signal-to-noise ratio.
    ruwe_max : float
        Maximum RUWE for astrometric quality.
    mag_limit : float
        Faint magnitude limit in G band.

    """

    parallax_over_error_min: float = 5.0
    ruwe_max: float = 1.4
    mag_limit: float = 20.0


def _run_gaia_query(query: str) -> Table:
    """Execute an async Gaia ADQL query and return the results."""
    _gaia_mod = importlib.import_module("astroquery.gaia")
    gaia_cls = _gaia_mod.Gaia

    job = gaia_cls.launch_job_async(query)
    return job.get_results()


def clean_phase_space(table: Table) -> tuple[NDArray[np.float64], NDArray[np.intp]]:
    """Convert an astropy table to a cleaned phase-space array.

    Drops rows with NaN values in the phase-space columns.

    Parameters
    ----------
    table : astropy.table.Table
        Input table with astrometric columns.

    Returns
    -------
    tuple
        (points, clean_indices) where points has shape (n_clean, n_features)
        and clean_indices maps rows back to the original table.

    """
    data = np.column_stack([np.asarray(table[c], dtype=np.float64) for c in PHASE_SPACE_COLS])
    clean_mask = ~np.any(np.isnan(data), axis=1)
    clean_indices = np.where(clean_mask)[0]
    return data[clean_mask], clean_indices


def serialize_candidates(candidates: Sequence[object]) -> list[dict[str, object]]:
    """Serialize stream candidates to a list of JSON-friendly dicts.

    Parameters
    ----------
    candidates : list
        StreamCandidate objects with persistence, birth, death,
        homology_dim, and member_indices attributes.

    Returns
    -------
    list[dict]
        Serialized candidate records.

    """
    return [
        {
            "persistence": c.persistence,  # type: ignore[attr-defined]
            "birth": c.birth,  # type: ignore[attr-defined]
            "death": c.death,  # type: ignore[attr-defined]
            "homology_dim": c.homology_dim,  # type: ignore[attr-defined]
            "n_members": len(c.member_indices),  # type: ignore[attr-defined]
        }
        for c in candidates
    ]


def fetch_gaia_region(
    l_min: float,
    l_max: float,
    b_min: float,
    b_max: float,
    quality: GaiaQualityFilter | None = None,
) -> Table:
    """Fetch a rectangular region from Gaia DR3 via ADQL.

    Parameters
    ----------
    l_min, l_max : float
        Galactic longitude range in degrees.
    b_min, b_max : float
        Galactic latitude range in degrees.
    quality : GaiaQualityFilter, optional
        Quality filters. Defaults to standard cuts.

    Returns
    -------
    astropy.table.Table
        Table with columns: source_id, ra, dec, pmra, pmdec, parallax,
        radial_velocity, phot_g_mean_mag, bp_rp.

    """
    if quality is None:
        quality = GaiaQualityFilter()
    query = f"""
        SELECT source_id, ra, dec, pmra, pmdec, parallax,
               radial_velocity, phot_g_mean_mag, bp_rp
        FROM gaiadr3.gaia_source
        WHERE l BETWEEN {l_min} AND {l_max}
          AND b BETWEEN {b_min} AND {b_max}
          AND parallax_over_error > {quality.parallax_over_error_min}
          AND ruwe < {quality.ruwe_max}
          AND phot_g_mean_mag < {quality.mag_limit}
          AND pmra IS NOT NULL
          AND pmdec IS NOT NULL
    """
    return _run_gaia_query(query)


def table_to_phase_space(table: Table, cols: list[str] | None = None) -> NDArray[np.float64]:
    """Convert an astropy Table to a phase-space numpy array.

    Parameters
    ----------
    table : astropy.table.Table
        Input table with astrometric columns.
    cols : list of str, optional
        Columns to include. Defaults to PHASE_SPACE_COLS.

    Returns
    -------
    NDArray
        Array of shape (n_stars, n_features).

    """
    if cols is None:
        cols = PHASE_SPACE_COLS

    data = np.column_stack([np.asarray(table[c], dtype=np.float64) for c in cols])

    # Drop rows with NaN
    mask = ~np.any(np.isnan(data), axis=1)
    result: NDArray[np.float64] = data[mask]
    return result


def load_starstream_members(filepath: str) -> NDArray[np.int64]:
    """Load StarStream DR member star source IDs from a file.

    Parameters
    ----------
    filepath : str
        Path to the StarStream DR catalog file.

    Returns
    -------
    NDArray
        Array of Gaia DR3 source_id values.

    """
    return np.loadtxt(filepath, dtype=np.int64)
