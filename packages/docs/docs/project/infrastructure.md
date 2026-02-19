---
sidebar_position: 6
---

# infrastructure

The `infrastructure` package defines the AWS backend as code using CDK (TypeScript).

## Stacks

### StorageStack

Persistent data stores for job tracking and results.

| Resource       | Type     | Details                                              |
| -------------- | -------- | ---------------------------------------------------- |
| Results bucket | S3       | S3-managed encryption, IA transition at 30 days      |
| Jobs table     | DynamoDB | Partition key: `jobId`, PAY_PER_REQUEST, TTL enabled |

### ComputeStack

GPU worker infrastructure for running stream recovery pipelines.

| Resource          | Type     | Details                                                                |
| ----------------- | -------- | ---------------------------------------------------------------------- |
| VPC               | VPC      | 2 AZs, 1 NAT gateway, public + private subnets                         |
| Job queue         | SQS      | 60-min visibility timeout                                              |
| Dead-letter queue | SQS      | 14-day retention, max 3 receive attempts                               |
| Worker repo       | ECR      | Max 10 images                                                          |
| Worker role       | IAM Role | EC2 assume, SQS + S3 + DynamoDB permissions                            |
| GPU instance      | EC2      | `g4dn.xlarge` (T4), 100GB GP3, private subnet, Docker + NVIDIA toolkit |

### ApiStack

REST API for submitting and tracking recovery jobs.

| Resource    | Type             | Details                                                  |
| ----------- | ---------------- | -------------------------------------------------------- |
| API Gateway | RestApi          | IAM auth (SigV4) on all routes                           |
| SubmitJob   | Lambda (Node 22) | POST `/jobs` — creates job, sends SQS                    |
| JobStatus   | Lambda (Node 22) | GET `/jobs/{id}` — reads DynamoDB                        |
| JobResults  | Lambda (Node 22) | GET `/jobs/{id}/results` — presigned S3 URLs (1h expiry) |
| Catalog     | Lambda (Node 22) | GET `/catalog` — hardcoded stream list                   |

All Lambdas: ARM64, 256 MB memory, 30-second timeout, esbuild-bundled.

### GitHubOIDCStack

Passwordless GitHub Actions deployments via OpenID Connect.

| Resource        | Type     | Details                                        |
| --------------- | -------- | ---------------------------------------------- |
| OIDC provider   | IAM OIDC | `token.actions.githubusercontent.com`          |
| Deployment role | IAM Role | 1-hour sessions, scoped to repo + environments |

## Cross-stack references

Stacks communicate via SSM parameters under the `/topostreams` prefix:

| Parameter                           | Source       | Consumers              |
| ----------------------------------- | ------------ | ---------------------- |
| `/topostreams/storage/bucket-name`  | StorageStack | ComputeStack, ApiStack |
| `/topostreams/storage/bucket-arn`   | StorageStack | ComputeStack, ApiStack |
| `/topostreams/storage/table-name`   | StorageStack | ComputeStack, ApiStack |
| `/topostreams/storage/table-arn`    | StorageStack | ComputeStack, ApiStack |
| `/topostreams/compute/queue-url`    | ComputeStack | ApiStack               |
| `/topostreams/compute/queue-arn`    | ComputeStack | ApiStack               |
| `/topostreams/compute/dlq-url`      | ComputeStack | —                      |
| `/topostreams/compute/ecr-repo-uri` | ComputeStack | CI/CD                  |
| `/topostreams/api/url`              | ApiStack     | explore CLI            |

## Authentication

All API Gateway routes use **IAM authentication** (SigV4). Callers must sign requests with valid AWS credentials. The `explore` CLI handles this automatically via `boto3`/`botocore` credential resolution.
