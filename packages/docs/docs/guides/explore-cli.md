---
sidebar_position: 2
---

# explore CLI Reference

The `explore` CLI tests whether persistent homology recovers known stellar streams from Gaia DR3 data.

## Commands

### `explore catalog`

List all available streams with their Galactic coordinate bounds and expected member counts.

```bash
uv run explore catalog
```

No options. The catalog is hardcoded with 5 streams: GD-1, Palomar 5, Jhelum, Orphan-Chenab, and ATLAS-Aliqa Uma.

### `explore recover <stream-name>`

Run the end-to-end recovery pipeline for a single stream.

```bash
uv run explore recover gd-1 [OPTIONS]
```

`stream-name` must match a key from `explore catalog` (e.g. `gd-1`, `palomar-5`).

**Options:**

| Option              | Type  | Default | Description                                                                         |
| ------------------- | ----- | ------- | ----------------------------------------------------------------------------------- |
| `--sigma-threshold` | float | `3.0`   | Number of standard deviations above mean lifetime to consider a feature significant |
| `--n-neighbors`     | int   | `32`    | Number of neighbors for kNN density estimation                                      |
| `--output-dir`      | path  | `runs/` | Root output directory                                                               |
| `--force`           | flag  | —       | Overwrite an existing run directory                                                 |

**Pipeline steps (local mode):**

1. Look up stream in the catalog to get Galactic coordinate bounds
2. Query Gaia DR3 via ADQL for all stars in the region
3. Save the astropy Table as `gaia_table.ecsv`
4. Extract 5D phase-space features `(ra, dec, pmra, pmdec, parallax)`, drop NaN rows
5. Compute kNN density filtration via GUDHI (or CUDA kernels if GPU available)
6. Save diagrams, point cloud, and `clean_indices` to `persistence.npz`
7. Extract stream candidates by sigma-thresholding feature lifetimes
8. Save `candidates.json` and `candidate_members.npz`
9. Save `metadata.json` with all run parameters

**Pipeline steps (API mode):**

When `TOPOSTREAMS_API_URL` is set, `recover` submits the job remotely instead:

1. POST to `/jobs` with `streamKey`, `nNeighbors`, `sigmaThreshold`
2. Poll `/jobs/{id}` until status is `COMPLETED` or `FAILED`
3. Download result files from presigned S3 URLs to the output directory

### `explore plot <run-dir>`

Generate plots from a saved recovery run.

```bash
uv run explore plot runs/palomar-5/20260218T143012Z/ [OPTIONS]
```

**Options:**

| Option           | Type | Default | Description                      |
| ---------------- | ---- | ------- | -------------------------------- |
| `--homology-dim` | int  | `0`     | Which homology dimension to plot |
| `--dpi`          | int  | `150`   | DPI for saved PNG figures        |

**Outputs:**

- `persistence_diagram.png` — Birth vs. death scatter plot for the chosen homology dimension
- `sky_map.png` — RA/Dec sky projection with candidate members highlighted (only generated if candidates exist and `gaia_table.ecsv` is present)

### `explore status <job-id>`

Check the status of a remote job. Requires `TOPOSTREAMS_API_URL` to be set.

```bash
uv run explore status <job-id>
```

Displays: job ID, stream key, status (PENDING/RUNNING/COMPLETED/FAILED), timestamps, and error message if failed.

### `explore jobs`

List streams from the remote catalog. Requires `TOPOSTREAMS_API_URL` to be set.

```bash
uv run explore jobs
```

Displays the stream catalog from the API as a Rich table.

## API mode

Set the `TOPOSTREAMS_API_URL` environment variable to enable API mode. All requests are signed with AWS SigV4 using your local AWS credentials.

```bash
export TOPOSTREAMS_API_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod

# Submit a job (runs on GPU worker)
uv run explore recover gd-1 --n-neighbors 32

# Check status
uv run explore status <job-id>

# List available streams from the remote catalog
uv run explore jobs
```

The API requires IAM authentication. Configure AWS credentials via environment variables, `~/.aws/credentials`, or an instance profile.

## Stream Catalog

| Key               | Name            | l range | b range  | Expected members |
| ----------------- | --------------- | ------- | -------- | ---------------- |
| `gd-1`            | GD-1            | 135–225 | 30–75    | ~1,689           |
| `palomar-5`       | Palomar 5       | 0–10    | 40–50    | ~500             |
| `jhelum`          | Jhelum          | 335–360 | -55– -35 | ~300             |
| `orphan-chenab`   | Orphan-Chenab   | 160–260 | 30–70    | ~800             |
| `atlas-aliqa-uma` | ATLAS-Aliqa Uma | 225–270 | 25–55    | ~200             |

Coordinates are Galactic longitude (l) and latitude (b) in degrees. These are literature-derived bounding boxes — not precise stream tracks.
