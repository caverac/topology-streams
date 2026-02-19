---
sidebar_position: 1
---

# Gaia DR3 Catalog

## Overview

Gaia Data Release 3 (DR3), released 13 June 2022, is the primary data source for TopoStreams. The full catalog contains ~1.8 billion sources with astrometric, photometric, and spectroscopic measurements.

All data is **public and free to access**.

## Relevant columns

For persistent homology stream detection, the minimum feature vector per star is:

| Column      | Description          | Coverage      | Bytes       |
| ----------- | -------------------- | ------------- | ----------- |
| `source_id` | Unique identifier    | ~1.8B sources | 8 (int64)   |
| `ra`        | Right ascension      | ~1.8B sources | 8 (float64) |
| `dec`       | Declination          | ~1.8B sources | 8 (float64) |
| `pmra`      | Proper motion in RA  | ~1.5B sources | 8 (float64) |
| `pmdec`     | Proper motion in Dec | ~1.5B sources | 8 (float64) |
| `parallax`  | Distance proxy       | ~1.5B sources | 8 (float64) |

Optional additions:

| Column            | Description            | Coverage      |
| ----------------- | ---------------------- | ------------- |
| `radial_velocity` | Line-of-sight velocity | ~33M sources  |
| `phot_g_mean_mag` | G-band magnitude       | ~1.5B sources |
| `bp_rp`           | Color index            | ~1.5B sources |

The **5D feature vector** `(ra, dec, pmra, pmdec, parallax)` at 48 bytes per row covers ~1.5 billion sources.

## Access methods

### Web UI

The ESA Gaia Archive provides a web interface for ADQL queries:

- **URL**: [gea.esac.esa.int/archive](https://gea.esac.esa.int/archive/)

### Python (astroquery)

```python
from astroquery.gaia import Gaia

job = Gaia.launch_job_async("""
    SELECT source_id, ra, dec, pmra, pmdec, parallax,
           radial_velocity, phot_g_mean_mag, bp_rp
    FROM gaiadr3.gaia_source
    WHERE parallax_over_error > 5
      AND ruwe < 1.4
      AND b > 30
""")
results = job.get_results()
```

- **Docs**: [astroquery.gaia](https://astroquery.readthedocs.io/en/latest/gaia/gaia.html)

### AWS S3 (free, no account needed)

Gaia DR3 is hosted as open data on AWS:

```bash
aws s3 ls --no-sign-request s3://stpubdata/gaia/
```

- **Bucket**: `s3://stpubdata/gaia/`
- **Region**: `us-east-1`
- **Format**: HATS (spatial indexing for efficient cross-matching)
- **Registry**: [registry.opendata.aws/gaia-dr3](https://registry.opendata.aws/gaia-dr3/)

Use [LSDB](https://lsdb.readthedocs.io/) for spatial queries directly against the bucket.

### Helper libraries

- **gaia_tools** (Jo Bovy): Cross-matches and caching — [GitHub](https://github.com/jobovy/gaia_tools)
- **ADQL guide**: [cosmos.esa.int](https://www.cosmos.esa.int/web/gaia-users/archive/writing-queries)
- **Tutorials**: [Astropy Gaia tutorials](https://learn.astropy.org/tutorials/gaia-galactic-orbits.html)

## Quality cuts

Standard quality filters for stream detection:

```sql
WHERE parallax_over_error > 5      -- reliable distances
  AND ruwe < 1.4                   -- good astrometric solutions
  AND b > 30                       -- high galactic latitude (less crowded)
  AND phot_g_mean_mag < 20         -- brightness limit
```

## Official documentation

- [Gaia DR3 contents summary](https://www.cosmos.esa.int/web/gaia/dr3)
- [Gaia DR3 full documentation](https://gea.esac.esa.int/archive/documentation/GDR3/)
- [Column descriptions](https://irsa.ipac.caltech.edu/data/Gaia/dr3/gaia_dr3_source_colDescriptions.html)
