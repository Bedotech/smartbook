import { z } from 'zod'

export const memberFormSchema = z.object({
  // Required: TULPS Minimums Only
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

  // Optional: All other fields
  place_of_birth_municipality_code: z.string().default(''),
  place_of_birth_country_code: z.string().default(''),
  residence_municipality_code: z.string().default(''),
  residence_country_code: z.string().default(''),
  residence_address: z.string().max(300, 'Address too long').default(''),
  residence_zip_code: z
    .string()
    .max(20, 'ZIP code too long')
    .regex(/^[A-Z0-9\s-]*$/i, 'Invalid ZIP code format')
    .default(''),
  citizenship_country_code: z.string().default(''),
  role: z.enum(['member', 'bus_driver', 'tour_guide']).default('member'),
})

export type MemberFormValues = z.infer<typeof memberFormSchema>
