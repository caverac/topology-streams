import { randomUUID } from 'node:crypto'

import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb'
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs'
import { marshall } from '@aws-sdk/util-dynamodb'
import type { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda'

import { SubmitJobEnv } from '../../shared/env'
import { SubmitJobRequestSchema } from '../../shared/types'

const ddb = new DynamoDBClient({})
const sqs = new SQSClient({})

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  const env = SubmitJobEnv.parse(process.env)

  const parseResult = SubmitJobRequestSchema.safeParse(JSON.parse(event.body ?? '{}'))
  if (!parseResult.success) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Invalid request', details: parseResult.error.flatten() })
    }
  }

  const { streamKey, nNeighbors, sigmaThreshold } = parseResult.data
  const jobId = randomUUID()
  const now = new Date().toISOString()
  const ttl = Math.floor(Date.now() / 1000) + 7 * 24 * 60 * 60 // 7 days

  const record = {
    jobId,
    streamKey,
    status: 'PENDING' as const,
    nNeighbors,
    sigmaThreshold,
    createdAt: now,
    updatedAt: now,
    ttl
  }

  await ddb.send(
    new PutItemCommand({
      TableName: env.TABLE_NAME,
      Item: marshall(record)
    })
  )

  await sqs.send(
    new SendMessageCommand({
      QueueUrl: env.QUEUE_URL,
      MessageBody: JSON.stringify({ jobId, streamKey, nNeighbors, sigmaThreshold })
    })
  )

  return {
    statusCode: 201,
    body: JSON.stringify({ jobId, status: 'PENDING' })
  }
}
