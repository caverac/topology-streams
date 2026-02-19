import * as cdk from 'aws-cdk-lib'
import { Template } from 'aws-cdk-lib/assertions'
import * as s3 from 'aws-cdk-lib/aws-s3'
import { ComputeStack } from 'lib/compute.stack'

describe('ComputeStack', () => {
  let template: Template

  beforeAll(() => {
    const app = new cdk.App()
    const bucket = new s3.Bucket(new cdk.Stack(app, 'BucketStack'), 'Bucket')
    const stack = new ComputeStack(app, 'TestCompute', {
      bucket,
      tableArn: 'arn:aws:dynamodb:us-east-1:123456789012:table/TestTable',
      tableName: 'TestTable'
    })
    template = Template.fromStack(stack)
  })

  it('creates a VPC with public and private subnets', () => {
    template.hasResourceProperties('AWS::EC2::VPC', {})
    template.resourceCountIs('AWS::EC2::Subnet', 4) // 2 public + 2 private
  })

  it('creates an SQS queue with DLQ', () => {
    template.hasResourceProperties('AWS::SQS::Queue', {
      VisibilityTimeout: 3600
    })
    // DLQ exists
    template.resourceCountIs('AWS::SQS::Queue', 2)
  })

  it('creates an ECR repository', () => {
    template.resourceCountIs('AWS::ECR::Repository', 1)
  })

  it('creates an EC2 instance with g4dn.xlarge', () => {
    template.hasResourceProperties('AWS::EC2::Instance', {
      InstanceType: 'g4dn.xlarge'
    })
  })

  it('creates SSM parameters for queue and ECR', () => {
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/compute/queue-url'
    })
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/compute/queue-arn'
    })
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/compute/dlq-url'
    })
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/compute/ecr-repo-uri'
    })
  })
})
