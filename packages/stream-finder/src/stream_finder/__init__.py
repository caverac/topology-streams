"""Stream-finder: stellar stream detection using persistent homology on Gaia data."""

__version__ = "0.1.0"

from stream_finder.data import (
    GaiaQualityFilter,
    clean_phase_space,
    fetch_gaia_region,
    load_starstream_members,
    serialize_candidates,
)
from stream_finder.streams import extract_stream_candidates
from stream_finder.topology import compute_density_filtration

__all__ = [
    "GaiaQualityFilter",
    "clean_phase_space",
    "fetch_gaia_region",
    "load_starstream_members",
    "serialize_candidates",
    "compute_density_filtration",
    "extract_stream_candidates",
]
