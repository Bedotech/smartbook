# Smartbook Implementation Plan (7 Steps)

## Project Overview
Multi-tenant web application for automated group check-in and compliance management for Italian hospitality (TULPS/ROS1000 compliance + City Tax calculation).

**Reference Document:** `basic_info.pdf` - Contains full technical specifications, regulatory requirements, and architecture details.

**Tech Stack:** Python 3.12+, UV package manager, FastAPI, PostgreSQL, pytest + coverage

---

## Step 1: Project Foundation & Core Domain Models

### Objective
Set up the Python project structure with UV, define core domain models, and establish the database schema.

### Tasks
1. Initialize UV project with dependencies:
   - `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic`, `alembic`
   - Dev: `pytest`, `pytest-cov`, `pytest-asyncio`, `httpx`, `factory-boy`

2. Create project structure:
   ```
   src/smartbook/
   ├── __init__.py
   ├── main.py              # FastAPI app entry
   ├── config.py            # Settings/env config
   ├── domain/
   │   ├── models/          # SQLAlchemy models
   │   ├── schemas/         # Pydantic schemas
   │   └── enums.py         # Guest types, document types
   ├── repositories/        # Data access layer
   ├── services/            # Business logic
   ├── api/                 # FastAPI routers
   └── integrations/        # ROS1000, notifications
   tests/
   ├── conftest.py
   ├── unit/
   ├── integration/
   └── fixtures/
   ```

3. Define core SQLAlchemy models (see PDF Section 3.2):
   - `Tenant` (multi-tenant support with row-level isolation)
   - `Booking` (check-in/out dates, type, status, magic_link_token)
   - `Guest` (personal data, document info, role - Capogruppo/Member)
   - `TaxRule` (configurable per tenant - rates, exemptions, caps)
   - `ComplianceRecord` (ROS1000 receipts, police confirmations)

4. Implement ISTAT reference tables:
   - `Municipality` (Codice Catastale lookup, e.g., H810 = Schilpario)
   - `Country` (ISTAT country codes, e.g., 100000100 = Italy)
   - `DocumentType` (Passport, ID Card, etc.)

### Tests
- Unit tests for all Pydantic schemas validation
- Model creation tests with SQLAlchemy
- Coverage target: 90%+

---

## Step 2: Multi-Tenant Repository Layer & Database

### Objective
Implement row-level tenancy, database migrations, and the repository pattern for data access.

### Tasks
1. Configure Alembic for migrations

2. Implement `TenantContext` middleware:
   - Extract `tenant_id` from JWT/session
   - Auto-inject `WHERE tenant_id = ?` in all queries (PDF Section 3.2.1)

3. Create async repositories:
   - `TenantRepository` - CRUD for tenants
   - `BookingRepository` - Create bookings, generate magic links
   - `GuestRepository` - Add/update guests, validate completeness
   - `TaxRuleRepository` - Manage tax configurations
   - `ComplianceRepository` - Store ROS1000 receipts

4. Implement magic link generation:
   - Cryptographically secure tokens (32+ bytes)
   - Expiration on checkout date (PDF Section 4.1)

