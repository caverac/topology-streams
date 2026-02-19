---
sidebar_position: 3
---

# explore

The `explore` package provides a CLI and AWS API client for running stream recovery pipelines on Gaia DR3 data.

## Installation

```bash
# From the monorepo root
uv sync --group dev
```

## Module structure

```
explore/
├── cli.py              # Click CLI entry point
├── commands/
│   ├── catalog.py      # List available streams
│   ├── recover.py      # Run recovery pipeline (local or API)
│   ├── plot.py         # Generate visualizations from run output
│   ├── status.py       # Check remote job status (API mode)
│   └── jobs.py         # List remote catalog (API mode)
├── _api_client.py      # SigV4-signed HTTP client for API Gateway
├── _config.py          # API configuration from environment
├── _types.py           # KnownStream, RecoveryResult dataclasses
├── _console.py         # Shared Rich console
└── _constants.py       # Shared constants
```

## Two modes of operation

### Local mode (default)

When no API URL is configured, `explore recover` runs the full pipeline locally using `stream-finder`:

1. Fetch Gaia DR3 data for the stream region
2. Clean phase-space features (drop NaN rows)
3. Compute kNN density filtration (CPU or GPU)
4. Extract stream candidates via sigma threshold
5. Save results to a timestamped local directory

### API mode

When `TOPOSTREAMS_API_URL` is set, `explore recover` submits the job to the AWS backend:

1. POST to `/jobs` with stream key and parameters
2. Poll `/jobs/{id}` until COMPLETED or FAILED
3. Download results from presigned S3 URLs

API-only commands (`status`, `jobs`) are available when the API URL is configured.

## Environment variables

| Variable              | Required | Description                                       |
| --------------------- | -------- | ------------------------------------------------- |
| `TOPOSTREAMS_API_URL` | No       | API Gateway URL — enables API mode                |
| `TOPOSTREAMS_REGION`  | No       | AWS region for SigV4 signing (default: us-east-1) |

API mode requires valid AWS credentials (via environment, profile, or instance role) for SigV4 request signing.

## Dependencies

| Package         | Purpose                       |
| --------------- | ----------------------------- |
| `stream-finder` | Core topology library         |
| `click`         | CLI framework                 |
| `rich`          | Terminal output and tables    |
| `boto3`         | AWS SDK (SigV4 signing)       |
| `botocore`      | AWS request signing internals |
