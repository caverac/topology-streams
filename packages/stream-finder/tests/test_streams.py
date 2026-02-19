"""Tests for the streams module."""

import numpy as np
from stream_finder.streams import StreamCandidate, extract_stream_candidates
from stream_finder.topology import compute_density_filtration


class TestExtractStreamCandidates:
    """Tests for extract_stream_candidates."""

    def test_returns_list_of_candidates(self) -> None:
        """Should return a list of StreamCandidate objects."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((100, 3))
        result = compute_density_filtration(points, max_dim=0)
        candidates = extract_stream_candidates(result, sigma_threshold=2.0)
        assert isinstance(candidates, list)
        for c in candidates:
            assert isinstance(c, StreamCandidate)

    def test_candidates_sorted_by_persistence(self) -> None:
        """Candidates should be sorted by persistence, highest first."""
        rng = np.random.default_rng(42)
        cluster_a = rng.standard_normal((30, 2))
        cluster_b = rng.standard_normal((30, 2)) + np.array([10, 10])
        points = np.vstack([cluster_a, cluster_b])

        result = compute_density_filtration(points, max_dim=0, scale=False)
        candidates = extract_stream_candidates(result, sigma_threshold=1.0)

        for i in range(len(candidates) - 1):
            assert candidates[i].persistence >= candidates[i + 1].persistence

    def test_no_candidates_from_noise(self) -> None:
        """Uniform random data with high threshold should yield no candidates."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points, max_dim=0)
        candidates = extract_stream_candidates(result, sigma_threshold=10.0)
        assert len(candidates) == 0

    def test_explicit_threshold(self) -> None:
        """Should respect an explicit persistence_threshold."""
        rng = np.random.default_rng(42)
        points = rng.standard_normal((50, 3))
        result = compute_density_filtration(points, max_dim=0)
        candidates = extract_stream_candidates(result, persistence_threshold=999.0)
        assert len(candidates) == 0
