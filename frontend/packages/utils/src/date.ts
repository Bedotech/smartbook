import { format, parseISO, differenceInYears } from 'date-fns'

export function formatDate(date: string | Date, formatStr = 'PP'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return format(dateObj, formatStr)
}

export function calculateAge(birthDate: string, referenceDate?: string): number {
  const birth = parseISO(birthDate)
  const reference = referenceDate ? parseISO(referenceDate) : new Date()
  return differenceInYears(reference, birth)
}

export function formatDateTime(date: string | Date): string {
  return formatDate(date, 'PPpp')
}

export function toISODate(date: Date): string {
  return format(date, 'yyyy-MM-dd')
}
