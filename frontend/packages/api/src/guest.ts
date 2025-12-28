import apiClient from './client'
import type {
  Booking,
  BookingProgress,
  Guest,
  LeaderFormData,
  MemberFormData,
  Municipality,
  Country,
} from '@smartbook/types'

export const guestApi = {
  // Booking endpoints
  getBooking: (token: string): Promise<Booking> =>
    apiClient.get(`/api/guest/booking/${token}`),

  getProgress: (token: string): Promise<BookingProgress> =>
    apiClient.get(`/api/guest/booking/${token}/progress`),

  getGuests: (token: string): Promise<Guest[]> =>
    apiClient.get(`/api/guest/booking/${token}/guests`),

  completeBooking: (token: string): Promise<Booking> =>
    apiClient.post(`/api/guest/booking/${token}/complete`),

  // Guest endpoints
  addLeader: (token: string, data: LeaderFormData): Promise<Guest> =>
    apiClient.post(`/api/guest/booking/${token}/guests/leader`, data),

  addMember: (token: string, data: MemberFormData): Promise<Guest> =>
    apiClient.post(`/api/guest/booking/${token}/guests/member`, data),

  // Autocomplete endpoints
  searchMunicipalities: (query: string, limit = 10): Promise<Municipality[]> =>
    apiClient.get('/api/guest/municipalities/search', { params: { query, limit } }),

  searchCountries: (query: string, limit = 10): Promise<Country[]> =>
    apiClient.get('/api/guest/countries/search', { params: { query, limit } }),
}
