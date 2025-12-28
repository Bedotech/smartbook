"""
Authentication endpoints for OAuth and session management.
"""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.database import get_db
from smartbook.services.oauth_service import OAuthService
from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository
from smartbook.repositories.tenant import TenantRepository
from smartbook.config import settings


router = APIRouter()


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


class LoginResponse(BaseModel):
    """Response for successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    user: dict


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth login flow.

    Redirects the user to Google's OAuth consent screen.

    Returns:
        Redirect response to Google OAuth
    """
    # Build Google OAuth URL
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",  # Get refresh token
        "prompt": "consent",  # Force consent screen to get refresh token
    }

    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    Exchanges authorization code for tokens, creates/updates user,
    and redirects to frontend with JWT tokens.

    Args:
        code: Authorization code from Google
        db: Database session

    Returns:
        Redirect to frontend with tokens in URL hash
    """
    oauth_service = OAuthService(db)

    try:
        redirect_uri = f"{settings.backend_url}/api/auth/google/callback"

        user, access_token, refresh_token, property_ids = await oauth_service.handle_google_callback(
            code=code,
            redirect_uri=redirect_uri,
        )

        # Redirect to frontend with tokens in URL hash
        # Frontend will extract and store in localStorage
        redirect_url = (
            f"{settings.frontend_url}/auth/callback"
            f"#access_token={access_token}"
            f"&refresh_token={refresh_token}"
            f"&token_type=bearer"
        )

        # Commit the transaction
        await db.commit()

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        # Rollback on error
        await db.rollback()

        # Redirect to frontend error page
        error_message = str(e).replace(" ", "+")  # URL-safe encoding
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/error?message={error_message}"
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access token and user info

    Raises:
        HTTPException 401: If refresh token is invalid
    """
    oauth_service = OAuthService(db)

    try:
        new_access_token, user, property_ids = await oauth_service.refresh_access_token(
            request.refresh_token
        )

        return LoginResponse(
            access_token=new_access_token,
            refresh_token=request.refresh_token,  # Keep same refresh token
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "picture_url": user.oauth_picture_url,
                "property_ids": [str(pid) for pid in property_ids],
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me")
async def get_current_user_info(
    # We'll add authentication dependency later
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user information and property assignments.

    Note: This endpoint will be updated with proper authentication
    dependency in the next phase.

    Returns:
        User info with assigned properties
    """
    # TODO: Add get_current_user dependency
    # For now, return a placeholder response
    return {
        "message": "Authentication required - to be implemented with JWT dependency"
    }


@router.post("/logout")
async def logout():
    """
    Logout current user.

    Note: With JWT, logout is primarily client-side (delete tokens).
    Could implement token blacklist for added security in the future.

    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}


@router.post("/test-login", response_model=LoginResponse)
async def test_login(
    db: AsyncSession = Depends(get_db),
):
    """
    **DEVELOPMENT ONLY** - Create/get test admin user and return tokens.

    This endpoint bypasses OAuth and creates a test admin user for
    automated testing with Playwright. Only available when TEST_MODE=true.

    Returns:
        LoginResponse with access token, refresh token, and user info

    Raises:
        HTTPException 404: If test mode is not enabled
    """
    if not settings.test_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )

    oauth_service = OAuthService(db)

    # Create or get test user
    user = await oauth_service._get_or_create_user(
        email="test@smartbook.app",
        name="Test Admin User",
        picture_url=None,
        oauth_provider_id="test-admin-001",
    )

    # Get user's property assignments
    property_ids = await oauth_service.assignment_repo.get_property_ids_for_user(user.id)

    # Generate JWT tokens
    from smartbook.services.jwt_service import JWTService
    access_token = JWTService.create_access_token(user, property_ids)
    refresh_token = JWTService.create_refresh_token(user)

    # Update last login
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    await oauth_service.user_repo.update(user)

    # Commit the transaction
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "picture_url": user.oauth_picture_url,
            "property_ids": [str(pid) for pid in property_ids],
        }
    )
