"""
FastAPI dependencies for authentication, authorization, and tenant context.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.database import get_db
from smartbook.domain.models.user import User
from smartbook.repositories.user import UserRepository
from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository
from smartbook.services.jwt_service import JWTService


# Security scheme for JWT
security = HTTPBearer()


class TenantContext:
    """
    Tenant context for row-level multi-tenancy.

    Ensures that all database queries are automatically filtered
    by tenant_id to prevent data leakage between tenants.
    """

    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id

    def __repr__(self) -> str:
        return f"<TenantContext tenant_id={self.tenant_id}>"


async def get_current_tenant_id(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> UUID:
    """
    Extract tenant ID from request header.

    In production, this would typically come from:
    1. JWT token claims
    2. Session data
    3. Subdomain mapping
    4. API key lookup

    For now, we use a header for simplicity.
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required",
        )

    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format",
        )


async def get_tenant_context(
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
) -> TenantContext:
    """
    Get tenant context from tenant ID.

    This dependency injects the tenant context into route handlers,
    ensuring all operations are scoped to the correct tenant.
    """
    return TenantContext(tenant_id=tenant_id)


# JWT Authentication Dependencies

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException 401: If token is invalid or expired
        HTTPException 404: If user not found or inactive
    """
    try:
        # Verify JWT token
        payload = JWTService.verify_token(credentials.credentials)

        # Extract user_id from 'sub' claim
        user_id = UUID(payload["sub"])

        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or inactive"
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_property_ids(
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[UUID]:
    """
    Get list of property IDs assigned to current user.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List of property UUIDs assigned to user
    """
    assignment_repo = UserPropertyAssignmentRepository(db)
    return await assignment_repo.get_property_ids_for_user(user.id)


async def require_admin_role(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require user to have admin role.

    Args:
        user: Current authenticated user

    Returns:
        User object (if admin)

    Raises:
        HTTPException 403: If user does not have admin role
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation"
        )
    return user


async def validate_property_access(
    property_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    Validate that user has access to the requested property.

    Used in endpoints that operate on a specific property.

    Args:
        property_id: Property ID from request (query param, path param, or body)
        user: Current authenticated user
        db: Database session

    Returns:
        Property ID (if access is granted)

    Raises:
        HTTPException 403: If user does not have access to property
    """
    assignment_repo = UserPropertyAssignmentRepository(db)
    property_ids = await assignment_repo.get_property_ids_for_user(user.id)

    if property_id not in property_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this property"
        )

    return property_id


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentTenant = Annotated[TenantContext, Depends(get_tenant_context)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin_role)]
UserPropertyIds = Annotated[list[UUID], Depends(get_user_property_ids)]
