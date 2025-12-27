"""
Integration tests for API endpoints.

Tests REST API structure and basic functionality:
- Health check endpoints
- API documentation
- Endpoint structure validation
"""

import pytest
from fastapi.testclient import TestClient

from smartbook.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/api/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


def test_health_check_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "smartbook-api"
    assert "version" in data


# ============================================================================
# API DOCUMENTATION
# ============================================================================


def test_openapi_docs_available(client: TestClient):
    """Test that OpenAPI documentation is available."""
    response = client.get("/api/docs")

    assert response.status_code == 200


def test_openapi_schema_available(client: TestClient):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema


def test_api_paths_structure(client: TestClient):
    """Test that API has expected path structure."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    # Health endpoints
    assert "/api/health" in paths
    assert "/api/" in paths

    # Guest portal endpoints
    assert "/api/guest/booking/{token}" in paths
    assert "/api/guest/booking/{token}/progress" in paths
    assert "/api/guest/booking/{token}/guests/leader" in paths
    assert "/api/guest/booking/{token}/guests/member" in paths
    assert "/api/guest/booking/{token}/guests" in paths
    assert "/api/guest/booking/{token}/complete" in paths
    assert "/api/guest/municipalities/search" in paths
    assert "/api/guest/countries/search" in paths

    # Admin endpoints
    assert "/api/admin/bookings" in paths
    assert "/api/admin/bookings/{booking_id}" in paths
    assert "/api/admin/bookings/{booking_id}/progress" in paths
    assert "/api/admin/bookings/{booking_id}/guests" in paths
    assert "/api/admin/guests/{guest_id}" in paths
    assert "/api/admin/bookings/{booking_id}/submit-ros1000" in paths
    assert "/api/admin/bookings/{booking_id}/cancel-ros1000" in paths
    assert "/api/admin/bookings/{booking_id}/calculate-tax" in paths
    assert "/api/admin/tax/reports/monthly" in paths
    assert "/api/admin/tax/reports/quarterly" in paths
    assert "/api/admin/tax/rules" in paths
    assert "/api/admin/dashboard/stats" in paths


def test_api_schemas_structure(client: TestClient):
    """Test that API has expected schema definitions."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    schemas = schema["components"]["schemas"]

    # Booking schemas
    assert "BookingCreate" in schemas
    assert "BookingResponse" in schemas
    assert "BookingUpdate" in schemas
    assert "BookingProgressResponse" in schemas

    # Guest schemas
    assert "GuestLeaderCreate" in schemas
    assert "GuestMemberCreate" in schemas
    assert "GuestResponse" in schemas
    assert "GuestUpdate" in schemas

    # Tax schemas
    assert "TaxRuleCreate" in schemas
    assert "TaxRuleResponse" in schemas
    assert "TaxRuleUpdate" in schemas

    # Municipality schemas
    assert "MunicipalitySearchResponse" in schemas
    assert "CountrySearchResponse" in schemas

    # Compliance schemas
    assert "ComplianceRecordResponse" in schemas


def test_booking_create_schema_structure(client: TestClient):
    """Test BookingCreate schema has required fields."""
    response = client.get("/openapi.json")

    schema = response.json()
    booking_create = schema["components"]["schemas"]["BookingCreate"]

    # Check required fields
    assert "required" in booking_create
    required_fields = booking_create["required"]
    assert "booking_type" in required_fields
    assert "check_in_date" in required_fields
    assert "check_out_date" in required_fields
    assert "expected_guests" in required_fields


def test_guest_leader_schema_structure(client: TestClient):
    """Test GuestLeaderCreate schema has required fields."""
    response = client.get("/openapi.json")

    schema = response.json()
    guest_leader = schema["components"]["schemas"]["GuestLeaderCreate"]

    # Check required fields (TULPS compliance - leaders need full details)
    assert "required" in guest_leader
    required_fields = guest_leader["required"]
    assert "first_name" in required_fields
    assert "last_name" in required_fields
    assert "date_of_birth" in required_fields
    assert "sex" in required_fields
    assert "document_type" in required_fields
    assert "document_number" in required_fields


def test_guest_member_schema_structure(client: TestClient):
    """Test GuestMemberCreate schema has required fields."""
    response = client.get("/openapi.json")

    schema = response.json()
    guest_member = schema["components"]["schemas"]["GuestMemberCreate"]

    # Check required fields (TULPS minimums - members only need basics)
    assert "required" in guest_member
    required_fields = guest_member["required"]
    assert "first_name" in required_fields
    assert "last_name" in required_fields
    assert "date_of_birth" in required_fields
    assert "sex" in required_fields
    # Document fields should NOT be required for members
    assert "document_type" not in required_fields
    assert "document_number" not in required_fields


# ============================================================================
# ENDPOINT HTTP METHODS
# ============================================================================


def test_guest_portal_http_methods(client: TestClient):
    """Test that guest portal endpoints use correct HTTP methods."""
    response = client.get("/openapi.json")

    schema = response.json()
    paths = schema["paths"]

    # GET methods
    assert "get" in paths["/api/guest/booking/{token}"]
    assert "get" in paths["/api/guest/booking/{token}/progress"]
    assert "get" in paths["/api/guest/booking/{token}/guests"]
    assert "get" in paths["/api/guest/municipalities/search"]
    assert "get" in paths["/api/guest/countries/search"]

    # POST methods
    assert "post" in paths["/api/guest/booking/{token}/guests/leader"]
    assert "post" in paths["/api/guest/booking/{token}/guests/member"]
    assert "post" in paths["/api/guest/booking/{token}/complete"]


def test_admin_http_methods(client: TestClient):
    """Test that admin endpoints use correct HTTP methods."""
    response = client.get("/openapi.json")

    schema = response.json()
    paths = schema["paths"]

    # GET methods
    assert "get" in paths["/api/admin/bookings"]
    assert "get" in paths["/api/admin/bookings/{booking_id}"]
    assert "get" in paths["/api/admin/tax/reports/monthly"]
    assert "get" in paths["/api/admin/dashboard/stats"]

    # POST methods
    assert "post" in paths["/api/admin/bookings"]
    assert "post" in paths["/api/admin/bookings/{booking_id}/submit-ros1000"]
    assert "post" in paths["/api/admin/tax/rules"]

    # PUT methods
    assert "put" in paths["/api/admin/bookings/{booking_id}"]
    assert "put" in paths["/api/admin/guests/{guest_id}"]
    assert "put" in paths["/api/admin/tax/rules/{rule_id}"]

    # DELETE methods
    assert "delete" in paths["/api/admin/bookings/{booking_id}"]
    assert "delete" in paths["/api/admin/guests/{guest_id}"]
    assert "delete" in paths["/api/admin/tax/rules/{rule_id}"]


# ============================================================================
# ERROR HANDLING
# ============================================================================


def test_404_on_invalid_route(client: TestClient):
    """Test 404 response on invalid route."""
    response = client.get("/api/nonexistent/route")

    assert response.status_code == 404


def test_health_endpoint_always_works(client: TestClient):
    """Test health endpoint works without authentication."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
