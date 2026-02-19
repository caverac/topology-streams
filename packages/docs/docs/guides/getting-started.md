---
sidebar_position: 1
---

# Getting Started

Run persistent homology on real Gaia DR3 data in under five minutes.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Install

From the monorepo root:

```bash
uv sync --group dev
```

This installs both `stream-finder` (the library) and `explore` (the CLI) along with all dependencies (GUDHI, astropy, astroquery, etc.).

Verify the CLI is available:

```bash
uv run explore --help
```

## See available streams

The CLI ships with 5 hardcoded stellar streams from the literature, each defined by Galactic coordinate bounds:

```bash
uv run explore catalog
```

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Key           ┃ Name          ┃ l range (deg) ┃ b range (deg) ┃     Expected ┃
┃               ┃               ┃               ┃               ┃      members ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ gd-1          │ GD-1          │ 135 – 225     │ 30 – 75       │       ~1,689 │
│ palomar-5     │ Palomar 5     │ 0 – 10        │ 40 – 50       │         ~500 │
│ jhelum        │ Jhelum        │ 335 – 360     │ -55 – -35     │         ~300 │
│ orphan-chenab │ Orphan-Chenab │ 160 – 260     │ 30 – 70       │         ~800 │
│ atlas-aliqa-… │ ATLAS-Aliqa   │ 225 – 270     │ 25 – 55       │         ~200 │
│               │ Uma           │               │               │              │
└───────────────┴───────────────┴───────────────┴───────────────┴──────────────┘
```

## Your first run

**Start with Palomar 5** — it has the tightest coordinate box (l=0–10, b=40–50), so fewer stars and the fastest compute time.

```bash
uv run explore recover palomar-5 --output-dir /tmp/explore-test
```

This will:

1. Query the ESA Gaia DR3 archive for all stars in the region (requires network)
2. Save the raw table as `gaia_table.ecsv`
3. Build a 5D phase-space array `(ra, dec, pmra, pmdec, parallax)`, dropping NaN rows
4. Run kNN density filtration to compute persistent homology
5. Extract stream candidates using a sigma threshold on feature lifetimes
6. Save everything to a timestamped run directory

### Tuning parameters

The `--n-neighbors` option controls the kNN graph density. Lower values capture finer structure but are noisier; higher values smooth out small-scale features.

| Option              | Default | Effect                                                      |
| ------------------- | ------- | ----------------------------------------------------------- |
| `--n-neighbors 16`  | `32`    | Finer structure, more sensitive to local density variations |
| `--sigma-threshold` | `3.0`   | Lower threshold = more candidates returned                  |

Example with adjusted parameters:

```bash
uv run explore recover palomar-5 \
  --n-neighbors 16 \
  --sigma-threshold 2.0 \
  --output-dir /tmp/explore-test
```

## Generate plots

After a run completes, generate a persistence diagram and sky map:

```bash
uv run explore plot /tmp/explore-test/palomar-5/<timestamp>
```

Replace `<timestamp>` with the actual directory name (e.g. `20260218T143012Z`).

This produces two PNG files in the run directory:

- **`persistence_diagram.png`** — birth vs. death scatter plot for the chosen homology dimension
- **`sky_map.png`** — RA/Dec projection with candidate members highlighted over the full field

Options:

| Option             | Default | Effect                      |
| ------------------ | ------- | --------------------------- |
| `--homology-dim 1` | `0`     | Plot $H_1$ instead of $H_0$ |
| `--dpi 300`        | `150`   | Higher resolution output    |

## Output structure

Each run saves to `<output-dir>/<stream-key>/<timestamp>/`:

```
runs/palomar-5/20260218T143012Z/
├── gaia_table.ecsv         # Raw Gaia query result
├── persistence.npz         # Diagrams, scaled point cloud, clean_indices
├── candidates.json         # Candidate summary (persistence, birth, death)
├── candidate_members.npz   # Member star indices per candidate
└── metadata.json           # Run parameters and star counts
```

The `clean_indices` array in `persistence.npz` maps point-cloud row indices back to the original table rows — this is how the `plot` command correctly maps candidate members onto RA/Dec coordinates from the full Gaia table.

## Next steps

- Try a larger stream like **GD-1**: `uv run explore recover gd-1`
- Compare candidates against known member catalogs
- Experiment with different `--sigma-threshold` values to tune sensitivity
