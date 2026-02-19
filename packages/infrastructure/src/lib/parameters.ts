/**
 * SSM parameter name constants for cross-stack references.
 */

const PREFIX = '/topostreams'

export const SSM = {
  BUCKET_NAME: `${PREFIX}/storage/bucket-name`,
  BUCKET_ARN: `${PREFIX}/storage/bucket-arn`,
  TABLE_NAME: `${PREFIX}/storage/table-name`,
  TABLE_ARN: `${PREFIX}/storage/table-arn`,
  QUEUE_URL: `${PREFIX}/compute/queue-url`,
  QUEUE_ARN: `${PREFIX}/compute/queue-arn`,
  DLQ_URL: `${PREFIX}/compute/dlq-url`,
  ECR_REPO_URI: `${PREFIX}/compute/ecr-repo-uri`,
  API_URL: `${PREFIX}/api/url`
} as const
