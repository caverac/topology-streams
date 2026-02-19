---
sidebar_position: 5
---

# cuda-kernels

The `cuda-kernels` package provides GPU-accelerated replacements for the CPU-bound steps in the stream-finder pipeline.

## Kernels

| Kernel             | Source file             | Replaces (CPU)                        |
| ------------------ | ----------------------- | ------------------------------------- |
| **kNN**            | `src/knn.cu`            | `sklearn.neighbors.NearestNeighbors`  |
| **Density**        | `src/density.cu`        | kth-NN distance → density computation |
| **Persistence H0** | `src/persistence_h0.cu` | GUDHI SimplexTree (H0)                |
| **Persistence H1** | `src/persistence_h1.cu` | GUDHI SimplexTree (H1)                |
| **Radius query**   | `src/radius_query.cu`   | `scipy.spatial.KDTree`                |

## Python bindings

The `topostreams_cuda` Python package exposes the CUDA kernels via ctypes:

```
cuda-kernels/
├── python/
│   └── topostreams_cuda/
│       ├── __init__.py       # Package exports
│       ├── _bindings.py      # ctypes shared library loader
│       ├── knn.py            # kNN binding
│       ├── density.py        # Density filtration binding
│       ├── persistence.py    # H0/H1 persistence binding
│       └── radius_query.py   # Radius query binding
├── include/topostreams/      # C++ headers
│   ├── knn.h
│   ├── density.h
│   ├── persistence.h
│   ├── radius_query.h
│   ├── types.h
│   └── error.h
└── src/                      # CUDA source files
```

## Integration with stream-finder

`stream-finder` detects GPU availability at import time via `_gpu.py`:

```python
# stream_finder/_gpu.py
try:
    import topostreams_cuda
    available = True
except (ImportError, OSError):
    available = False
```

When `available` is `True`, `topology.py` and `streams.py` use the CUDA kernels for kNN, density filtration, persistence computation, and radius queries. Otherwise they fall back to scikit-learn, GUDHI, and scipy.

## Build

Requires CUDA 12.x and CMake:

```bash
cd packages/cuda-kernels
mkdir build && cd build
cmake .. -DCMAKE_CUDA_ARCHITECTURES=75  # sm_75 = T4
make -j
```

The default architecture target is `sm_75` (NVIDIA T4), matching the `g4dn.xlarge` EC2 instance type used in production. Override `CMAKE_CUDA_ARCHITECTURES` for other GPUs.

The build produces a shared library `libtopostreams.so` that the Python ctypes bindings load at runtime.
