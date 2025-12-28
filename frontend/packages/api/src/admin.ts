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
  Property,
  PropertyCreate,
  PropertyUpdate,
  PropertyUser,
  User,
  UserPropertyAssignment,
} from '@smartbook/types'

export const adminApi = {
  // Booking endpoints
  getBookings: (propertyId: string, params?: BookingFilters): Promise<Booking[]> =>
    apiClient.get('/api/admin/bookings', { params: { property_id: propertyId, ...params } }),

  createBooking: (propertyId: string, data: BookingCreateData): Promise<Booking> =>
    apiClient.post('/api/admin/bookings', data, { params: { property_id: propertyId } }),

  getBooking: (propertyId: string, id: string): Promise<Booking> =>
    apiClient.get(`/api/admin/bookings/${id}`, { params: { property_id: propertyId } }),

  updateBooking: (propertyId: string, id: string, data: BookingUpdateData): Promise<Booking> =>
    apiClient.put(`/api/admin/bookings/${id}`, data, { params: { property_id: propertyId } }),

  deleteBooking: (propertyId: string, id: string): Promise<void> =>
    apiClient.delete(`/api/admin/bookings/${id}`, { params: { property_id: propertyId } }),

  getBookingProgress: (propertyId: string, id: string): Promise<BookingProgress> =>
    apiClient.get(`/api/admin/bookings/${id}/progress`, { params: { property_id: propertyId } }),

  // Guest endpoints
  getGuests: (propertyId: string, bookingId: string): Promise<Guest[]> =>
    apiClient.get(`/api/admin/bookings/${bookingId}/guests`, { params: { property_id: propertyId } }),

  updateGuest: (propertyId: string, id: string, data: GuestUpdate): Promise<Guest> =>
    apiClient.put(`/api/admin/guests/${id}`, data, { params: { property_id: propertyId } }),

  deleteGuest: (propertyId: string, id: string): Promise<void> =>
    apiClient.delete(`/api/admin/guests/${id}`, { params: { property_id: propertyId } }),

  // ROS1000 endpoints
  submitROS1000: (propertyId: string, bookingId: string) =>
    apiClient.post(`/api/admin/bookings/${bookingId}/submit-ros1000`, {}, { params: { property_id: propertyId } }),

  cancelROS1000: (propertyId: string, bookingId: string) =>
    apiClient.post(`/api/admin/bookings/${bookingId}/cancel-ros1000`, {}, { params: { property_id: propertyId } }),

  // Tax endpoints
  calculateTax: (propertyId: string, bookingId: string): Promise<TaxCalculationResult> =>
    apiClient.post(`/api/admin/bookings/${bookingId}/calculate-tax`, {}, { params: { property_id: propertyId } }),

  getMonthlyReport: (propertyId: string, year: number, month: number): Promise<TaxReport> =>
    apiClient.get('/api/admin/tax/reports/monthly', { params: { property_id: propertyId, year, month } }),

  getQuarterlyReport: (propertyId: string, year: number, quarter: number): Promise<TaxReport> =>
    apiClient.get('/api/admin/tax/reports/quarterly', { params: { property_id: propertyId, year, quarter } }),

  // Tax rules endpoints
  getTaxRules: (propertyId: string): Promise<TaxRule[]> =>
    apiClient.get('/api/admin/tax/rules', { params: { property_id: propertyId } }),

  createTaxRule: (propertyId: string, data: TaxRuleCreate): Promise<TaxRule> =>
    apiClient.post('/api/admin/tax/rules', data, { params: { property_id: propertyId } }),

  updateTaxRule: (propertyId: string, id: string, data: Partial<TaxRuleCreate>): Promise<TaxRule> =>
    apiClient.put(`/api/admin/tax/rules/${id}`, data, { params: { property_id: propertyId } }),

  deleteTaxRule: (propertyId: string, id: string): Promise<void> =>
    apiClient.delete(`/api/admin/tax/rules/${id}`, { params: { property_id: propertyId } }),

  // Dashboard endpoints
  getDashboardStats: (propertyId: string): Promise<DashboardStats> =>
    apiClient.get('/api/admin/dashboard/stats', { params: { property_id: propertyId } }),

  // Property management endpoints (Admin only)
  getProperties: (params?: { search?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<Property[]> =>
    apiClient.get('/api/admin/properties', { params }),

  getProperty: (id: string): Promise<Property> =>
    apiClient.get(`/api/admin/properties/${id}`),

  createProperty: (data: PropertyCreate): Promise<Property> =>
    apiClient.post('/api/admin/properties', data),

  updateProperty: (id: string, data: PropertyUpdate): Promise<Property> =>
    apiClient.put(`/api/admin/properties/${id}`, data),

  activateProperty: (id: string): Promise<{ message: string }> =>
    apiClient.patch(`/api/admin/properties/${id}/activate`),

  deactivateProperty: (id: string): Promise<{ message: string }> =>
    apiClient.patch(`/api/admin/properties/${id}/deactivate`),

  getPropertyUsers: (propertyId: string): Promise<PropertyUser[]> =>
    apiClient.get(`/api/admin/properties/${propertyId}/users`),

  assignUserToProperty: (propertyId: string, userId: string): Promise<{ message: string }> =>
    apiClient.post(`/api/admin/properties/${propertyId}/users/${userId}`),

  removeUserFromProperty: (propertyId: string, userId: string): Promise<void> =>
    apiClient.delete(`/api/admin/properties/${propertyId}/users/${userId}`),

  // User management endpoints (Admin only)
  getUsers: (params?: { search?: string; role?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<User[]> =>
    apiClient.get('/api/admin/users', { params }),

  getUser: (userId: string): Promise<User> =>
    apiClient.get(`/api/admin/users/${userId}`),

  getUserProperties: (userId: string): Promise<UserPropertyAssignment[]> =>
    apiClient.get(`/api/admin/users/${userId}/properties`),

  assignPropertiesToUser: (userId: string, propertyIds: string[]): Promise<{ message: string }> =>
    apiClient.post(`/api/admin/users/${userId}/properties`, { property_ids: propertyIds }),

  removePropertyFromUser: (userId: string, propertyId: string): Promise<void> =>
    apiClient.delete(`/api/admin/users/${userId}/properties/${propertyId}`),
}
