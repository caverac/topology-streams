---
sidebar_position: 4
---

# worker

The `worker` package is an SQS consumer that runs the stream recovery pipeline on GPU-enabled EC2 instances.

## Module structure

```
worker/
├── main.py         # SQS poll loop with graceful shutdown
├── pipeline.py     # Full stream recovery pipeline (fetch → compute → upload)
├── config.py       # WorkerConfig from environment variables
├── dynamodb.py     # Job status updates (PENDING → RUNNING → COMPLETED/FAILED)
└── s3_io.py        # Result serialization and S3 upload
```

## How it works

### SQS poll loop (`main.py`)

The worker runs a continuous loop:

1. Long-poll SQS with 20-second wait time
2. Receive one message at a time (visibility timeout: 60 minutes)
3. Parse the job payload (`jobId`, `streamKey`, `nNeighbors`, `sigmaThreshold`)
4. Update DynamoDB status to `RUNNING`
5. Execute the pipeline
6. On success: update status to `COMPLETED`, delete the SQS message
7. On failure: update status to `FAILED` with error message (truncated to 1000 chars), message returns to queue after visibility timeout

After 3 failed attempts, messages move to the dead-letter queue.

### Graceful shutdown

Signal handlers (SIGTERM, SIGINT) set a shutdown flag. The poll loop checks this flag between iterations and exits cleanly, allowing any in-progress job to complete.

### Pipeline (`pipeline.py`)

The pipeline mirrors the local `explore recover` flow:

1. Fetch Gaia DR3 data for the stream region
2. Clean phase-space features (drop NaN rows)
3. Compute kNN density filtration via `stream-finder` (uses GPU if available)
4. Extract stream candidates
5. Serialize results (NPZ, JSON, ECSV)
6. Upload all files to S3 under `jobs/{jobId}/`

### Output files (uploaded to S3)

| File                    | Format | Content                                |
| ----------------------- | ------ | -------------------------------------- |
| `gaia_table.ecsv`       | ECSV   | Raw Gaia query result                  |
| `persistence.npz`       | NPZ    | Persistence diagrams (diagram_0, etc.) |
| `candidates.json`       | JSON   | Stream candidate summaries             |
| `candidate_members.npz` | NPZ    | Member star indices per candidate      |
| `metadata.json`         | JSON   | Run parameters and star counts         |

## Configuration

All configuration is via environment variables:

| Variable             | Required | Default   | Description                      |
| -------------------- | -------- | --------- | -------------------------------- |
| `QUEUE_URL`          | Yes      | —         | SQS job queue URL                |
| `BUCKET_NAME`        | Yes      | —         | S3 results bucket name           |
| `TABLE_NAME`         | Yes      | —         | DynamoDB jobs table name         |
| `AWS_DEFAULT_REGION` | No       | us-east-1 | AWS region                       |
| `POLL_INTERVAL`      | No       | 20        | Seconds between SQS polls        |
| `VISIBILITY_TIMEOUT` | No       | 3600      | Message visibility timeout (sec) |

## Deployment

The worker runs as a Docker container on an EC2 `g4dn.xlarge` instance (NVIDIA T4 GPU). The ComputeStack provisions the instance with:

- NVIDIA container toolkit for GPU access
- Docker with automatic image pull from ECR on boot
- IAM role with SQS, S3, and DynamoDB permissions
- Private subnet placement behind a NAT gateway
