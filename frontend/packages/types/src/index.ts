// Booking types
export type BookingType = 'individual' | 'family' | 'group'
export type BookingStatus = 'pending' | 'in_progress' | 'complete' | 'synced' | 'error'

export interface Booking {
  id: string
  tenant_id: string
  booking_type: BookingType
  check_in_date: string
  check_out_date: string
  expected_guests: number
  status: BookingStatus
  magic_link_token: string
  token_expires_at: string
  notes?: string
  ros1000_receipt_number?: string
  created_at: string
  updated_at: string
}

export interface BookingProgress {
  booking_id: string
  expected_guests: number
  current_guest_count: number
  has_leader: boolean
  completion_percentage: number
  status: BookingStatus
}

export interface BookingCreateData {
  booking_type: BookingType
  check_in_date: string
  check_out_date: string
  expected_guests: number
  notes?: string
}

export interface BookingUpdateData {
  booking_type?: BookingType
  check_in_date?: string
  check_out_date?: string
  expected_guests?: number
  notes?: string
  status?: BookingStatus
}

export interface BookingFilters {
  status?: BookingStatus
  check_in_from?: string
  check_in_to?: string
  limit?: number
  offset?: number
}

// Guest types
export type GuestRole = 'leader' | 'member' | 'bus_driver' | 'tour_guide'
export type Sex = 'M' | 'F'
export type DocumentType = 'passport' | 'id_card' | 'driving_license' | 'other'

export interface Guest {
  id: string
  booking_id: string
  role: GuestRole
  first_name: string
  last_name: string
  sex: Sex
  date_of_birth: string
  place_of_birth_municipality_code: string
  place_of_birth_country_code: string
  residence_municipality_code: string
  residence_country_code: string
  residence_address: string
  residence_zip_code: string
  citizenship_country_code: string
  document_type?: DocumentType
  document_number?: string
  document_issuing_authority?: string
  document_issue_date?: string
  document_issue_place?: string
  is_tax_exempt: boolean
  tax_exemption_reason?: string
}

export interface LeaderFormData {
  first_name: string
  last_name: string
  sex: Sex
  date_of_birth: string
  place_of_birth_municipality_code: string
  place_of_birth_country_code: string
  residence_municipality_code: string
  residence_country_code: string
  residence_address: string
  residence_zip_code: string
  citizenship_country_code: string
  document_type: DocumentType
  document_number: string
  document_issuing_authority: string
  document_issue_date: string
  document_issue_place: string
}

export interface MemberFormData {
  first_name: string
  last_name: string
  sex: Sex
  date_of_birth: string
  place_of_birth_municipality_code: string
  place_of_birth_country_code: string
  residence_municipality_code: string
  residence_country_code: string
  residence_address: string
  residence_zip_code: string
  citizenship_country_code: string
  role?: GuestRole
}

export interface GuestUpdate {
  first_name?: string
  last_name?: string
  sex?: Sex
  date_of_birth?: string
  // ... other optional fields
}

// Municipality/Country types
export interface Municipality {
  istat_code: string
  name: string
  province_code: string
  province_name: string
  region_name: string
}

export interface Country {
  istat_code: string
  name: string
  iso_code: string
}

// Tax types
export interface TaxCalculationResult {
  total_tax: number
  total_taxable_nights: number
  total_exempt_nights: number
  guest_breakdown: Array<{
    guest_id: string
    guest_name: string
    nights: number
    taxable_nights: number
    exempt_nights: number
    tax_amount: number
    exemption_reason?: string
  }>
}

export interface TaxReport {
  period: string
  total_tax: number
  total_bookings: number
  total_guests: number
  total_taxable_nights: number
  total_exempt_nights: number
  exemption_breakdown: Record<string, number>
}

export interface TaxRule {
  id: string
  tenant_id: string
  valid_from: string
  valid_until?: string
  base_rate_per_night: number
  max_taxable_nights: number
  age_exemption_threshold: number
  exemption_rules: Record<string, any>
  structure_classification: string
}

export interface TaxRuleCreate {
  valid_from: string
  valid_until?: string
  base_rate_per_night: number
  max_taxable_nights: number
  age_exemption_threshold: number
  exemption_rules: Record<string, any>
  structure_classification: string
}

// Dashboard types
export interface DashboardStats {
  total_bookings: number
  pending_bookings: number
  complete_bookings: number
  synced_bookings: number
  error_bookings: number
  completion_rate: number
}
