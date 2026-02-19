"""Tests for the _types module."""

from explore._types import STREAM_CATALOG, KnownStream, RecoveryResult


class TestKnownStream:
    """Tests for the KnownStream dataclass."""

    def test_is_frozen(self) -> None:
        """KnownStream instances should be immutable."""
        stream = KnownStream(name="Test", key="test", l_min=0, l_max=10, b_min=0, b_max=10, expected_members=100)
        try:
            stream.name = "Changed"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass

    def test_fields(self) -> None:
        """KnownStream should expose all coordinate fields."""
        stream = KnownStream(name="X", key="x", l_min=1, l_max=2, b_min=3, b_max=4, expected_members=50)
        assert stream.l_min == 1
        assert stream.l_max == 2
        assert stream.b_min == 3
        assert stream.b_max == 4
        assert stream.expected_members == 50


class TestStreamCatalog:
    """Tests for STREAM_CATALOG integrity."""

    def test_catalog_has_five_entries(self) -> None:
        """Catalog should contain exactly five streams."""
        assert len(STREAM_CATALOG) == 5

    def test_keys_match_stream_key_field(self) -> None:
        """Dictionary keys should match each stream's key attribute."""
        for key, stream in STREAM_CATALOG.items():
            assert key == stream.key

    def test_all_keys_are_lowercase(self) -> None:
        """All catalog keys should be lowercase."""
        for key in STREAM_CATALOG:
            assert key == key.lower()

    def test_longitude_ranges_valid(self) -> None:
        """l_min should be less than l_max for each stream."""
        for stream in STREAM_CATALOG.values():
            assert stream.l_min < stream.l_max, f"{stream.name}: l_min >= l_max"

    def test_latitude_ranges_valid(self) -> None:
        """b_min should be less than b_max for each stream."""
        for stream in STREAM_CATALOG.values():
            assert stream.b_min < stream.b_max, f"{stream.name}: b_min >= b_max"

    def test_expected_members_positive(self) -> None:
        """Expected member counts should be positive."""
        for stream in STREAM_CATALOG.values():
            assert stream.expected_members > 0, f"{stream.name}: expected_members <= 0"

    def test_gd1_in_catalog(self) -> None:
        """GD-1 should be in the catalog."""
        assert "gd-1" in STREAM_CATALOG
        assert STREAM_CATALOG["gd-1"].name == "GD-1"


def test_recovery_result_fields() -> None:
    """RecoveryResult should store all run summary fields."""
    stream = STREAM_CATALOG["gd-1"]
    result = RecoveryResult(stream=stream, n_stars=1000, n_clean=950, n_candidates=2, run_dir="/tmp/test")
    assert result.n_stars == 1000
    assert result.n_clean == 950
    assert result.n_candidates == 2
    assert result.run_dir == "/tmp/test"
    assert result.stream is stream
