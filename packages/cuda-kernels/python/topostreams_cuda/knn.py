"""GPU-accelerated k-nearest neighbors."""

from __future__ import annotations

import ctypes

import numpy as np
from numpy.typing import NDArray
from topostreams_cuda._bindings import _check, _lib


def gpu_knn(points: NDArray[np.float64], k: int) -> tuple[NDArray[np.float64], NDArray[np.intp]]:
    """Compute k-nearest neighbors on GPU.

    Parameters
    ----------
    points : NDArray
        Array of shape (n, d) with data points.
    k : int
        Number of neighbors (excluding self).

    Returns
    -------
    distances : NDArray
        Array of shape (n, k) with distances to neighbors.
    indices : NDArray
        Array of shape (n, k) with neighbor indices.

    """
    points = np.ascontiguousarray(points, dtype=np.float64)
    n, d = points.shape

    out_dist = np.empty((n, k), dtype=np.float64)
    out_idx = np.empty((n, k), dtype=np.int32)

    err = _lib.topo_gpu_knn(
        points.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(n),
        ctypes.c_int(d),
        ctypes.c_int(k),
        out_dist.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        out_idx.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
    )
    _check(err)

    return out_dist, out_idx.astype(np.intp)
