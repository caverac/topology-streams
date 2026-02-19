import { DynamoDBClient, GetItemCommand } from '@aws-sdk/client-dynamodb'
import { GetObjectCommand, S3Client } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { unmarshall } from '@aws-sdk/util-dynamodb'
import type { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda'

import { JobResultsEnv } from '../../shared/env'

const ddb = new DynamoDBClient({})
const s3 = new S3Client({})

const RESULT_FILES = [
  'gaia_table.ecsv',
  'persistence.npz',
  'candidates.json',
  'candidate_members.npz',
  'metadata.json'
]

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  const env = JobResultsEnv.parse(process.env)

  const jobId = event.pathParameters?.id
  if (!jobId) {
    return { statusCode: 400, body: JSON.stringify({ error: 'Missing job ID' }) }
  }

  const jobResult = await ddb.send(
    new GetItemCommand({
      TableName: env.TABLE_NAME,
      Key: { jobId: { S: jobId } }
    })
  )

  if (!jobResult.Item) {
    return { statusCode: 404, body: JSON.stringify({ error: 'Job not found' }) }
  }

  const record = unmarshall(jobResult.Item)
  if (record.status !== 'COMPLETED') {
    return {
      statusCode: 409,
      body: JSON.stringify({ error: 'Job not completed', status: record.status })
    }
  }

  const urls: Record<string, string> = {}
  for (const file of RESULT_FILES) {
    const command = new GetObjectCommand({
      Bucket: env.BUCKET_NAME,
      Key: `jobs/${jobId}/${file}`
    })
    urls[file] = await getSignedUrl(s3, command, { expiresIn: 3600 })
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ jobId, files: urls })
  }
}