### Tests
- Repository CRUD operations
- Tenant isolation verification (Admin A cannot see Admin B's data)
- Magic link token generation and expiration
- Coverage target: 90%+

---

## Step 3: Guest Data Collection & Validation Service

### Objective
Implement the business logic for guest data collection following TULPS requirements.

### Tasks
1. Create `GuestService` with validation:
   - **Group Leader (Capogruppo)**: Full document details required
     - Document Type, Number, Issuing Authority
     - Place/Date of Issue
     - Full residential address
   - **Group Members**: TULPS minimums only (PDF Section 2.1.2)
     - Name, Surname, Sex, Date of Birth, Place of Birth/Residence

2. Implement municipality autocomplete:
   - Search by name prefix (e.g., "Schil" → "Schilpario (BG)")
   - Return ISTAT Codice Catastale for backend

3. Create `BookingService`:
   - Booking creation workflow
   - Progress tracking (e.g., "12/50 Guests Entered")
   - Status management (pending → in_progress → complete → synced)

4. Implement "Same as Leader" feature:
   - Copy residence from leader to members (PDF Section 4.2)
   - Reduce data entry by ~50% for local groups

### Tests
- Guest validation (required fields per role)
- Municipality lookup accuracy
- Booking status transitions
- Edge cases: partial data, invalid dates
- Coverage target: 90%+

---

## Step 4: City Tax Calculation Engine

### Objective
Build the configurable tax rule engine for Imposta di Soggiorno (PDF Section 7).

### Tasks
1. Create `TaxCalculationService`:
   - **Base Rate**: Per night fee (e.g., €1.00)
   - **Max Nights Cap**: Only first N nights taxed (e.g., 10 nights)
   - **Age Exemption**: Dynamic calculation
     ```python
     if (check_in_date - birth_date).years < age_threshold:
         tax = 0  # Minor exempt
     ```
   - **Role Exemptions**: Bus drivers (1 per 25 guests), tour guides

2. Implement exemption ratio logic:
   ```python
   exempt_count = total_guests // 25  # 1 driver per 25
   taxable_guests = total_guests - exempt_count
   ```

3. Create tax configuration CRUD:
   - Store rules as JSON per tenant
   - Support historical rules for past calculations

4. Build reporting module:
   - Aggregate taxable vs exempt nights
   - Breakdown by exemption type
   - Generate PDF summary for municipality

### Tests
- Tax calculation with various scenarios:
  - Group of 50 with 10 minors, 2 drivers
  - Stay exceeding max nights cap
  - Mixed nationalities
- Rule configuration updates
- Report generation accuracy
- Coverage target: 95%+ (critical financial logic)

---

## Step 5: ROS1000 Integration & XML Generation

### Objective
Implement the SOAP client for ROS1000/Questura data transmission (PDF Section 6).

### Tasks
1. Create XML builder for ROS1000 schema:
   - Map user input to ROS1000 codes:
     | User Selection | ROS1000 Code |
     |----------------|--------------|
     | Group Leader   | 19           |
     | Group Member   | 20           |
     | Family Head    | 17           |
   - Convert municipality names to Codice Catastale
   - Convert countries to ISTAT codes

2. Implement `ROS1000Service`:
   - WSDL consumption from flussituristici.servizirl.it
   - SOAP envelope construction with auth header
   - WS Key injection for Questura bridge

3. Build pre-validation layer:
   - Reject incomplete data before transmission
   - Clear error messages (e.g., "Guest 3 is missing Date of Birth")

4. Handle response parsing (PDF Section 6.3):
   - **Total Success**: Save Protocol ID + Police Receipt
   - **Partial Success**: Flag "Police Error" for admin
   - **Failure**: Log and alert for malformed XML

5. Store compliance records:
   - Digital receipts for 5-year retention requirement
   - Audit trail for all transmissions

### Tests
- XML generation matches ROS1000 schema
- SOAP client with mock server
- Error handling for all response types
- Pre-validation catches all edge cases
- Coverage target: 90%+

---

## Step 6: REST API & Admin Dashboard Backend

### Objective
Build the FastAPI endpoints for both guest portal and admin dashboard.

### Tasks
1. **Guest Portal API** (public, magic-link authenticated):
   - `GET /api/checkin/{token}` - Get booking details
   - `POST /api/checkin/{token}/leader` - Submit leader data
   - `POST /api/checkin/{token}/members` - Submit member matrix
   - `GET /api/municipalities?q=` - Autocomplete search

2. **Admin Dashboard API** (JWT authenticated):
   - `POST /api/auth/login` - Admin authentication
   - `GET /api/bookings` - List with status indicators
   - `POST /api/bookings` - Create new booking
   - `GET /api/bookings/{id}` - Booking details with guest progress
   - `POST /api/bookings/{id}/sync-ros1000` - Trigger SOAP transmission
   - `GET /api/bookings/{id}/receipt` - Download police receipt
   - `GET /api/bookings/{id}/tax-report` - Generate tax PDF

3. **Tenant Configuration API**:
   - `GET/PUT /api/settings/ros1000` - Credentials, WS Key, Facility Code
   - `GET/PUT /api/settings/tax-rules` - Rate, exemptions, caps

4. Implement notification triggers:
   - On check-in complete: Email/SMS to admin
   - SLA warning: Reminder if not submitted by 10:00 AM on arrival day

### Tests
- All endpoint responses and status codes
- Authentication and authorization
- Tenant isolation in API layer
- Rate limiting and input validation
- Coverage target: 90%+

---

## Step 7: End-to-End Integration & Quality Assurance

### Objective
Complete integration testing, documentation, and production readiness.

### Tasks
1. **End-to-End Test Scenarios**:
   - Full group check-in flow (50 guests)
   - Magic link lifecycle (create → use → expire)
   - ROS1000 transmission with mock server
   - Tax calculation and report generation
   - Multi-tenant isolation verification

2. **Performance Testing**:
   - Concurrent guest data entry
   - Large group handling (100+ members)
   - Database query optimization

3. **Security Audit**:
   - Input sanitization (XSS, SQL injection)
   - PII encryption at rest
   - TLS 1.3 enforcement
   - Token entropy verification

4. **Documentation**:
   - API documentation (OpenAPI/Swagger)
   - Deployment guide
   - Admin user manual

5. **CI/CD Setup**:
   - GitHub Actions workflow
   - Test + coverage on PR
   - Automated deployment

6. **Final Coverage Report**:
   - Minimum 85% overall coverage
   - 95%+ for tax calculation and compliance modules
   - All critical paths tested

### Deliverables
- Fully tested Python backend
- Coverage report with pytest-cov
- OpenAPI spec
- Docker configuration for deployment

---

## Quick Reference

### Key Regulatory Codes (from PDF)
| Item | Code |
|------|------|
| Schilpario Municipality | H810 |
| Italy (ISTAT) | 100000100 |
| Germany (ISTAT) | 100000122 |
| Group Leader (Capogruppo) | 19 |
| Group Member | 20 |

### Commands
```bash
# Install dependencies
uv sync

# Run tests with coverage
uv run pytest --cov=src/smartbook --cov-report=html

# Run development server
uv run uvicorn smartbook.main:app --reload

# Run migrations
uv run alembic upgrade head
```
