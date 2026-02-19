import * as cdk from 'aws-cdk-lib'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as ssm from 'aws-cdk-lib/aws-ssm'
import type { Construct } from 'constructs'

export interface GitHubOIDCStackProps extends cdk.StackProps {
  /**
   * GitHub repository in format "owner/repo"
   * @example "caverac/topology-streams"
   */
  readonly githubRepo: string

  /**
   * GitHub environments allowed to assume the role.
   * @default ["development", "production"]
   */
  readonly allowedEnvironments?: string[]

  /**
   * ARN of an existing GitHub OIDC provider in the account.
   * When set, the stack imports the provider instead of creating one
   * (AWS allows only one provider per URL per account).
   */
  readonly existingProviderArn?: string
}

/**
 * Creates OIDC provider and IAM role for GitHub Actions deployments.
 *
 * Enables passwordless authentication from GitHub Actions to AWS
 * using OpenID Connect (OIDC) - no long-lived credentials needed.
 */
export class GitHubOIDCStack extends cdk.Stack {
  public readonly role: iam.Role
  public readonly roleArn: string

  constructor(scope: Construct, id: string, props: GitHubOIDCStackProps) {
    super(scope, id, props)

    const {
      githubRepo,
      allowedEnvironments = ['development', 'production'],
      existingProviderArn
    } = props

    const providerArn = existingProviderArn
      ? existingProviderArn
      : new iam.OpenIdConnectProvider(this, 'GitHubOIDCProvider', {
          url: 'https://token.actions.githubusercontent.com',
          clientIds: ['sts.amazonaws.com'],
          thumbprints: [
            '6938fd4d98bab03faadb97b34396831e3780aea1',
            '1c58a3a8518e8759bf075b76b750d4f2df264fcd'
          ]
        }).openIdConnectProviderArn

    const subjectConditions = allowedEnvironments.map(
      (env) => `repo:${githubRepo}:environment:${env}`
    )

    this.role = new iam.Role(this, 'GitHubActionsRole', {
      roleName: 'TopoStreams-GitHubActions-Role',
      description: 'Role assumed by GitHub Actions for TopoStreams deployments',
      maxSessionDuration: cdk.Duration.hours(1),
      assumedBy: new iam.WebIdentityPrincipal(providerArn, {
        StringEquals: {
          'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
        },
        StringLike: {
          'token.actions.githubusercontent.com:sub': subjectConditions
        }
      })
    })

    this.role.addToPolicy(
      new iam.PolicyStatement({
        sid: 'AssumeCDKBootstrapRoles',
        effect: iam.Effect.ALLOW,
        actions: ['sts:AssumeRole'],
        resources: ['arn:aws:iam::*:role/cdk-*']
      })
    )

    this.roleArn = this.role.roleArn

    new ssm.StringParameter(this, 'GitHubActionsRoleArnParam', {
      parameterName: '/topostreams/github-actions/role-arn',
      description: 'IAM role ARN for GitHub Actions OIDC authentication',
      stringValue: this.roleArn
    })
  }
}
