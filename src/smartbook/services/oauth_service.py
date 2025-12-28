"""
OAuth 2.0 service for Google authentication.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.user import User
from smartbook.repositories.user import UserRepository
from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository
from smartbook.services.jwt_service import JWTService
from smartbook.config import settings


class OAuthService:
    """Handle OAuth authentication flows."""

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.assignment_repo = UserPropertyAssignmentRepository(db)

    async def handle_google_callback(
        self,
        code: str,
        redirect_uri: str,
    ) -> tuple[User, str, str, list[UUID]]:
        """
        Handle Google OAuth callback.

        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in the OAuth flow

        Returns:
            Tuple of (User, access_token, refresh_token, property_ids)

        Raises:
            ValueError: If OAuth flow fails
        """
        # 1. Exchange code for tokens
        token_data = await self._exchange_code_for_tokens(code, redirect_uri)

        # 2. Get user info from Google
        user_info = await self._get_google_user_info(token_data["access_token"])

        # 3. Create or update user in database
        user = await self._get_or_create_user(
            email=user_info["email"],
            name=user_info.get("name", user_info["email"]),
            picture_url=user_info.get("picture"),
            oauth_provider_id=user_info["sub"],
        )

        # 4. Get user's property assignments
        property_ids = await self.assignment_repo.get_property_ids_for_user(user.id)

        # 5. Generate JWT tokens
        access_token = JWTService.create_access_token(user, property_ids)
        refresh_token = JWTService.create_refresh_token(user)

        # 6. Update last_login_at
        user.last_login_at = datetime.utcnow()
        await self.user_repo.update(user)

        return user, access_token, refresh_token, property_ids

    async def _exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access/refresh tokens.

        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in the OAuth flow

        Returns:
            Token response from Google

        Raises:
            ValueError: If token exchange fails
        """
        async with AsyncOAuth2Client(
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
        ) as client:
            try:
                token_response = await client.fetch_token(
                    self.GOOGLE_TOKEN_URL,
                    grant_type="authorization_code",
                    code=code,
                    redirect_uri=redirect_uri,
                )
                return token_response
            except Exception as e:
                raise ValueError(f"Failed to exchange code for tokens: {str(e)}")

    async def _get_google_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Get user information from Google.

        Args:
            access_token: Google access token

        Returns:
            User info dictionary with email, name, sub, picture

        Raises:
            ValueError: If user info fetch fails
        """
        async with AsyncOAuth2Client(token={"access_token": access_token}) as client:
            try:
                response = await client.get(self.GOOGLE_USERINFO_URL)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise ValueError(f"Failed to get user info from Google: {str(e)}")

    async def _get_or_create_user(
        self,
        email: str,
        name: str,
        picture_url: str | None,
        oauth_provider_id: str,
    ) -> User:
        """
        Get existing user or create new one.

        Handles three cases:
        1. User exists with OAuth provider ID → Update info and return
        2. User exists with email (migration case) → Update OAuth info and return
        3. New user → Create with default role 'admin'

        Args:
            email: User email address
            name: User full name
            picture_url: Profile picture URL (optional)
            oauth_provider_id: OAuth provider user ID (Google sub)

        Returns:
            User object
        """
        # Try to find by OAuth provider ID
        user = await self.user_repo.get_by_oauth_provider_id("google", oauth_provider_id)

        if user:
            # Update user info
            user.name = name
            user.oauth_picture_url = picture_url
            await self.user_repo.update(user)
            return user

        # Try to find by email (migration case - user created from property email)
        user = await self.user_repo.get_by_email(email)

        if user:
            # Update OAuth info for migrated user
            user.oauth_provider = "google"
            user.oauth_provider_id = oauth_provider_id
            user.name = name
            user.oauth_picture_url = picture_url
            await self.user_repo.update(user)
            return user

        # Create new user
        new_user = User(
            email=email,
            name=name,
            oauth_provider="google",
            oauth_provider_id=oauth_provider_id,
            oauth_picture_url=picture_url,
            role="admin",  # Default role for new users
            is_active=True,
        )
        return await self.user_repo.create(new_user)

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> tuple[str, User, list[UUID]]:
        """
        Generate new access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, user, property_ids)

        Raises:
            ValueError: If refresh token is invalid or expired
        """
        # Verify refresh token
        try:
            payload = JWTService.verify_token(refresh_token)
        except ValueError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")

        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")

        # Get user
        user_id = UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Get property assignments
        property_ids = await self.assignment_repo.get_property_ids_for_user(user.id)

        # Generate new access token
        new_access_token = JWTService.create_access_token(user, property_ids)

        return new_access_token, user, property_ids
