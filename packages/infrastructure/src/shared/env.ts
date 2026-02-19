import { z } from 'zod'

export const SubmitJobEnv = z.object({
  TABLE_NAME: z.string().min(1),
  QUEUE_URL: z.string().url()
})

export const JobStatusEnv = z.object({
  TABLE_NAME: z.string().min(1)
})

export const JobResultsEnv = z.object({
  TABLE_NAME: z.string().min(1),
  BUCKET_NAME: z.string().min(1)
})

export const CatalogEnv = z.object({})
