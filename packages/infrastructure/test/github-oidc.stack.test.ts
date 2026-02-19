import * as cdk from 'aws-cdk-lib'
import { Match, Template } from 'aws-cdk-lib/assertions'
import { GitHubOIDCStack } from 'lib/github-oidc.stack'

function createTemplate(
  githubRepo = 'caverac/topology-streams',
  allowedEnvironments?: string[],
  existingProviderArn?: string
): Template {
  const app = new cdk.App()
  const stack = new GitHubOIDCStack(app, 'TestGitHubOIDC', {
    githubRepo,
    allowedEnvironments,
    existingProviderArn,
    env: { account: '123456789012', region: 'us-east-1' }
  })
  return Template.fromStack(stack)
}

describe('GitHubOIDCStack', () => {
  const template = createTemplate()

  test('creates an OIDC provider for GitHub Actions', () => {
    template.hasResourceProperties('Custom::AWSCDKOpenIdConnectProvider', {
      Url: 'https://token.actions.githubusercontent.com',
      ClientIDList: ['sts.amazonaws.com']
    })
  })

  test('IAM role has correct name', () => {
    template.hasResourceProperties('AWS::IAM::Role', {
      RoleName: 'TopoStreams-GitHubActions-Role',
      MaxSessionDuration: 3600
    })
  })

  test('trust policy requires correct audience', () => {
    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Condition: Match.objectLike({
              StringEquals: Match.objectLike({
                'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
              })
            })
          })
        ])
      }
    })
  })

  test('trust policy allows development and production by default', () => {
    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Condition: Match.objectLike({
              StringLike: Match.objectLike({
                'token.actions.githubusercontent.com:sub': [
                  'repo:caverac/topology-streams:environment:development',
                  'repo:caverac/topology-streams:environment:production'
                ]
              })
            })
          })
        ])
      }
    })
  })

  test('has sts:AssumeRole policy for CDK bootstrap roles', () => {
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: 'sts:AssumeRole',
            Effect: 'Allow',
            Resource: 'arn:aws:iam::*:role/cdk-*'
          })
        ])
      }
    })
  })

  test('creates SSM parameter with role ARN', () => {
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topostreams/github-actions/role-arn',
      Type: 'String'
    })
  })

  test('custom environments override defaults', () => {
    const customTemplate = createTemplate('caverac/topology-streams', ['production'])
    customTemplate.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Condition: Match.objectLike({
              StringLike: Match.objectLike({
                'token.actions.githubusercontent.com:sub': [
                  'repo:caverac/topology-streams:environment:production'
                ]
              })
            })
          })
        ])
      }
    })
  })
})

describe('GitHubOIDCStack (existing provider)', () => {
  const existingArn = 'arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com'
  const template = createTemplate('caverac/topology-streams', undefined, existingArn)

  test('does not create a new OIDC provider', () => {
    template.resourceCountIs('Custom::AWSCDKOpenIdConnectProvider', 0)
  })

  test('IAM role still references the provider in trust policy', () => {
    template.hasResourceProperties('AWS::IAM::Role', {
      RoleName: 'TopoStreams-GitHubActions-Role',
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Condition: Match.objectLike({
              StringEquals: Match.objectLike({
                'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
              })
            }),
            Principal: Match.objectLike({
              Federated: existingArn
            })
          })
        ])
      }
    })
  })
})
