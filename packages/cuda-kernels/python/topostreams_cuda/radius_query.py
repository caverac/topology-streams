"""GPU-accelerated radius query."""

from __future__ import annotations

import ctypes

import numpy as np
from numpy.typing import NDArray
from topostreams_cuda._bindings import _check, _lib


def gpu_radius_query(
    points: NDArray[np.float64],
    query: NDArray[np.float64],
    radius: float,
) -> NDArray[np.intp]:
    """Find all points within a given radius of a query point.

    Parameters
    ----------
    points : NDArray
        Array of shape (n, d) with data points.
    query : NDArray
        Query point of shape (d,).
    radius : float
        Search radius.

    Returns
    -------
    NDArray
        Array of indices of points within the radius.

    """
    points = np.ascontiguousarray(points, dtype=np.float64)
    query = np.ascontiguousarray(query, dtype=np.float64)
    n, d = points.shape

    out_indices = np.empty(n, dtype=np.int32)
    out_count = ctypes.c_int(0)

    err = _lib.topo_gpu_radius_query(
        points.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        query.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(n),
        ctypes.c_int(d),
        ctypes.c_double(radius),
        out_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        ctypes.byref(out_count),
    )
    _check(err)

    count = out_count.value
    return out_indices[:count].astype(np.intp)
