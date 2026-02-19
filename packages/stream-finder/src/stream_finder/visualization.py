"""Visualization utilities for persistence diagrams and stream candidates."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from stream_finder.streams import StreamCandidate
    from stream_finder.topology import PersistenceResult


def plot_persistence_diagram(
    result: PersistenceResult,
    homology_dim: int = 0,
    ax: Axes | None = None,
    threshold: float | None = None,
) -> tuple[Figure, Axes]:
    """Plot a persistence diagram.

    Parameters
    ----------
    result : PersistenceResult
        Output from compute_persistence().
    homology_dim : int
        Which homology dimension to plot. Default 0.
    ax : matplotlib Axes, optional
        Axes to plot on. If None, creates new figure.
    threshold : float, optional
        If given, draws a line indicating the persistence threshold.

    Returns
    -------
    tuple of (Figure, Axes)

    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    else:
        fig = cast("Figure", ax.get_figure())

    diagram = result.diagrams[homology_dim]
    finite_mask = np.isfinite(diagram[:, 1])

    # Plot finite features
    ax.scatter(
        diagram[finite_mask, 0],
        diagram[finite_mask, 1],
        s=15,
        alpha=0.6,
        label=f"$H_{homology_dim}$",
    )

    # Plot diagonal
    lims = [
        min(diagram[finite_mask, 0].min(), 0),
        diagram[finite_mask, 1].max() * 1.1,
    ]
    ax.plot(lims, lims, "k--", alpha=0.3, linewidth=0.5)

    if threshold is not None:
        # Draw threshold line parallel to diagonal
        ax.plot(
            lims,
            [lims[0] + threshold, lims[1] + threshold],
            "r--",
            alpha=0.5,
            label=f"threshold = {threshold:.2f}",
        )

    ax.set_xlabel("Birth")
    ax.set_ylabel("Death")
    ax.set_title(f"Persistence Diagram ($H_{homology_dim}$)")
    ax.legend()
    ax.set_aspect("equal")

    return fig, ax


def plot_sky_candidates(
    ra: NDArray[np.float64],
    dec: NDArray[np.float64],
    candidates: list[StreamCandidate],
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Plot stream candidates on the sky.

    Parameters
    ----------
    ra, dec : NDArray
        Right ascension and declination of all stars.
    candidates : list of StreamCandidate
        Stream candidates to highlight.
    ax : matplotlib Axes, optional
        Axes to plot on. If None, creates new figure.

    Returns
    -------
    tuple of (Figure, Axes)

    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    else:
        fig = cast("Figure", ax.get_figure())

    # Background field stars
    ax.scatter(ra, dec, s=0.1, c="gray", alpha=0.1, rasterized=True)

    # Highlight each candidate
    cmap = matplotlib.colormaps["viridis"]
    colors = cmap(np.linspace(0.2, 0.9, len(candidates)))
    for i, candidate in enumerate(candidates):
        idx = candidate.member_indices
        ax.scatter(
            ra[idx],
            dec[idx],
            s=5,
            c=[colors[i]],
            alpha=0.7,
            label=f"Candidate {i + 1} (p={candidate.persistence:.2f})",
        )

    ax.set_xlabel("RA (deg)")
    ax.set_ylabel("Dec (deg)")
    ax.set_title("Stream Candidates")
    ax.invert_xaxis()
    ax.legend(fontsize=8)

    return fig, ax
