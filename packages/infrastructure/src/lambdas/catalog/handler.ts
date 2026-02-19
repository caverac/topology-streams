import type { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda'

import type { KnownStreamInfo } from '../../shared/types'

const CATALOG: KnownStreamInfo[] = [
  {
    name: 'GD-1',
    key: 'gd-1',
    lMin: 135.0,
    lMax: 225.0,
    bMin: 30.0,
    bMax: 75.0,
    expectedMembers: 1689
  },
  {
    name: 'Palomar 5',
    key: 'palomar-5',
    lMin: 0.0,
    lMax: 10.0,
    bMin: 40.0,
    bMax: 50.0,
    expectedMembers: 500
  },
  {
    name: 'Jhelum',
    key: 'jhelum',
    lMin: 335.0,
    lMax: 360.0,
    bMin: -55.0,
    bMax: -35.0,
    expectedMembers: 300
  },
  {
    name: 'Orphan-Chenab',
    key: 'orphan-chenab',
    lMin: 160.0,
    lMax: 260.0,
    bMin: 30.0,
    bMax: 70.0,
    expectedMembers: 800
  },
  {
    name: 'ATLAS-Aliqa Uma',
    key: 'atlas-aliqa-uma',
    lMin: 225.0,
    lMax: 270.0,
    bMin: 25.0,
    bMax: 55.0,
    expectedMembers: 200
  }
]

export async function handler(_event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  return {
    statusCode: 200,
    body: JSON.stringify({ streams: CATALOG })
  }
}
