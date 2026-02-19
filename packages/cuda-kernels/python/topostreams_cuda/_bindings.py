"""Low-level ctypes bindings for libtopostreams.so."""

from __future__ import annotations

import ctypes
import os
from ctypes import POINTER, c_double, c_int
from pathlib import Path


def _find_library() -> str:
    """Locate libtopostreams.so via environment variable or standard paths."""
    env_path = os.environ.get("TOPOSTREAMS_LIB_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # Check relative to this file (build directory layout)
    here = Path(__file__).parent
    candidates = [
        here / "libtopostreams.so",
        here.parent.parent.parent / "build" / "libtopostreams.so",
        Path("/usr/local/lib/libtopostreams.so"),
        Path("/usr/lib/libtopostreams.so"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)

    raise OSError("Cannot find libtopostreams.so. Set TOPOSTREAMS_LIB_PATH or install the library.")


_lib = ctypes.CDLL(_find_library())

# TopoError = c_int (enum)

# topo_error_string
_lib.topo_error_string.restype = ctypes.c_char_p
_lib.topo_error_string.argtypes = [c_int]

# topo_gpu_knn
_lib.topo_gpu_knn.restype = c_int
_lib.topo_gpu_knn.argtypes = [
    POINTER(c_double),  # points
    c_int,  # n
    c_int,  # d
    c_int,  # k
    POINTER(c_double),  # out_dist
    POINTER(c_int),  # out_idx
]

# topo_gpu_density_filtration
_lib.topo_gpu_density_filtration.restype = c_int
_lib.topo_gpu_density_filtration.argtypes = [
    POINTER(c_double),  # kth_distances
    c_int,  # n
    POINTER(c_double),  # out_filtration
]

# topo_gpu_persistence_h0
_lib.topo_gpu_persistence_h0.restype = c_int
_lib.topo_gpu_persistence_h0.argtypes = [
    POINTER(c_double),  # vertex_filt
    POINTER(c_int),  # edge_src
    POINTER(c_int),  # edge_dst
    POINTER(c_double),  # edge_filt
    c_int,  # n
    c_int,  # m
    POINTER(c_double),  # out_births
    POINTER(c_double),  # out_deaths
    POINTER(c_int),  # out_count
]

# topo_gpu_persistence_h1
_lib.topo_gpu_persistence_h1.restype = c_int
_lib.topo_gpu_persistence_h1.argtypes = [
    POINTER(c_int),  # edge_src
    POINTER(c_int),  # edge_dst
    POINTER(c_double),  # edge_filt
    POINTER(c_int),  # tri_v0
    POINTER(c_int),  # tri_v1
    POINTER(c_int),  # tri_v2
    POINTER(c_double),  # tri_filt
    c_int,  # m
    c_int,  # t
    POINTER(c_double),  # out_births
    POINTER(c_double),  # out_deaths
    POINTER(c_int),  # out_count
]

# topo_gpu_radius_query
_lib.topo_gpu_radius_query.restype = c_int
_lib.topo_gpu_radius_query.argtypes = [
    POINTER(c_double),  # points
    POINTER(c_double),  # query
    c_int,  # n
    c_int,  # d
    c_double,  # radius
    POINTER(c_int),  # out_indices
    POINTER(c_int),  # out_count
]


def _check(err: int) -> None:
    """Raise RuntimeError if a CUDA call returned a non-zero error code."""
    if err != 0:
        msg = _lib.topo_error_string(err)
        raise RuntimeError(f"topostreams CUDA error ({err}): {msg.decode()}")
