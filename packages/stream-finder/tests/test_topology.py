"""Tests for the topology module."""

import numpy as np
from stream_finder.topology import PersistenceResult, compute_density_filtration, persistence_to_lifetimes


class TestComputeDensityFiltration:
    """Tests for compute_density_filtration."""

    def test_returns_persistence_result(self) -> None:
        """Should return a PersistenceResult dataclass."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points)
        assert isinstance(result, PersistenceResult)

    def test_diagrams_have_correct_dimensions(self) -> None:
        """Should return H0 and H1 diagrams by default (max_dim=1)."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points, max_dim=1)
        assert len(result.diagrams) == 2  # H0 and H1

    def test_h0_has_features(self) -> None:
        """H0 diagram should have at least one feature."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points, max_dim=0)
        assert len(result.diagrams[0]) > 0

    def test_scaling_changes_point_cloud(self) -> None:
        """Scaling should normalize the point cloud."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3)) * 100 + 500
        result = compute_density_filtration(points, scale=True)
        # Scaled data should have mean ~0, std ~1
        assert abs(result.point_cloud.mean()) < 0.5
        assert abs(result.point_cloud.std() - 1.0) < 0.5

    def test_two_clusters_have_persistent_h0(self) -> None:
        """Two separated clusters should produce a persistent H0 feature."""
        rng = np.random.default_rng(42)
        cluster_a = rng.standard_normal((30, 2)) + np.array([0, 0])
        cluster_b = rng.standard_normal((30, 2)) + np.array([10, 10])
        points = np.vstack([cluster_a, cluster_b])

        result = compute_density_filtration(points, max_dim=0, scale=False)
        lifetimes = persistence_to_lifetimes(result.diagrams[0])

        # At least one H0 feature should have non-trivial persistence
        assert lifetimes.max() > 0.0

    def test_n_neighbors_param(self) -> None:
        """Should accept custom n_neighbors parameter."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points, n_neighbors=10)
        assert isinstance(result, PersistenceResult)

    def test_birth_before_death(self) -> None:
        """All finite features should have birth <= death."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points, max_dim=1)
        for dgm in result.diagrams:
            if len(dgm) == 0:
                continue
            finite_mask = np.isfinite(dgm[:, 1])
            finite_dgm = dgm[finite_mask]
            if len(finite_dgm) > 0:
                assert np.all(finite_dgm[:, 0] <= finite_dgm[:, 1])


class TestPersistenceToLifetimes:
    """Tests for persistence_to_lifetimes."""

    def test_computes_lifetimes(self) -> None:
        """Should compute death - birth for finite features."""
        diagram = np.array([[0.0, 1.0], [0.5, 2.0], [0.0, np.inf]])
        lifetimes = persistence_to_lifetimes(diagram)
        np.testing.assert_array_almost_equal(lifetimes, [1.0, 1.5])

    def test_empty_after_filtering(self) -> None:
        """Should return empty array if all features are infinite."""
        diagram = np.array([[0.0, np.inf]])
        lifetimes = persistence_to_lifetimes(diagram)
        assert len(lifetimes) == 0
