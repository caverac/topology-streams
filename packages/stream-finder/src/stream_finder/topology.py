"""Persistent homology computation on phase-space point clouds."""

from __future__ import annotations

import importlib
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from stream_finder._gpu import available as _gpu_available

if _gpu_available:
    from topostreams_cuda.density import gpu_density_filtration
    from topostreams_cuda.knn import gpu_knn
    from topostreams_cuda.persistence import gpu_persistence_h0
else:

    def gpu_knn(*_args: object, **_kwargs: object) -> object:  # type: ignore[misc]
        """Stub: GPU not available."""
        raise RuntimeError("GPU not available")

    def gpu_density_filtration(*_args: object, **_kwargs: object) -> object:  # type: ignore[misc]
        """Stub: GPU not available."""
        raise RuntimeError("GPU not available")

    def gpu_persistence_h0(*_args: object, **_kwargs: object) -> object:  # type: ignore[misc]
        """Stub: GPU not available."""
        raise RuntimeError("GPU not available")


@dataclass
class PersistenceResult:
    """Result of a persistent homology computation.

    Attributes
    ----------
    diagrams : list of NDArray
        Persistence diagrams for each homology dimension.
        Each array has shape (n_features, 2) with columns (birth, death).
    point_cloud : NDArray
        The (scaled) input point cloud.
    scaler : StandardScaler
        The fitted scaler, for inverse-transforming back to original units.

    """

    diagrams: list[NDArray[np.float64]]
    point_cloud: NDArray[np.float64]
    scaler: StandardScaler


def _build_edge_list(
    n_pts: int,
    k: int,
    indices: NDArray[np.intp],
    filtration_values: NDArray[np.float64],
) -> tuple[NDArray[np.int32], NDArray[np.int32], NDArray[np.float64]]:
    """Build a deduplicated edge list from kNN indices."""
    edge_src_list: list[int] = []
    edge_dst_list: list[int] = []
    edge_filt_list: list[float] = []
    seen: set[tuple[int, int]] = set()
    for i in range(n_pts):
        for j_idx in range(k):
            j = int(indices[i, j_idx])
            edge_key = (min(i, j), max(i, j))
            if edge_key not in seen:
                seen.add(edge_key)
                edge_src_list.append(i)
                edge_dst_list.append(j)
                edge_filt_list.append(max(filtration_values[i], filtration_values[j]))

    edge_src = np.array(edge_src_list, dtype=np.int32)
    edge_dst = np.array(edge_dst_list, dtype=np.int32)
    edge_filt = np.array(edge_filt_list, dtype=np.float64)
    return edge_src, edge_dst, edge_filt


