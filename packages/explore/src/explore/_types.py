"""Data types for the explore CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnownStream:
    """A known stellar stream with its Galactic coordinate bounds.

    Attributes
    ----------
    name : str
        Human-readable name (e.g. "GD-1").
    key : str
        CLI-friendly lowercase key (e.g. "gd-1").
    l_min : float
        Minimum Galactic longitude in degrees.
    l_max : float
        Maximum Galactic longitude in degrees.
    b_min : float
        Minimum Galactic latitude in degrees.
    b_max : float
        Maximum Galactic latitude in degrees.
    expected_members : int
        Approximate expected number of member stars.

    """

    name: str
    key: str
    l_min: float
    l_max: float
    b_min: float
    b_max: float
    expected_members: int


@dataclass
class RecoveryResult:
    """Summary of a single recovery run.

    Attributes
    ----------
    stream : KnownStream
        The stream that was targeted.
    n_stars : int
        Number of stars fetched from Gaia.
    n_clean : int
        Number of stars after NaN removal.
    n_candidates : int
        Number of stream candidates extracted.
    run_dir : str
        Path to the output directory for this run.

    """

    stream: KnownStream
    n_stars: int
    n_clean: int
    n_candidates: int
    run_dir: str


# ---------------------------------------------------------------------------
# Stream catalog
# ---------------------------------------------------------------------------

STREAM_CATALOG: dict[str, KnownStream] = {
    s.key: s
    for s in [
        KnownStream(
            name="GD-1",
            key="gd-1",
            l_min=135.0,
            l_max=225.0,
            b_min=30.0,
            b_max=75.0,
            expected_members=1689,
        ),
        KnownStream(
            name="Palomar 5",
            key="palomar-5",
            l_min=0.0,
            l_max=10.0,
            b_min=40.0,
            b_max=50.0,
            expected_members=500,
        ),
        KnownStream(
            name="Jhelum",
            key="jhelum",
            l_min=335.0,
            l_max=360.0,
            b_min=-55.0,
            b_max=-35.0,
            expected_members=300,
        ),
        KnownStream(
            name="Orphan-Chenab",
            key="orphan-chenab",
            l_min=160.0,
            l_max=260.0,
            b_min=30.0,
            b_max=70.0,
            expected_members=800,
        ),
        KnownStream(
            name="ATLAS-Aliqa Uma",
            key="atlas-aliqa-uma",
            l_min=225.0,
            l_max=270.0,
            b_min=25.0,
            b_max=55.0,
            expected_members=200,
        ),
    ]
}
