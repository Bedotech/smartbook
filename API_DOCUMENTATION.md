# Smartbook API Documentation

**Version**: 0.1.0
**Base URL**: `https://api.smartbook.app` (production) or `http://localhost:8000` (development)
**Interactive Docs**: `/api/docs` (Swagger UI) or `/api/redoc` (ReDoc)

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Health Check Endpoints](#health-check-endpoints)
4. [Guest Portal API](#guest-portal-api)
5. [Admin Dashboard API](#admin-dashboard-api)
6. [Error Handling](#error-handling)
7. [Rate Limits](#rate-limits)
8. [Examples](#examples)

---

## Overview

Smartbook provides two main API surfaces:

1. **Guest Portal API** (`/api/guest/*`) - Magic link authenticated endpoints for guests to enter their information
2. **Admin Dashboard API** (`/api/admin/*`) - JWT authenticated endpoints for property managers

All endpoints return JSON responses and follow REST conventions.

---

## Authentication

### Magic Link Authentication (Guest Portal)

Guests receive a unique magic link token via email:
```
https://app.smartbook.app/checkin/{token}
```

This token is used in all guest portal API calls:
```
GET /api/guest/booking/{token}
```

**Token Properties**:
- 256-bit cryptographically secure
- URL-safe (uses `token_urlsafe`)
- Expires on booking check-out date
- Single-use recommended (but not enforced)

### JWT Authentication (Admin Dashboard)

**⚠️ NOT YET IMPLEMENTED** - Placeholder exists at `src/smartbook/api/dependencies.py`

Future implementation will use:
```
Authorization: Bearer <jwt_token>
```

---

## Health Check Endpoints

### GET /api/

Root endpoint with API metadata.

**Response**:
```json
{
  "name": "Smartbook",
  "version": "0.1.0",
  "description": "Multi-tenant group check-in and compliance for Italian hospitality",
  "docs": "/api/docs",
  "health": "/api/health"
}
```

### GET /api/health

Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy",
  "service": "smartbook-api",
  "version": "0.1.0"
}
```

---

## Guest Portal API

All guest portal endpoints are prefixed with `/api/guest` and require a magic link token.

### GET /api/guest/booking/{token}

Get booking details by magic link token.

**Parameters**:
- `token` (path) - Magic link token

**Response** (`200 OK`):
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "booking_type": "group",
  "check_in_date": "2024-01-15",
  "check_out_date": "2024-01-18",
  "expected_guests": 50,
  "status": "pending",
  "magic_link_token": "abc123...",
  "notes": "School trip from Milano",
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-10T10:00:00Z"
}
```

**Errors**:
- `404` - Invalid or expired magic link

---

### GET /api/guest/booking/{token}/progress

Get booking progress (e.g., "12/50 guests entered").

**Parameters**:
- `token` (path) - Magic link token

**Response** (`200 OK`):
```json
{
  "total_expected": 50,
  "total_entered": 12,
  "percent_complete": 24.0,
  "has_leader": true,
  "is_complete": false
}
```

---

### POST /api/guest/booking/{token}/guests/leader

Create group leader with full TULPS document details.

**Parameters**:
- `token` (path) - Magic link token

**Request Body**:
```json
{
  "first_name": "Marco",
  "last_name": "Rossi",
  "date_of_birth": "1985-03-15",
  "sex": "M",
  "citizenship_country_code": "100",
  "birth_municipality_code": "F205",
  "residence_municipality_code": "F205",
  "document_type": "passport",
  "document_number": "YA1234567",
  "document_issue_date": "2019-03-15",
  "document_issuing_authority": "Questura di Milano"
}
```

**Response** (`200 OK`):
```json
{
  "id": "uuid",
  "booking_id": "uuid",
  "role": "leader",
  "first_name": "Marco",
  "last_name": "Rossi",
  "date_of_birth": "1985-03-15",
  "sex": "M",
  "citizenship_country_code": "100",
  "document_number": "YA1234567",
  "created_at": "2024-01-15T14:30:00Z"
}
```

**Required Fields** (TULPS Article 109 compliance):
- Personal: `first_name`, `last_name`, `date_of_birth`, `sex`
- Location: `citizenship_country_code`, `birth_municipality_code`, `residence_municipality_code`
- Document: `document_type`, `document_number`, `document_issue_date`, `document_issuing_authority`

**Errors**:
- `400` - Validation error (missing required fields)
- `400` - Leader already exists for this booking

---

### POST /api/guest/booking/{token}/guests/member

Create group member with TULPS minimums (document details optional).

**Request Body**:
```json
{
  "first_name": "Maria",
  "last_name": "Bianchi",
  "date_of_birth": "2010-01-01",
  "sex": "F",
  "citizenship_country_code": "100",
  "residence_municipality_code": "F205",
  "document_type": "id_card",
  "document_number": "CA9876543"
}
```

**Required Fields** (TULPS minimums):
- `first_name`, `last_name`, `date_of_birth`, `sex`
- `citizenship_country_code`, `residence_municipality_code`

**Optional Fields**:
- `birth_municipality_code`
- `document_type`, `document_number`, `document_issue_date`, `document_issuing_authority`

---

### GET /api/guest/booking/{token}/guests

Get all guests for a booking.

**Response** (`200 OK`):
```json
[
  {
    "id": "uuid",
    "role": "leader",
    "first_name": "Marco",
    "last_name": "Rossi",
    ...
  },
  {
    "id": "uuid",
    "role": "member",
    "first_name": "Maria",
    "last_name": "Bianchi",
    ...
  }
]
```

---

### POST /api/guest/booking/{token}/complete

Mark booking as complete (all guests entered).

**Validation**:
- All expected guests must be entered
- At least one leader must exist
- All leaders must have complete document details
- All members must have TULPS minimums

**Response** (`200 OK`):
```json
{
  "id": "uuid",
  "status": "complete",
  ...
}
```

**Errors**:
- `400` - Validation failed (e.g., "Missing 3 guests", "No leader found")

---

### GET /api/guest/municipalities/search

Search Italian municipalities (ISTAT autocomplete).

**Query Parameters**:
- `query` (string, required) - Search query (e.g., "Milan")
- `limit` (integer, optional) - Maximum results (default: 10, max: 100)

**Response** (`200 OK`):
```json
[
  {
    "istat_code": "F205",
    "name": "Milano",
    "province_code": "MI",
    "province_name": "Milano"
  }
]
```

---

### GET /api/guest/countries/search

Search countries (ISTAT codes).

**Query Parameters**:
- `query` (string, required) - Search query
- `limit` (integer, optional) - Maximum results

**Response** (`200 OK`):
```json
[
  {
    "istat_code": "100",
    "name": "Italia",
    "iso_code": "IT"
  }
]
```

---

## Admin Dashboard API

All admin endpoints are prefixed with `/api/admin` and require JWT authentication.

### Booking Management

#### GET /api/admin/bookings

List all bookings with optional filtering.

**Query Parameters**:
- `status` (string, optional) - Filter by status: `pending`, `complete`, `synced`, `error`
- `check_in_from` (date, optional) - Filter bookings from this check-in date
- `check_in_to` (date, optional) - Filter bookings until this check-in date
- `limit` (integer, optional) - Page size (default: 50, max: 100)
- `offset` (integer, optional) - Pagination offset (default: 0)

**Response** (`200 OK`):
```json
[
  {
    "id": "uuid",
    "booking_type": "group",
    "check_in_date": "2024-01-15",
    "expected_guests": 50,
    "status": "complete",
    ...
  }
]
```

---

#### POST /api/admin/bookings

Create a new booking.

**Request Body**:
```json
{
  "booking_type": "group",
  "check_in_date": "2024-01-15",
  "check_out_date": "2024-01-18",
  "expected_guests": 50,
  "notes": "School trip"
}
```

**Response** (`201 Created`):
```json
{
  "id": "uuid",
  "magic_link_token": "abc123...",
  "status": "pending",
  ...
}
```

---

#### PUT /api/admin/bookings/{booking_id}

Update booking details.

---

#### DELETE /api/admin/bookings/{booking_id}

Delete a booking (only if not submitted to ROS1000).

---

### ROS1000 Compliance

#### POST /api/admin/bookings/{booking_id}/submit-ros1000

Submit booking to ROS1000/Alloggiati Web system.

**Prerequisites**:
- Booking must be in `complete` status
- All guests must have valid data
- Facility must have ROS1000 credentials configured

**Response** (`200 OK`):
```json
{
  "success": true,
  "receipt_number": "2024/BG/12345",
  "error_message": null,
  "warnings": [],
  "partial_success": false
}
```

**Errors**:
- `400` - Validation failed (returns list of errors)
- `500` - SOAP submission failed

---

#### POST /api/admin/bookings/{booking_id}/cancel-ros1000

Cancel/correct a previous ROS1000 submission.

---

#### GET /api/admin/compliance/records

List compliance records (5-year retention).

**Query Parameters**:
- `booking_id` (uuid, optional) - Filter by booking
- `status` (string, optional) - Filter by status
- `limit` (integer, optional)

---

### Tax Calculation & Reporting

#### POST /api/admin/bookings/{booking_id}/calculate-tax

Calculate city tax (Imposta di Soggiorno) for a booking.

**Response** (`200 OK`):
```json
{
  "booking_id": "uuid",
  "total_tax": "125.00",
  "total_nights": 3,
  "taxable_nights": 3,
  "total_guests": 50,
  "taxable_guests": 48,
  "base_rate_per_night": "2.50",
  "exemptions": {
    "age_exempt": 2,
    "bus_driver_exempt": 0,
    "tour_guide_exempt": 0,
    "total_exempt": 2
  },
  "breakdown_by_guest": [...]
}
```

---

#### GET /api/admin/tax/reports/monthly

Generate monthly tax report.

**Query Parameters**:
- `year` (integer, required) - Year (e.g., 2024)
- `month` (integer, required) - Month (1-12)

**Response** (`200 OK`):
```json
{
  "period": "January 2024",
  "total_bookings": 15,
  "total_guests": 450,
  "total_taxable_guests": 420,
  "total_nights": 45,
  "total_tax": "3150.00",
  "average_tax_per_booking": "210.00",
  "exemption_summary": {
    "age_exempt": 25,
    "bus_driver_exempt": 3,
    "tour_guide_exempt": 2
  },
  "booking_details": [...]
}
```

---

#### GET /api/admin/tax/reports/quarterly

Generate quarterly tax report.

**Query Parameters**:
- `year` (integer, required)
- `quarter` (integer, required) - Quarter (1-4)

---

### Tax Rule Configuration

#### GET /api/admin/tax/rules

List all tax rules for the tenant.

---

#### POST /api/admin/tax/rules

Create a new tax rule.

**Request Body**:
```json
{
  "base_rate_per_night": "2.50",
  "max_taxable_nights": 5,
  "valid_from": "2024-01-01",
  "valid_until": null,
  "exemption_rules": {
    "age_under": 14,
    "bus_driver_ratio": 25,
    "tour_guide_exempt": true
  }
}
```

---

### Dashboard Analytics

#### GET /api/admin/dashboard/stats

Get dashboard statistics.

**Response** (`200 OK`):
```json
{
  "total_bookings": 150,
  "pending_bookings": 10,
  "complete_bookings": 100,
  "synced_bookings": 35,
  "error_bookings": 5,
  "completion_rate": 90.0
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**HTTP Status Codes**:
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid authentication)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

**Validation Errors** (`422`):
```json
{
  "detail": [
    {
      "loc": ["body", "first_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limits

**⚠️ NOT YET IMPLEMENTED**

Planned rate limits:
- Guest Portal: 100 requests/minute per IP
- Admin Dashboard: 1000 requests/minute per user
- ROS1000 Submissions: 10 submissions/minute per tenant

---

## Examples

### Complete Guest Check-in Flow

```bash
# 1. Guest receives magic link via email
TOKEN="abc123def456..."

# 2. Guest accesses booking
curl -X GET "https://api.smartbook.app/api/guest/booking/${TOKEN}"

# 3. Guest checks progress
curl -X GET "https://api.smartbook.app/api/guest/booking/${TOKEN}/progress"

# 4. Leader enters their information
curl -X POST "https://api.smartbook.app/api/guest/booking/${TOKEN}/guests/leader" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Marco",
    "last_name": "Rossi",
    "date_of_birth": "1985-03-15",
    "sex": "M",
    "citizenship_country_code": "100",
    "birth_municipality_code": "F205",
    "residence_municipality_code": "F205",
    "document_type": "passport",
    "document_number": "YA1234567",
    "document_issue_date": "2019-03-15",
    "document_issuing_authority": "Questura di Milano"
  }'

# 5. Add group members (repeat for each)
curl -X POST "https://api.smartbook.app/api/guest/booking/${TOKEN}/guests/member" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Maria",
    "last_name": "Bianchi",
    "date_of_birth": "2010-01-01",
    "sex": "F",
    "citizenship_country_code": "100",
    "residence_municipality_code": "F205"
  }'

# 6. Mark booking complete
curl -X POST "https://api.smartbook.app/api/guest/booking/${TOKEN}/complete"
```

### Admin Workflow

```bash
# 1. Create booking (generates magic link)
curl -X POST "https://api.smartbook.app/api/admin/bookings" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_type": "group",
    "check_in_date": "2024-01-15",
    "check_out_date": "2024-01-18",
    "expected_guests": 50
  }'

# 2. Submit to ROS1000
BOOKING_ID="uuid..."
curl -X POST "https://api.smartbook.app/api/admin/bookings/${BOOKING_ID}/submit-ros1000" \
  -H "Authorization: Bearer <jwt_token>"

# 3. Calculate tax
curl -X POST "https://api.smartbook.app/api/admin/bookings/${BOOKING_ID}/calculate-tax" \
  -H "Authorization: Bearer <jwt_token>"

# 4. Generate monthly tax report
curl -X GET "https://api.smartbook.app/api/admin/tax/reports/monthly?year=2024&month=1" \
  -H "Authorization: Bearer <jwt_token>"
```

---

## Support

For API support:
- **Documentation**: `/api/docs` (Swagger UI)
- **OpenAPI Schema**: `/openapi.json`
- **Issues**: https://github.com/bedotech/smartbook/issues
