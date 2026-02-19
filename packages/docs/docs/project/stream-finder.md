---
sidebar_position: 2
---

# stream-finder

The `stream-finder` Python package implements persistent homology for stellar stream detection in Gaia data.

## Installation

```bash
# From the monorepo root
uv sync

# Or install directly
pip install -e packages/stream-finder
```

## Module structure

```
stream_finder/
├── __init__.py          # Public API
├── data.py              # Gaia data fetching & preprocessing
├── topology.py          # kNN density filtration + persistent homology
├── streams.py           # Stream candidate extraction from persistence diagrams
├── visualization.py     # Plotting persistence diagrams & stream overlays
└── _gpu.py              # GPU availability detection
```

## Approach

### 1. Data ingestion (`data.py`)

Fetch phase-space data from Gaia DR3 via `astroquery.gaia` or load from pre-processed catalogs (StarStream DR, galstreams).

Feature vector per star: `(ra, dec, pmra, pmdec, parallax)` — 5D.

### 2. kNN density filtration (`topology.py`)

Compute persistence diagrams using a density-based approach:

1. **kNN distances**: compute the distance to the k-th nearest neighbor for each point (default k=32)
2. **Density estimation**: convert kNN distances to density values (`1 / distance_to_kth_neighbor`)
3. **Superlevel-set filtration**: negate densities to build a filtration that processes high-density regions first
4. **Persistent homology**: compute $H_0$ (connected components) and $H_1$ (loops) persistence on the kNN graph

The CPU backend uses scikit-learn `NearestNeighbors` for kNN and GUDHI `SimplexTree` for persistence. When GPU is available, all steps use CUDA kernels from `topostreams-cuda`.

### 3. Stream extraction (`streams.py`)

Identify stream candidates from topological features:

- Compute **lifetimes** (death - birth) for all finite features
- Apply a **sigma threshold** (default 3.0): features with lifetime > mean + sigma \* std are significant
- For each significant feature, perform a **radius query** to find member stars in the point cloud
- Return `StreamCandidate` objects sorted by persistence (highest first)

The radius query uses CUDA kernels when GPU is available, otherwise falls back to `scipy.spatial.KDTree`.

### 4. Visualization (`visualization.py`)

- Persistence diagrams and barcodes
- Sky-projected stream candidates overlaid on Gaia field stars
- Comparison with galstreams known tracks

## GPU acceleration

The `_gpu.py` module detects GPU availability at import time:

```python
try:
    import topostreams_cuda
    available = True
except (ImportError, OSError):
    available = False
```

When `available` is `True`, `topology.py` uses CUDA kernels for kNN computation, density filtration, and persistence (H0/H1). When `False`, it falls back to the CPU stack (scikit-learn + GUDHI + scipy). No code changes are needed — the backend is selected automatically.

## Dependencies

| Package            | Purpose                                         |
| ------------------ | ----------------------------------------------- |
| `numpy`            | Array operations                                |
| `scipy`            | Spatial algorithms (KDTree for radius queries)  |
| `scikit-learn`     | kNN computation, preprocessing (StandardScaler) |
| `gudhi`            | SimplexTree for persistent homology (CPU)       |
| `astropy`          | Coordinate transforms, FITS I/O                 |
| `astroquery`       | Gaia archive queries                            |
| `matplotlib`       | Visualization                                   |
| `topostreams-cuda` | GPU-accelerated kernels (optional)              |
