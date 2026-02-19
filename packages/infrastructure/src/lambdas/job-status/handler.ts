import { DynamoDBClient, GetItemCommand } from '@aws-sdk/client-dynamodb'
import { unmarshall } from '@aws-sdk/util-dynamodb'
import type { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda'

import { JobStatusEnv } from '../../shared/env'

const ddb = new DynamoDBClient({})

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  const env = JobStatusEnv.parse(process.env)

  const jobId = event.pathParameters?.id
  if (!jobId) {
    return { statusCode: 400, body: JSON.stringify({ error: 'Missing job ID' }) }
  }

  const result = await ddb.send(
    new GetItemCommand({
      TableName: env.TABLE_NAME,
      Key: { jobId: { S: jobId } }
    })
  )

  if (!result.Item) {
    return { statusCode: 404, body: JSON.stringify({ error: 'Job not found' }) }
  }

  const record = unmarshall(result.Item)
  return {
    statusCode: 200,
    body: JSON.stringify({
      jobId: record.jobId,
      streamKey: record.streamKey,
      status: record.status,
      createdAt: record.createdAt,
      updatedAt: record.updatedAt,
      error: record.error
    })
  }
}
