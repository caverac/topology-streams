import * as cdk from 'aws-cdk-lib'
import { Template } from 'aws-cdk-lib/assertions'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import { ApiStack } from 'lib/api.stack'

describe('ApiStack', () => {
  let template: Template

  beforeAll(() => {
    const app = new cdk.App()
    const depStack = new cdk.Stack(app, 'DepStack')
    const table = new dynamodb.Table(depStack, 'Table', {
      partitionKey: { name: 'jobId', type: dynamodb.AttributeType.STRING }
    })
    const bucket = new s3.Bucket(depStack, 'Bucket')
    const queue = new sqs.Queue(depStack, 'Queue')

    const stack = new ApiStack(app, 'TestApi', { table, bucket, queue })
    template = Template.fromStack(stack)
  })

  it('creates a REST API', () => {
    template.hasResourceProperties('AWS::ApiGateway::RestApi', {
      Name: 'TopoStreams API'
    })
  })

  it('creates 4 Lambda functions', () => {
    template.resourceCountIs('AWS::Lambda::Function', 4)
  })

  it('creates Lambda functions with Node.js 22 and ARM64', () => {
    template.hasResourceProperties('AWS::Lambda::Function', {
      Runtime: 'nodejs22.x',
      Architectures: ['arm64'],
      MemorySize: 256,
      Timeout: 30
    })
  })

  it('creates API methods with IAM auth', () => {
    template.hasResourceProperties('AWS::ApiGateway::Method', {
      AuthorizationType: 'AWS_IAM',
      HttpMethod: 'POST'
    })
    template.hasResourceProperties('AWS::ApiGateway::Method', {
      AuthorizationType: 'AWS_IAM',
      HttpMethod: 'GET'
    })
  })

  it('creates SSM parameter for API URL', () => {
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/api/url'
    })
  })
})
