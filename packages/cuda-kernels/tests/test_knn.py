"""Tests for GPU kNN against sklearn reference."""

import numpy as np
import pytest

try:
    from topostreams_cuda.knn import gpu_knn

    GPU_AVAILABLE = True
except (ImportError, OSError):
    GPU_AVAILABLE = False

pytestmark = pytest.mark.skipif(not GPU_AVAILABLE, reason="CUDA library not available")


def test_knn_matches_sklearn():
    from sklearn.neighbors import NearestNeighbors

    rng = np.random.default_rng(42)
    points = rng.standard_normal((100, 5))
    k = 10

    nn = NearestNeighbors(n_neighbors=k + 1, algorithm="brute")
    nn.fit(points)
    ref_dist, ref_idx = nn.kneighbors(points)
    ref_dist = ref_dist[:, 1:]  # skip self
    ref_idx = ref_idx[:, 1:]

    gpu_dist, gpu_idx = gpu_knn(points, k)

    np.testing.assert_allclose(gpu_dist, ref_dist, rtol=1e-10)
    np.testing.assert_array_equal(gpu_idx, ref_idx)


def test_knn_small():
    points = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype=np.float64)
    k = 2

    dist, idx = gpu_knn(points, k)
    assert dist.shape == (4, 2)
    assert idx.shape == (4, 2)
    assert np.all(dist[:, 0] <= dist[:, 1])  # sorted ascending


def test_knn_returns_correct_types():
    rng = np.random.default_rng(0)
    points = rng.standard_normal((50, 3))
    dist, idx = gpu_knn(points, 5)

    assert dist.dtype == np.float64
    assert idx.dtype == np.intp
