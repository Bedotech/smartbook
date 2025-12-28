import apiClient from './client'
import type {
  Booking,
  BookingCreateData,
  BookingUpdateData,
  BookingFilters,
  BookingProgress,
  Guest,
  GuestUpdate,
  TaxCalculationResult,
  TaxReport,
  TaxRule,
  TaxRuleCreate,
  DashboardStats,
} from '@smartbook/types'

export const adminApi = {
  // Booking endpoints
  getBookings: (params?: BookingFilters): Promise<Booking[]> =>
    apiClient.get('/api/admin/bookings', { params }),

  createBooking: (data: BookingCreateData): Promise<Booking> =>
    apiClient.post('/api/admin/bookings', data),

  getBooking: (id: string): Promise<Booking> =>
    apiClient.get(`/api/admin/bookings/${id}`),

  updateBooking: (id: string, data: BookingUpdateData): Promise<Booking> =>
    apiClient.put(`/api/admin/bookings/${id}`, data),

  deleteBooking: (id: string): Promise<void> =>
    apiClient.delete(`/api/admin/bookings/${id}`),

  getBookingProgress: (id: string): Promise<BookingProgress> =>
    apiClient.get(`/api/admin/bookings/${id}/progress`),

  // Guest endpoints
  getGuests: (bookingId: string): Promise<Guest[]> =>
    apiClient.get(`/api/admin/bookings/${bookingId}/guests`),

  updateGuest: (id: string, data: GuestUpdate): Promise<Guest> =>
    apiClient.put(`/api/admin/guests/${id}`, data),

  deleteGuest: (id: string): Promise<void> =>
    apiClient.delete(`/api/admin/guests/${id}`),

  // ROS1000 endpoints
  submitROS1000: (bookingId: string) =>
    apiClient.post(`/api/admin/bookings/${bookingId}/submit-ros1000`),

  cancelROS1000: (bookingId: string) =>
    apiClient.post(`/api/admin/bookings/${bookingId}/cancel-ros1000`),

  // Tax endpoints
  calculateTax: (bookingId: string): Promise<TaxCalculationResult> =>
    apiClient.post(`/api/admin/bookings/${bookingId}/calculate-tax`),

  getMonthlyReport: (year: number, month: number): Promise<TaxReport> =>
    apiClient.get('/api/admin/tax/reports/monthly', { params: { year, month } }),

  getQuarterlyReport: (year: number, quarter: number): Promise<TaxReport> =>
    apiClient.get('/api/admin/tax/reports/quarterly', { params: { year, quarter } }),

  // Tax rules endpoints
  getTaxRules: (): Promise<TaxRule[]> =>
    apiClient.get('/api/admin/tax/rules'),

  createTaxRule: (data: TaxRuleCreate): Promise<TaxRule> =>
    apiClient.post('/api/admin/tax/rules', data),

  updateTaxRule: (id: string, data: Partial<TaxRuleCreate>): Promise<TaxRule> =>
    apiClient.put(`/api/admin/tax/rules/${id}`, data),

  deleteTaxRule: (id: string): Promise<void> =>
    apiClient.delete(`/api/admin/tax/rules/${id}`),

  // Dashboard endpoints
  getDashboardStats: (): Promise<DashboardStats> =>
    apiClient.get('/api/admin/dashboard/stats'),
}
