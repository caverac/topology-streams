import * as cdk from 'aws-cdk-lib'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as ssm from 'aws-cdk-lib/aws-ssm'
import { Construct } from 'constructs'
import { SSM } from 'lib/parameters'

export class StorageStack extends cdk.Stack {
  readonly bucket: s3.Bucket
  readonly table: dynamodb.Table

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    this.bucket = new s3.Bucket(this, 'ResultsBucket', {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30)
            }
          ]
        }
      ]
    })

    this.table = new dynamodb.Table(this, 'JobsTable', {
      partitionKey: { name: 'jobId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      timeToLiveAttribute: 'ttl'
    })

    new ssm.StringParameter(this, 'BucketNameParam', {
      parameterName: SSM.BUCKET_NAME,
      stringValue: this.bucket.bucketName
    })

    new ssm.StringParameter(this, 'BucketArnParam', {
      parameterName: SSM.BUCKET_ARN,
      stringValue: this.bucket.bucketArn
    })

    new ssm.StringParameter(this, 'TableNameParam', {
      parameterName: SSM.TABLE_NAME,
      stringValue: this.table.tableName
    })

    new ssm.StringParameter(this, 'TableArnParam', {
      parameterName: SSM.TABLE_ARN,
      stringValue: this.table.tableArn
    })
  }
}
