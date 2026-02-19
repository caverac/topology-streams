---
sidebar_position: 4
---

# References

## Stream discovery & catalogs

| Paper                                         | Year | Method                      | Data                | Link                                                                                       |
| --------------------------------------------- | ---- | --------------------------- | ------------------- | ------------------------------------------------------------------------------------------ |
| Malhan & Ibata — STREAMFINDER I               | 2018 | Matched filter (orbits)     | Gaia DR2            | [arXiv:1804.11338](https://arxiv.org/abs/1804.11338)                                       |
| Ibata et al. — Streams of the Gaping Abyss    | 2019 | STREAMFINDER                | Gaia DR2            | [arXiv:1901.07566](https://arxiv.org/abs/1901.07566)                                       |
| Yuan et al. — StarGO / Cetus                  | 2019 | Self-organizing maps        | Gaia DR2 + LAMOST   | [ADS](https://ui.adsabs.harvard.edu/abs/2019ApJ...881..164Y)                               |
| Malhan et al. — Galactic Acceleration Field I | 2021 | STREAMFINDER + spectroscopy | Gaia DR2/EDR3       | [arXiv:2012.05245](https://arxiv.org/abs/2012.05245)                                       |
| Shih & Buckley — Via Machinae 1.0             | 2021 | Unsupervised ML (ANODE)     | Gaia DR2            | [arXiv:2104.12789](https://arxiv.org/abs/2104.12789)                                       |
| Mateu — galstreams library                    | 2023 | Catalog / library           | Multi-survey        | [arXiv:2204.10326](https://arxiv.org/abs/2204.10326)                                       |
| Shih & Buckley — Via Machinae 2.0             | 2023 | Unsupervised ML (ANODE)     | Gaia DR2            | [arXiv:2303.01529](https://arxiv.org/abs/2303.01529)                                       |
| Ibata et al. — STREAMFINDER Atlas             | 2024 | Matched filter (orbits)     | Gaia DR3            | [arXiv:2311.17202](https://arxiv.org/abs/2311.17202)                                       |
| New tidal stream (northern sky)               | 2024 | Phase-space analysis        | Gaia DR3            | [arXiv:2404.03257](https://arxiv.org/html/2404.03257)                                      |
| Split stream in SMC periphery                 | 2024 | —                           | Gaia                | [MNRAS 533](https://academic.oup.com/mnras/article/533/3/3238/7723691)                     |
| SkyCURTAINs                                   | 2024 | Weakly-supervised ML        | Gaia DR2            | [arXiv:2405.12131](https://arxiv.org/abs/2405.12131)                                       |
| CWoLa anomaly detection                       | 2024 | Weakly-supervised ML        | Gaia                | [arXiv:2305.03761](https://arxiv.org/abs/2305.03761)                                       |
| Stellar wakes — deep learning                 | 2024 | Deep learning               | Gaia                | [arXiv:2412.02749](https://arxiv.org/abs/2412.02749)                                       |
| Bonaca et al. — Review                        | 2025 | —                           | —                   | [arXiv:2405.19410](https://arxiv.org/abs/2405.19410)                                       |
| GD-1 density & membership                     | 2025 | Flexible models             | Gaia DR3            | [arXiv:2502.13236](https://arxiv.org/html/2502.13236)                                      |
| StarStream (GC streams)                       | 2025 | Physics-inspired model      | Gaia DR3            | [arXiv:2510.14924](https://arxiv.org/abs/2510.14924)                                       |
| StarStream algorithm                          | 2025 | Physics-inspired model      | —                   | [arXiv:2510.14929](https://arxiv.org/abs/2510.14929)                                       |
| Via Machinae 3.0                              | 2025 | ML (CATHODE)                | Gaia DR2            | [arXiv:2509.08064](https://arxiv.org/abs/2509.08064)                                       |
| MW halo substructures                         | 2025 | —                           | Gaia                | [arXiv:2507.08074](https://arxiv.org/html/2507.08074)                                      |
| Chemo-kinematic tagging                       | 2025 | Clustering (chem+kin)       | Gaia + spectroscopy | [A&A 2025](https://www.aanda.org/articles/aa/full_html/2025/12/aa54934-25/aa54934-25.html) |

## TDA / persistent homology in astronomy

| Paper                               | Year | Topic                      | Link                                                                                       |
| ----------------------------------- | ---- | -------------------------- | ------------------------------------------------------------------------------------------ |
| Cosmic web with TDA                 | 2018 | LSS filaments/voids        | [ADS](https://ui.adsabs.harvard.edu/abs/2018AAS...23121307C)                               |
| Intro to TDA for physicists         | 2019 | TDA tutorial (LGM to FRBs) | [arXiv:1904.11044](https://arxiv.org/abs/1904.11044)                                       |
| Persistent homology in cosmic shear | 2021 | Weak lensing constraints   | [A&A 2021](https://www.aanda.org/articles/aa/full_html/2021/04/aa39048-20/aa39048-20.html) |
| TDA and ML survey                   | 2023 | Review                     | [Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/23746149.2023.2202331)     |
| TDA: simulated galaxies vs DM halos | 2023 | Galaxy morphology          | [MNRAS 2023](https://academic.oup.com/mnras/article/523/4/5738/7197452)                    |
| Exoplanet detection with TDA        | 2025 | Kepler light curves        | [KoreaScience](https://www.koreascience.kr/article/JAKO202520261203526.pub)                |
| TDA beyond PH — review              | 2025 | Comprehensive review       | [arXiv:2507.19504](https://arxiv.org/abs/2507.19504)                                       |

## Data sources & tools

| Resource         | Description                          | Link                                                               |
| ---------------- | ------------------------------------ | ------------------------------------------------------------------ |
| ESA Gaia Archive | Primary data access (ADQL queries)   | [gea.esac.esa.int](https://gea.esac.esa.int/archive/)              |
| Gaia DR3 on AWS  | Free S3 open data                    | [AWS Registry](https://registry.opendata.aws/gaia-dr3/)            |
| astroquery.gaia  | Python programmatic access           | [Docs](https://astroquery.readthedocs.io/en/latest/gaia/gaia.html) |
| gaia_tools       | Cross-match & caching helpers        | [GitHub](https://github.com/jobovy/gaia_tools)                     |
| galstreams       | Stream footprints & tracks library   | [GitHub](https://github.com/cmateu/galstreams)                     |
| StarStream_DR    | GC stream member star catalogs       | [GitHub](https://github.com/ybillchen/StarStream_DR)               |
| StreamCatalogs   | Simulated GC streams (TNG50, FIRE-2) | [GitHub](https://github.com/cholm-hansen/StreamCatalogs)           |
