"""Stream candidate extraction from persistence diagrams."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import KDTree
from stream_finder._gpu import available as _gpu_available
from stream_finder.topology import PersistenceResult

if _gpu_available:
    from topostreams_cuda.radius_query import gpu_radius_query
else:

    def gpu_radius_query(*_args: object, **_kwargs: object) -> object:  # type: ignore[misc]
        """Stub: GPU not available."""
        raise RuntimeError("GPU not available")


@dataclass
class StreamCandidate:
    """A stream candidate identified from topological analysis.

    Attributes
    ----------
    member_indices : NDArray
        Indices into the original point cloud for member stars.
    persistence : float
        Lifetime of the topological feature (death - birth).
    birth : float
        Birth scale of the feature.
    death : float
        Death scale of the feature.
    homology_dim : int
        Homology dimension (0 = connected component, 1 = loop).

    """

    member_indices: NDArray[np.intp]
    persistence: float
    birth: float
    death: float
    homology_dim: int


def _radius_query(point_cloud: NDArray[np.float64], query: NDArray[np.float64], radius: float) -> list[int]:
    """Perform radius query using GPU or CPU fallback."""
    if _gpu_available:
        indices = gpu_radius_query(point_cloud, query, radius)
        result: list[int] = indices.tolist()
        return result

    tree = KDTree(point_cloud)
    cpu_result: list[int] = tree.query_ball_point(query, r=radius)
    return cpu_result


def _compute_significance_threshold(
    lifetimes: NDArray[np.float64],
    sigma_threshold: float,
) -> float:
    """Compute persistence threshold from lifetime statistics."""
    mean_life = float(np.mean(lifetimes))
    std_life = float(np.std(lifetimes))
    return mean_life + sigma_threshold * std_life


def _build_candidate(
    diagram: NDArray[np.float64],
    point_cloud: NDArray[np.float64],
    idx: int,
    homology_dim: int,
) -> StreamCandidate:
    """Build a single StreamCandidate from a diagram index."""
    birth = float(diagram[idx, 0])
    death = float(diagram[idx, 1])
    members = _radius_query(point_cloud, point_cloud[idx], death)
    return StreamCandidate(
        member_indices=np.array(members, dtype=np.intp),
        persistence=death - birth,
        birth=birth,
        death=death,
        homology_dim=homology_dim,
    )


def extract_stream_candidates(
    result: PersistenceResult,
    persistence_threshold: float | None = None,
    sigma_threshold: float = 3.0,
    homology_dim: int = 0,
) -> list[StreamCandidate]:
    """Extract stream candidates from a persistence result.

    Identifies topological features with persistence significantly above
    the noise floor. For H0, these correspond to clusters of stars that
    remain connected over a wide range of scales — the signature of a
    kinematically coherent stream.

    Parameters
    ----------
    result : PersistenceResult
        Output from compute_persistence().
    persistence_threshold : float, optional
        Absolute persistence threshold. If None, uses sigma_threshold.
    sigma_threshold : float
        Number of standard deviations above the mean persistence to
        consider a feature significant. Default 3.0.
    homology_dim : int
        Which homology dimension to extract from. Default 0.

    Returns
    -------
    list of StreamCandidate
        Stream candidates sorted by persistence (highest first).

    """
    diagram = result.diagrams[homology_dim]

    # Filter out features with any infinite value (e.g. essential classes)
    finite_mask = np.all(np.isfinite(diagram), axis=1)
    finite_dgm = diagram[finite_mask]
    finite_indices = np.where(finite_mask)[0]

    if len(finite_dgm) == 0:
        return []

    lifetimes = finite_dgm[:, 1] - finite_dgm[:, 0]

    if persistence_threshold is None:
        persistence_threshold = _compute_significance_threshold(lifetimes, sigma_threshold)

    significant_mask = lifetimes > persistence_threshold
    significant_indices = finite_indices[significant_mask]

    candidates = [_build_candidate(diagram, result.point_cloud, idx, homology_dim) for idx in significant_indices]

    # Sort by persistence, highest first
    candidates.sort(key=lambda c: c.persistence, reverse=True)
    return candidates
