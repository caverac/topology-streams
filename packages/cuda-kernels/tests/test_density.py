"""Tests for GPU density filtration."""

import numpy as np
import pytest

try:
    from topostreams_cuda.density import gpu_density_filtration

    GPU_AVAILABLE = True
except (ImportError, OSError):
    GPU_AVAILABLE = False

pytestmark = pytest.mark.skipif(not GPU_AVAILABLE, reason="CUDA library not available")


def test_density_filtration_basic():
    kth_dist = np.array([1.0, 2.0, 0.5, 4.0], dtype=np.float64)
    result = gpu_density_filtration(kth_dist)

    expected = -1.0 / np.maximum(kth_dist, 1e-10)
    np.testing.assert_allclose(result, expected, rtol=1e-10)


def test_density_filtration_avoids_division_by_zero():
    kth_dist = np.array([0.0, 1e-15, 1.0], dtype=np.float64)
    result = gpu_density_filtration(kth_dist)

    # Tiny values should be clamped to 1e-10
    assert np.all(np.isfinite(result))
    assert result[0] == pytest.approx(-1.0 / 1e-10)


def test_density_filtration_all_negative():
    kth_dist = np.ones(100, dtype=np.float64) * 2.0
    result = gpu_density_filtration(kth_dist)

    assert np.all(result < 0)
    np.testing.assert_allclose(result, -0.5, rtol=1e-10)
