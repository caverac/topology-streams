#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib'
import { ApiStack } from 'lib/api.stack'
import { ComputeStack } from 'lib/compute.stack'
import { GitHubOIDCStack } from 'lib/github-oidc.stack'
import { StorageStack } from 'lib/storage.stack'
import { z } from 'zod'

const envSchema = z.object({
  ENVIRONMENT: z.enum(['development', 'production']),
  AWS_ACCOUNT: z.string(),
  AWS_DEFAULT_REGION: z.string().default('us-east-1')
})

const env = envSchema.parse(process.env)

const cdkEnv = {
  account: env.AWS_ACCOUNT,
  region: env.AWS_DEFAULT_REGION
}

const app = new cdk.App()

const storage = new StorageStack(app, 'TopoStreamsStorage', { env: cdkEnv })

const compute = new ComputeStack(app, 'TopoStreamsCompute', {
  env: cdkEnv,
  bucket: storage.bucket,
  tableArn: storage.table.tableArn,
  tableName: storage.table.tableName
})

new ApiStack(app, 'TopoStreamsApi', {
  env: cdkEnv,
  table: storage.table,
  bucket: storage.bucket,
  queue: compute.queue
})

new GitHubOIDCStack(app, 'TopoStreamsGitHubOIDC', {
  githubRepo: 'caverac/topology-streams',
  existingProviderArn: `arn:aws:iam::${env.AWS_ACCOUNT}:oidc-provider/token.actions.githubusercontent.com`,
  env: cdkEnv
})
