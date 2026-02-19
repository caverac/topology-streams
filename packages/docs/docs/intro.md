---
sidebar_position: 1
slug: /
---

# TopoStreams

**Stellar stream discovery using persistent homology on Gaia data.**

## Motivation

Over 120 stellar streams have been discovered in the Milky Way halo, primarily using ESA's Gaia mission data. Current detection methods fall into two camps:

- **Model-dependent**: STREAMFINDER, StarStream — require assumptions about orbits or the Galactic potential.
- **ML-based (model-agnostic)**: Via Machinae, SkyCURTAINs — use neural density estimators borrowed from particle physics.

**Persistent homology (PH) has never been applied to this problem**, despite being a natural fit. Streams are 1D manifolds embedded in 5-6D phase space — exactly the kind of topological structure PH is designed to detect.

## What this project does

TopoStreams applies topological data analysis (TDA) — specifically persistent homology — to Gaia phase-space data to discover and characterize stellar streams. The approach is:

- **Model-agnostic**: No assumptions about orbits, Galactic potential, or isochrones
- **Scale-free**: Captures features across all spatial scales via persistence diagrams
- **Noise-robust**: Naturally distinguishes persistent topological features from noise
- **Complementary**: Can detect wide, short, or morphologically unusual streams that matched-filter methods miss

## Project structure

```
topology-streams/
├── packages/
│   ├── stream-finder/      # Python — PH-based stream detection library
│   ├── explore/            # Python — CLI + AWS API client
│   ├── worker/             # Python — SQS consumer for GPU pipeline
│   ├── cuda-kernels/       # C++/CUDA — GPU-accelerated kernels + Python bindings
│   ├── infrastructure/     # TypeScript — AWS CDK (API Gateway, Lambda, SQS, S3, DynamoDB)
│   └── docs/               # This documentation
├── package.json            # Yarn workspace root
├── pyproject.toml          # uv workspace root
└── .github/workflows/      # CI/CD pipelines
```

The pipeline runs in two modes: **locally** (direct `stream-finder` calls via the `explore` CLI) or **on AWS** (jobs submitted to API Gateway, processed by GPU workers on EC2 g4dn instances).

Ready to try it? Head to the [Getting Started](guides/getting-started) guide.
