"""GPU-accelerated density filtration computation."""

from __future__ import annotations

import ctypes

import numpy as np
from numpy.typing import NDArray
from topostreams_cuda._bindings import _check, _lib


def gpu_density_filtration(
    kth_distances: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute density-based filtration values on GPU.

    filtration[i] = -1.0 / max(kth_distances[i], 1e-10)

    Parameters
    ----------
    kth_distances : NDArray
        Array of length n with k-th neighbor distances.

    Returns
    -------
    NDArray
        Array of length n with filtration values.

    """
    kth_distances = np.ascontiguousarray(kth_distances, dtype=np.float64)
    n = len(kth_distances)

    out_filtration = np.empty(n, dtype=np.float64)

    err = _lib.topo_gpu_density_filtration(
        kth_distances.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(n),
        out_filtration.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    )
    _check(err)

    return out_filtration
