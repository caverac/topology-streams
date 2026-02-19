---
sidebar_position: 3
---

# Storage & Cost Estimates

## Dataset size — coordinates only

For ~1.5 billion sources with 5-parameter astrometry:

| Column            | Type    | Bytes        |
| ----------------- | ------- | ------------ |
| `source_id`       | int64   | 8            |
| `ra`              | float64 | 8            |
| `dec`             | float64 | 8            |
| `pmra`            | float64 | 8            |
| `pmdec`           | float64 | 8            |
| `parallax`        | float64 | 8            |
| **Total per row** |         | **48 bytes** |

| Format                                     | Size          |
| ------------------------------------------ | ------------- |
| Raw uncompressed                           | **~72 GB**    |
| Parquet / compressed                       | **~20-30 GB** |
| High-latitude subset only (\|b\| > 30 deg) | **~5-10 GB**  |

## Gaia DR3 is already on AWS (free)

The full catalog is hosted as open data on AWS S3 — **no account required**:

```bash
aws s3 ls --no-sign-request s3://stpubdata/gaia/
```

| Property | Value                                                                     |
| -------- | ------------------------------------------------------------------------- |
| Bucket   | `s3://stpubdata/gaia/`                                                    |
| Region   | `us-east-1`                                                               |
| Format   | HATS (spatial indexing)                                                   |
| Cost     | **Free to read**                                                          |
| Registry | [registry.opendata.aws/gaia-dr3](https://registry.opendata.aws/gaia-dr3/) |

## AWS S3 cost if storing your own subset

| Tier                 | $/GB/month | ~30 GB (compressed) | ~72 GB (raw) |
| -------------------- | ---------- | ------------------- | ------------ |
| S3 Standard          | $0.023     | **$0.69/mo**        | **$1.66/mo** |
| S3 Infrequent Access | $0.0125    | **$0.38/mo**        | **$0.90/mo** |
| S3 One Zone-IA       | $0.01      | **$0.30/mo**        | **$0.72/mo** |

**Bottom line: $0.30 - $1.70/month.** Essentially negligible.

## Practical recommendation

| Option                                     | Storage cost | Best for                    |
| ------------------------------------------ | ------------ | --------------------------- |
| Query on demand via `astroquery.gaia`      | $0           | Exploration, small patches  |
| Read from `s3://stpubdata/gaia/` with LSDB | $0           | Large-scale spatial queries |
| Cache high-latitude subset as Parquet      | ~$0.30/mo    | Repeated local analysis     |
