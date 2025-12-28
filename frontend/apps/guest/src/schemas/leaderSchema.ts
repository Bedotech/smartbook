import { z } from 'zod'

export const leaderFormSchema = z.object({
  // Role - default to leader
  role: z.literal('leader').default('leader'),

  // Required: Personal Information
  first_name: z
    .string()
    .min(1, 'First name is required')
    .max(100, 'First name too long')
    .regex(/^[a-zA-ZÀ-ÿ\s'-]+$/, 'Invalid characters in first name'),

  last_name: z
    .string()
    .min(1, 'Last name is required')
    .max(100, 'Last name too long')
    .regex(/^[a-zA-ZÀ-ÿ\s'-]+$/, 'Invalid characters in last name'),

  sex: z.enum(['M', 'F'], {
    errorMap: () => ({ message: 'Please select sex' }),
  }),

  date_of_birth: z
    .string()
    .min(1, 'Date of birth is required')
    .refine(
      (val) => {
        const date = new Date(val)
        const today = new Date()
        const age = today.getFullYear() - date.getFullYear()
        return age >= 0 && age <= 150
      },
      { message: 'Invalid date of birth' }
    ),

  // Required: Document Information
  document_type: z.enum(['passport', 'id_card', 'driving_license', 'other'], {
    errorMap: () => ({ message: 'Please select document type' }),
  }),

  document_number: z
    .string()
    .min(1, 'Document number is required')
    .max(50, 'Document number too long')
    .regex(/^[A-Z0-9]+$/i, 'Only letters and numbers allowed'),

  document_issuing_authority: z
    .string()
    .min(1, 'Issuing authority is required')
    .max(200, 'Issuing authority too long'),

  document_issue_date: z
    .string()
    .min(1, 'Issue date is required')
    .refine(
      (val) => {
        const issueDate = new Date(val)
        const today = new Date()
        return issueDate <= today
      },
      { message: 'Issue date cannot be in the future' }
    ),

  document_issue_place: z
    .string()
    .min(1, 'Issue place is required')
    .max(200, 'Issue place too long'),

  // Optional: Place of Birth
  place_of_birth_municipality_code: z.string().default(''),
  place_of_birth_country_code: z.string().default(''),

  // Optional: Residence
  residence_municipality_code: z.string().default(''),
  residence_country_code: z.string().default(''),
  residence_address: z.string().max(300, 'Address too long').default(''),
  residence_zip_code: z
    .string()
    .max(20, 'ZIP code too long')
    .regex(/^[A-Z0-9\s-]*$/i, 'Invalid ZIP code format')
    .default(''),

  // Optional: Citizenship
  citizenship_country_code: z.string().default(''),
})

export type LeaderFormValues = z.infer<typeof leaderFormSchema>
