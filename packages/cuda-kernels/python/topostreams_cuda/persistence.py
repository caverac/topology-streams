"""GPU-accelerated persistent homology computation."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from topostreams_cuda._bindings import _check, _lib


@dataclass(frozen=True)
class TriangleSimplex:
    """Triangle simplex data for H1 persistence computation.

    Attributes
    ----------
    v0 : NDArray[np.int32]
        First vertex index for each triangle, length t.
    v1 : NDArray[np.int32]
        Second vertex index for each triangle, length t.
    v2 : NDArray[np.int32]
        Third vertex index for each triangle, length t.
    filt : NDArray[np.float64]
        Filtration value for each triangle, length t.

    """

    v0: NDArray[np.int32]
    v1: NDArray[np.int32]
    v2: NDArray[np.int32]
    filt: NDArray[np.float64]


def gpu_persistence_h0(
    vertex_filt: NDArray[np.float64],
    edge_src: NDArray[np.int32],
    edge_dst: NDArray[np.int32],
    edge_filt: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute H0 persistent homology on GPU.

    Parameters
    ----------
    vertex_filt : NDArray
        Filtration values for each vertex, length n.
    edge_src : NDArray
        Source vertex index for each edge, length m.
    edge_dst : NDArray
        Destination vertex index for each edge, length m.
    edge_filt : NDArray
        Filtration value for each edge, length m.

    Returns
    -------
    NDArray
        Persistence diagram of shape (count, 2) with (birth, death) pairs.

    """
    vertex_filt = np.ascontiguousarray(vertex_filt, dtype=np.float64)
    edge_src = np.ascontiguousarray(edge_src, dtype=np.int32)
    edge_dst = np.ascontiguousarray(edge_dst, dtype=np.int32)
    edge_filt = np.ascontiguousarray(edge_filt, dtype=np.float64)

    n = len(vertex_filt)
    m = len(edge_src)

    out_births = np.empty(n, dtype=np.float64)
    out_deaths = np.empty(n, dtype=np.float64)
    out_count = ctypes.c_int(0)

    err = _lib.topo_gpu_persistence_h0(
        vertex_filt.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        edge_src.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        edge_dst.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        edge_filt.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(n),
        ctypes.c_int(m),
        out_births.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        out_deaths.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.byref(out_count),
    )
    _check(err)

    count = out_count.value
    if count == 0:
        return np.empty((0, 2), dtype=np.float64)

    return np.column_stack([out_births[:count], out_deaths[:count]])


def gpu_persistence_h1(
    edge_src: NDArray[np.int32],
    edge_dst: NDArray[np.int32],
    edge_filt: NDArray[np.float64],
    triangles: TriangleSimplex,
) -> NDArray[np.float64]:
    """Compute H1 persistent homology via boundary matrix reduction.

    Parameters
    ----------
    edge_src, edge_dst : NDArray
        Edge endpoints, length m.
    edge_filt : NDArray
        Edge filtration values, length m.
    triangles : TriangleSimplex
        Triangle simplex data containing vertex indices and filtration values.

    Returns
    -------
    NDArray
        Persistence diagram of shape (count, 2) with (birth, death) pairs.

    """
    edge_src = np.ascontiguousarray(edge_src, dtype=np.int32)
    edge_dst = np.ascontiguousarray(edge_dst, dtype=np.int32)
    edge_filt = np.ascontiguousarray(edge_filt, dtype=np.float64)
    tri_v0 = np.ascontiguousarray(triangles.v0, dtype=np.int32)
    tri_v1 = np.ascontiguousarray(triangles.v1, dtype=np.int32)
    tri_v2 = np.ascontiguousarray(triangles.v2, dtype=np.int32)
    tri_filt = np.ascontiguousarray(triangles.filt, dtype=np.float64)

    m = len(edge_src)
    t = len(tri_v0)

    out_births = np.empty(t, dtype=np.float64)
    out_deaths = np.empty(t, dtype=np.float64)
    out_count = ctypes.c_int(0)

    err = _lib.topo_gpu_persistence_h1(
        edge_src.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        edge_dst.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        edge_filt.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        tri_v0.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        tri_v1.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        tri_v2.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        tri_filt.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(m),
        ctypes.c_int(t),
        out_births.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        out_deaths.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.byref(out_count),
    )
    _check(err)

    count = out_count.value
    if count == 0:
        return np.empty((0, 2), dtype=np.float64)

    return np.column_stack([out_births[:count], out_deaths[:count]])
