import { z } from 'zod'

export const JobStatusSchema = z.enum(['PENDING', 'RUNNING', 'COMPLETED', 'FAILED'])
export type JobStatus = z.infer<typeof JobStatusSchema>

export const SubmitJobRequestSchema = z.object({
  streamKey: z.string().min(1),
  nNeighbors: z.number().int().min(1).default(32),
  sigmaThreshold: z.number().positive().default(3.0)
})
export type SubmitJobRequest = z.infer<typeof SubmitJobRequestSchema>

export const JobRecordSchema = z.object({
  jobId: z.string().uuid(),
  streamKey: z.string(),
  status: JobStatusSchema,
  nNeighbors: z.number().int(),
  sigmaThreshold: z.number(),
  createdAt: z.string(),
  updatedAt: z.string(),
  error: z.string().optional(),
  ttl: z.number().optional()
})
export type JobRecord = z.infer<typeof JobRecordSchema>

export const KnownStreamInfoSchema = z.object({
  name: z.string(),
  key: z.string(),
  lMin: z.number(),
  lMax: z.number(),
  bMin: z.number(),
  bMax: z.number(),
  expectedMembers: z.number().int()
})
export type KnownStreamInfo = z.infer<typeof KnownStreamInfoSchema>
