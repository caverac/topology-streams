"""Tests for GPU radius query against scipy reference."""

import numpy as np
import pytest

try:
    from topostreams_cuda.radius_query import gpu_radius_query

    GPU_AVAILABLE = True
except (ImportError, OSError):
    GPU_AVAILABLE = False

pytestmark = pytest.mark.skipif(not GPU_AVAILABLE, reason="CUDA library not available")


def test_radius_query_matches_scipy():
    from scipy.spatial import KDTree

    rng = np.random.default_rng(42)
    points = rng.standard_normal((200, 3))
    query = points[0]
    radius = 1.5

    tree = KDTree(points)
    ref_indices = sorted(tree.query_ball_point(query, r=radius))

    gpu_indices = sorted(gpu_radius_query(points, query, radius).tolist())

    assert gpu_indices == ref_indices


def test_radius_query_empty():
    points = np.array([[10.0, 10.0]], dtype=np.float64)
    query = np.array([0.0, 0.0], dtype=np.float64)
    result = gpu_radius_query(points, query, 0.1)
    assert len(result) == 0


def test_radius_query_all_match():
    points = np.zeros((5, 2), dtype=np.float64)
    query = np.zeros(2, dtype=np.float64)
    result = gpu_radius_query(points, query, 1.0)
    assert len(result) == 5