def _flip_negated_diagram(dgm: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert a diagram from negated filtration back to density scale."""
    if dgm.shape[0] > 0:
        dgm = -dgm
        dgm = np.column_stack([dgm[:, 1], dgm[:, 0]])
    return dgm


def _build_neighbor_sets(n_pts: int, k: int, indices: NDArray[np.intp]) -> list[set[int]]:
    """Build per-vertex neighbor sets from kNN indices."""
    neighbor_set: list[set[int]] = [set() for _ in range(n_pts)]
    for i in range(n_pts):
        for j_idx in range(k):
            neighbor_set[i].add(int(indices[i, j_idx]))
    return neighbor_set


def _find_triangles(
    n_pts: int,
    neighbor_set: list[set[int]],
    filtration_values: NDArray[np.float64],
) -> tuple[list[int], list[int], list[int], list[float]]:
    """Find all triangles in the kNN graph and their filtration values."""
    tri_v0: list[int] = []
    tri_v1: list[int] = []
    tri_v2: list[int] = []
    tri_filt: list[float] = []
    for i in range(n_pts):
        for j in neighbor_set[i]:
            if j <= i:
                continue
            for c in neighbor_set[i] & neighbor_set[j]:
                if c <= j:
                    continue
                tri_v0.append(i)
                tri_v1.append(j)
                tri_v2.append(c)
                tri_filt.append(max(filtration_values[i], filtration_values[j], filtration_values[c]))
    return tri_v0, tri_v1, tri_v2, tri_filt


@dataclass
class _KnnGraph:
    """kNN graph data needed for triangle discovery."""

    n_pts: int
    k: int
    indices: NDArray[np.intp]
    filtration_values: NDArray[np.float64]


def _compute_gpu_h1(
    edge_src: NDArray[np.int32],
    edge_dst: NDArray[np.int32],
    edge_filt: NDArray[np.float64],
    knn: _KnnGraph,
) -> NDArray[np.float64]:
    """Compute H1 persistence on GPU, falling back to empty diagram on failure."""
    try:
        _persistence_mod = importlib.import_module("topostreams_cuda.persistence")
        gpu_persistence_h1 = _persistence_mod.gpu_persistence_h1

        neighbor_set = _build_neighbor_sets(knn.n_pts, knn.k, knn.indices)
        tri_v0, tri_v1, tri_v2, tri_filt = _find_triangles(knn.n_pts, neighbor_set, knn.filtration_values)

        if tri_v0:
            tri_simplex = _persistence_mod.TriangleSimplex(
                v0=np.array(tri_v0, dtype=np.int32),
                v1=np.array(tri_v1, dtype=np.int32),
                v2=np.array(tri_v2, dtype=np.int32),
                filt=np.array(tri_filt, dtype=np.float64),
            )
            h1_dgm = gpu_persistence_h1(
                edge_src,
                edge_dst,
                edge_filt,
                tri_simplex,
            )
            return _flip_negated_diagram(h1_dgm)
        return np.empty((0, 2), dtype=np.float64)
    except (ImportError, OSError):
        return np.empty((0, 2), dtype=np.float64)


def _compute_gpu(
    scaled: NDArray[np.float64],
    k: int,
    max_dim: int,
) -> list[NDArray[np.float64]]:
    """GPU-accelerated persistence computation."""
    n_pts = len(scaled)

    # kNN on GPU
    distances, indices = gpu_knn(scaled, k)

    # Density filtration on GPU
    kth_dist = distances[:, -1]
    filtration_values = gpu_density_filtration(kth_dist)

    # Build edge list from kNN indices
    edge_src, edge_dst, edge_filt = _build_edge_list(n_pts, k, indices, filtration_values)

    # H0 persistence on GPU
    h0_dgm = gpu_persistence_h0(filtration_values, edge_src, edge_dst, edge_filt)
    h0_dgm = _flip_negated_diagram(h0_dgm)

    diagrams: list[NDArray[np.float64]] = [h0_dgm]

    # H1 via GPU if requested
    if max_dim >= 1:
        knn = _KnnGraph(n_pts=n_pts, k=k, indices=indices, filtration_values=filtration_values)
        h1_dgm = _compute_gpu_h1(edge_src, edge_dst, edge_filt, knn)
        diagrams.append(h1_dgm)

    return diagrams


def _build_cpu_knn(
    scaled: NDArray[np.float64],
    k: int,
) -> tuple[NDArray[np.intp], NDArray[np.float64], NDArray[np.float64]]:
    """Build kNN graph and compute density filtration values on CPU."""
    nn = NearestNeighbors(n_neighbors=k + 1, algorithm="auto")
    nn.fit(scaled)
    distances, indices = nn.kneighbors(scaled)

    # Density estimate: 1 / distance-to-kth-neighbor
    kth_dist = distances[:, -1]
    kth_dist = np.maximum(kth_dist, 1e-10)
    density = 1.0 / kth_dist

    # Superlevel-set filtration via negation
    filtration_values = -density
    return indices, filtration_values, distances


def _extract_diagrams(simplex_tree: object, max_dim: int) -> list[NDArray[np.float64]]:
    """Extract and flip persistence diagrams from a computed SimplexTree."""
    diagrams: list[NDArray[np.float64]] = []
    for dim in range(max_dim + 1):
        pairs = simplex_tree.persistence_intervals_in_dimension(dim)  # type: ignore[attr-defined]
        if len(pairs) == 0:
            dgm = np.empty((0, 2), dtype=np.float64)
        else:
            dgm = np.array(pairs, dtype=np.float64)
            dgm = -dgm
            dgm = np.column_stack([dgm[:, 1], dgm[:, 0]])
        diagrams.append(dgm)
    return diagrams


def _build_simplex_tree(
    n_pts: int,
    k: int,
    indices: NDArray[np.intp],
    filtration_values: NDArray[np.float64],
    max_dim: int,
) -> list[NDArray[np.float64]]:
    """Build a SimplexTree, compute persistence, and return diagrams."""
    _gudhi_mod = importlib.import_module("gudhi")
    st = _gudhi_mod.SimplexTree()

    for i in range(n_pts):
        st.insert([i], filtration=filtration_values[i])

    for i in range(n_pts):
        for j_idx in range(1, k + 1):
            j = int(indices[i, j_idx])
            edge_filt = max(filtration_values[i], filtration_values[j])
            st.insert([i, j], filtration=edge_filt)

    if max_dim > 1:
        st.expansion(max_dim + 1)

    st.compute_persistence()
    return _extract_diagrams(st, max_dim)


def _compute_cpu(
    scaled: NDArray[np.float64],
    k: int,
    max_dim: int,
) -> list[NDArray[np.float64]]:
    """CPU fallback using sklearn + GUDHI."""
    n_pts = len(scaled)
    indices, filtration_values, _ = _build_cpu_knn(scaled, k)
    return _build_simplex_tree(n_pts, k, indices, filtration_values, max_dim)


def compute_density_filtration(
    points: NDArray[np.float64],
    n_neighbors: int = 32,
    max_dim: int = 1,
    scale: bool = True,
) -> PersistenceResult:
    """Compute persistent homology via kNN density filtration.

    Estimates local density using the distance to the k-th nearest
    neighbor, then builds a filtration on the kNN graph.  Uses GPU
    acceleration when topostreams-cuda is available, otherwise falls
    back to sklearn + GUDHI on CPU.

    Parameters
    ----------
    points : NDArray
        Array of shape (n_stars, n_features) in phase space.
    n_neighbors : int
        Number of nearest neighbors for density estimation. Default 32.
    max_dim : int
        Maximum homology dimension to compute. Default 1 (H0 + H1).
    scale : bool
        Whether to standardize features before computing. Default True.

    Returns
    -------
    PersistenceResult
        Persistence diagrams and metadata.

    """
    scaler = StandardScaler()
    if scale:
        scaled = scaler.fit_transform(points)
    else:
        scaler.fit(points)
        scaled = points.copy()

    k = min(n_neighbors, len(scaled) - 1)

    if _gpu_available:
        diagrams = _compute_gpu(scaled, k, max_dim)
    else:
        diagrams = _compute_cpu(scaled, k, max_dim)

    return PersistenceResult(diagrams=diagrams, point_cloud=scaled, scaler=scaler)


def persistence_to_lifetimes(diagram: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert a persistence diagram to lifetimes (death - birth).

    Parameters
    ----------
    diagram : NDArray
        Persistence diagram of shape (n_features, 2).

    Returns
    -------
    NDArray
        Lifetimes array of shape (n_features,).

    """
    # Filter out infinite-death features
    finite_mask = np.isfinite(diagram[:, 1])
    finite_dgm = diagram[finite_mask]
    return finite_dgm[:, 1] - finite_dgm[:, 0]
