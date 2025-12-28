"""
User management endpoints (admin only).

These endpoints allow administrators to manage users and their property assignments.
"""

from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from smartbook.api.dependencies import AdminUser, DbSession
from smartbook.repositories.user import UserRepository
from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository
from smartbook.domain.models.user import User


router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    name: str
    role: str
    oauth_provider: str
    oauth_picture_url: str | None
    is_active: bool
    last_login_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class PropertyAssignmentRequest(BaseModel):
    """Request to assign properties to a user."""
    property_ids: list[UUID]


class PropertyAssignmentResponse(BaseModel):
    """Property assignment response."""
    user_id: str
    property_ids: list[str]
    assigned_count: int


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================


@router.get("/users", response_model=Sequence[UserResponse])
async def list_users(
    role: str | None = Query(None, description="Filter by role (admin or staff)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    List all users in the system (admin only).

    Args:
        role: Optional role filter
        is_active: Optional active status filter
        limit: Maximum number of results
        offset: Pagination offset
        admin: Current admin user
        db: Database session

    Returns:
        List of users
    """
    user_repo = UserRepository(db)

    if role:
        users = await user_repo.get_by_role(role)
    elif is_active is not None:
        users = await user_repo.get_active_users() if is_active else []
    else:
        # Get all users - need to implement in repository
        # For now, get active users
        users = await user_repo.get_active_users()

    # Apply pagination
    paginated_users = list(users)[offset : offset + limit]

    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            oauth_provider=user.oauth_provider,
            oauth_picture_url=user.oauth_picture_url,
            is_active=user.is_active,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            created_at=user.created_at.isoformat(),
        )
        for user in paginated_users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        admin: Current admin user
        db: Database session

    Returns:
        User details
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        oauth_provider=user.oauth_provider,
        oauth_picture_url=user.oauth_picture_url,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat(),
    )


@router.get("/users/{user_id}/properties", response_model=PropertyAssignmentResponse)
async def get_user_properties(
    user_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get properties assigned to a user (admin only).

    Args:
        user_id: User ID
        admin: Current admin user
        db: Database session

    Returns:
        User's property assignments
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    assignment_repo = UserPropertyAssignmentRepository(db)
    property_ids = await assignment_repo.get_property_ids_for_user(user_id)

    return PropertyAssignmentResponse(
        user_id=str(user_id),
        property_ids=[str(pid) for pid in property_ids],
        assigned_count=len(property_ids),
    )


@router.post("/users/{user_id}/properties", response_model=PropertyAssignmentResponse)
async def assign_properties_to_user(
    user_id: UUID,
    request: PropertyAssignmentRequest,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Assign properties to a user (admin only).

    This replaces all existing property assignments with the new list.

    Args:
        user_id: User ID
        request: Property assignment request with list of property IDs
        admin: Current admin user
        db: Database session

    Returns:
        Updated property assignments
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    assignment_repo = UserPropertyAssignmentRepository(db)

    # Get current assignments
    current_property_ids = await assignment_repo.get_property_ids_for_user(user_id)

    # Determine what to add and remove
    requested_ids = set(request.property_ids)
    current_ids = set(current_property_ids)

    to_add = requested_ids - current_ids
    to_remove = current_ids - requested_ids

    # Remove properties that are no longer assigned
    for property_id in to_remove:
        await assignment_repo.remove_assignment(user_id, property_id)

    # Add new property assignments
    for property_id in to_add:
        await assignment_repo.assign_property_to_user(
            user_id=user_id,
            property_id=property_id,
            assigned_by_user_id=admin.id,
        )

    # Get updated assignments
    updated_property_ids = await assignment_repo.get_property_ids_for_user(user_id)

    return PropertyAssignmentResponse(
        user_id=str(user_id),
        property_ids=[str(pid) for pid in updated_property_ids],
        assigned_count=len(updated_property_ids),
    )


@router.delete("/users/{user_id}/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property_from_user(
    user_id: UUID,
    property_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Remove a property assignment from a user (admin only).

    Args:
        user_id: User ID
        property_id: Property ID
        admin: Current admin user
        db: Database session
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    assignment_repo = UserPropertyAssignmentRepository(db)

    # Check if assignment exists
    property_ids = await assignment_repo.get_property_ids_for_user(user_id)
    if property_id not in property_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property assignment not found"
        )

    # Remove assignment
    await assignment_repo.remove_assignment(user_id, property_id)


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Deactivate a user (admin only).

    Deactivated users cannot log in.

    Args:
        user_id: User ID
        admin: Current admin user
        db: Database session

    Returns:
        Updated user
    """
    user_repo = UserRepository(db)
    user = await user_repo.deactivate_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        oauth_provider=user.oauth_provider,
        oauth_picture_url=user.oauth_picture_url,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat(),
    )


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Activate a user (admin only).

    Args:
        user_id: User ID
        admin: Current admin user
        db: Database session

    Returns:
        Updated user
    """
    user_repo = UserRepository(db)
    user = await user_repo.activate_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        oauth_provider=user.oauth_provider,
        oauth_picture_url=user.oauth_picture_url,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat(),
    )
