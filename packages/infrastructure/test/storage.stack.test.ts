import * as cdk from 'aws-cdk-lib'
import { Template } from 'aws-cdk-lib/assertions'
import { StorageStack } from 'lib/storage.stack'

describe('StorageStack', () => {
  let template: Template

  beforeAll(() => {
    const app = new cdk.App()
    const stack = new StorageStack(app, 'TestStorage')
    template = Template.fromStack(stack)
  })

  it('creates an S3 bucket with encryption and block public access', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketEncryption: {
        ServerSideEncryptionConfiguration: [
          { ServerSideEncryptionByDefault: { SSEAlgorithm: 'AES256' } }
        ]
      },
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true
      }
    })
  })

  it('creates an S3 bucket with IA lifecycle rule', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      LifecycleConfiguration: {
        Rules: [
          {
            Transitions: [{ StorageClass: 'STANDARD_IA', TransitionInDays: 30 }],
            Status: 'Enabled'
          }
        ]
      }
    })
  })

  it('creates a DynamoDB table with PAY_PER_REQUEST and TTL', () => {
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      KeySchema: [{ AttributeName: 'jobId', KeyType: 'HASH' }],
      BillingMode: 'PAY_PER_REQUEST',
      TimeToLiveSpecification: {
        AttributeName: 'ttl',
        Enabled: true
      }
    })
  })

  it('creates SSM parameters for bucket and table', () => {
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/storage/bucket-name'
    })
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/storage/bucket-arn'
    })
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/storage/table-name'
    })
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/storage/table-arn'
    })
  })
})
