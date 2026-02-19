import * as cdk from 'aws-cdk-lib'
import * as ec2 from 'aws-cdk-lib/aws-ec2'
import * as ecr from 'aws-cdk-lib/aws-ecr'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import * as ssm from 'aws-cdk-lib/aws-ssm'
import { Construct } from 'constructs'
import { SSM } from 'lib/parameters'

interface ComputeStackProps extends cdk.StackProps {
  readonly bucket: s3.IBucket
  readonly tableArn: string
  readonly tableName: string
}

export class ComputeStack extends cdk.Stack {
  readonly queue: sqs.Queue
  readonly dlq: sqs.Queue
  readonly vpc: ec2.Vpc
  readonly ecrRepo: ecr.Repository

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props)

    this.vpc = new ec2.Vpc(this, 'WorkerVpc', {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
        { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 }
      ]
    })

    this.dlq = new sqs.Queue(this, 'DeadLetterQueue', {
      retentionPeriod: cdk.Duration.days(14)
    })

    this.queue = new sqs.Queue(this, 'JobQueue', {
      visibilityTimeout: cdk.Duration.minutes(60),
      deadLetterQueue: {
        queue: this.dlq,
        maxReceiveCount: 3
      }
    })

    this.ecrRepo = new ecr.Repository(this, 'WorkerRepo', {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [{ maxImageCount: 10 }]
    })

    const workerRole = new iam.Role(this, 'WorkerRole', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore')]
    })

    this.queue.grantConsumeMessages(workerRole)
    props.bucket.grantReadWrite(workerRole)
    this.ecrRepo.grantPull(workerRole)

    workerRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:UpdateItem', 'dynamodb:GetItem'],
        resources: [props.tableArn]
      })
    )

    const instanceProfile = new iam.CfnInstanceProfile(this, 'WorkerInstanceProfile', {
      roles: [workerRole.roleName]
    })

    const workerSg = new ec2.SecurityGroup(this, 'WorkerSg', {
      vpc: this.vpc,
      description: 'Security group for GPU worker instances',
      allowAllOutbound: true
    })

    const userData = ec2.UserData.forLinux()
    userData.addCommands(
      'yum install -y docker',
      'systemctl enable docker && systemctl start docker',
      'distribution=$(. /etc/os-release;echo $ID$VERSION_ID)',
      'curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | tee /etc/yum.repos.d/nvidia-container-toolkit.repo',
      'yum install -y nvidia-container-toolkit',
      'nvidia-ctk runtime configure --runtime=docker',
      'systemctl restart docker',
      `aws ecr get-login-password --region ${this.region} | docker login --username AWS --password-stdin ${this.account}.dkr.ecr.${this.region}.amazonaws.com`,
      `docker pull ${this.ecrRepo.repositoryUri}:latest`,
      `docker run -d --gpus all --restart always \\`,
      `  -e QUEUE_URL=${this.queue.queueUrl} \\`,
      `  -e BUCKET_NAME=${props.bucket.bucketName} \\`,
      `  -e TABLE_NAME=${props.tableName} \\`,
      `  -e AWS_DEFAULT_REGION=${this.region} \\`,
      `  ${this.ecrRepo.repositoryUri}:latest`
    )

    new ec2.Instance(this, 'GpuWorker', {
      vpc: this.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      instanceType: new ec2.InstanceType('g4dn.xlarge'),
      machineImage: ec2.MachineImage.latestAmazonLinux2(),
      role: workerRole,
      securityGroup: workerSg,
      userData,
      blockDevices: [
        {
          deviceName: '/dev/xvda',
          volume: ec2.BlockDeviceVolume.ebs(100, { volumeType: ec2.EbsDeviceVolumeType.GP3 })
        }
      ]
    })

    // Suppress cfn-nag warning for instance profile (it's used by the Instance above)
    instanceProfile.node.addDependency(workerRole)

    new ssm.StringParameter(this, 'QueueUrlParam', {
      parameterName: SSM.QUEUE_URL,
      stringValue: this.queue.queueUrl
    })

    new ssm.StringParameter(this, 'QueueArnParam', {
      parameterName: SSM.QUEUE_ARN,
      stringValue: this.queue.queueArn
    })

    new ssm.StringParameter(this, 'DlqUrlParam', {
      parameterName: SSM.DLQ_URL,
      stringValue: this.dlq.queueUrl
    })

    new ssm.StringParameter(this, 'EcrRepoUriParam', {
      parameterName: SSM.ECR_REPO_URI,
      stringValue: this.ecrRepo.repositoryUri
    })
  }
}
