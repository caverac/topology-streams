import * as path from 'node:path'

import * as cdk from 'aws-cdk-lib'
import * as apigateway from 'aws-cdk-lib/aws-apigateway'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import { NodejsFunction } from 'aws-cdk-lib/aws-lambda-nodejs'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import * as ssm from 'aws-cdk-lib/aws-ssm'
import { Construct } from 'constructs'
import { SSM } from 'lib/parameters'

interface ApiStackProps extends cdk.StackProps {
  readonly table: dynamodb.ITable
  readonly bucket: s3.IBucket
  readonly queue: sqs.IQueue
}

export class ApiStack extends cdk.Stack {
  readonly api: apigateway.RestApi

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props)

    this.api = new apigateway.RestApi(this, 'TopoStreamsApi', {
      restApiName: 'TopoStreams API',
      defaultMethodOptions: {
        authorizationType: apigateway.AuthorizationType.IAM
      }
    })

    const jobsResource = this.api.root.addResource('jobs')
    const jobResource = jobsResource.addResource('{id}')
    const resultsResource = jobResource.addResource('results')
    const catalogResource = this.api.root.addResource('catalog')

    // POST /jobs
    const submitFn = this.createApiLambda('SubmitJob', {
      entry: path.join(__dirname, '..', 'lambdas', 'submit-job', 'handler.ts'),
      environment: {
        TABLE_NAME: props.table.tableName,
        QUEUE_URL: props.queue.queueUrl
      }
    })
    props.table.grantWriteData(submitFn)
    props.queue.grantSendMessages(submitFn)
    jobsResource.addMethod('POST', new apigateway.LambdaIntegration(submitFn))

    // GET /jobs/{id}
    const statusFn = this.createApiLambda('JobStatus', {
      entry: path.join(__dirname, '..', 'lambdas', 'job-status', 'handler.ts'),
      environment: {
        TABLE_NAME: props.table.tableName
      }
    })
    props.table.grantReadData(statusFn)
    jobResource.addMethod('GET', new apigateway.LambdaIntegration(statusFn))

    // GET /jobs/{id}/results
    const resultsFn = this.createApiLambda('JobResults', {
      entry: path.join(__dirname, '..', 'lambdas', 'job-results', 'handler.ts'),
      environment: {
        TABLE_NAME: props.table.tableName,
        BUCKET_NAME: props.bucket.bucketName
      }
    })
    props.table.grantReadData(resultsFn)
    props.bucket.grantRead(resultsFn)
    resultsFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['s3:GetObject'],
        resources: [props.bucket.arnForObjects('jobs/*')]
      })
    )
    resultsResource.addMethod('GET', new apigateway.LambdaIntegration(resultsFn))

    // GET /catalog
    const catalogFn = this.createApiLambda('Catalog', {
      entry: path.join(__dirname, '..', 'lambdas', 'catalog', 'handler.ts'),
      environment: {}
    })
    catalogResource.addMethod('GET', new apigateway.LambdaIntegration(catalogFn))

    new ssm.StringParameter(this, 'ApiUrlParam', {
      parameterName: SSM.API_URL,
      stringValue: this.api.url
    })
  }

  private createApiLambda(
    name: string,
    opts: { entry: string; environment: Record<string, string> }
  ): NodejsFunction {
    return new NodejsFunction(this, name, {
      entry: opts.entry,
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      architecture: lambda.Architecture.ARM_64,
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      environment: opts.environment,
      bundling: {
        minify: true,
        sourceMap: true,
        target: 'node22'
      }
    })
  }
}
