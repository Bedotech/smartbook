"""
JWT token generation and validation service.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt

from smartbook.config import settings
from smartbook.domain.models.user import User


class JWTService:
    """Handle JWT token creation and validation."""

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    def create_access_token(user: User, property_ids: list[UUID]) -> str:
        """
        Create JWT access token.

        Token claims:
        - sub: user_id
        - email: user email
        - name: user name
        - role: admin or staff
        - property_ids: list of assigned property UUIDs
        - iat: issued at
        - exp: expiration (15 minutes)
        - type: access

        Args:
            user: User object
            property_ids: List of property UUIDs assigned to user

        Returns:
            Encoded JWT token string
        """
        now = datetime.utcnow()
        expiration = now + timedelta(minutes=JWTService.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "property_ids": [str(pid) for pid in property_ids],
            "iat": now,
            "exp": expiration,
            "type": "access",
        }

        return jwt.encode(payload, settings.secret_key, algorithm=JWTService.ALGORITHM)

    @staticmethod
    def create_refresh_token(user: User) -> str:
        """
        Create refresh token (7 days TTL).

        Token claims:
        - sub: user_id
        - iat: issued at
        - exp: expiration (7 days)
        - type: refresh

        Args:
            user: User object

        Returns:
            Encoded JWT token string
        """
        now = datetime.utcnow()
        expiration = now + timedelta(days=JWTService.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user.id),
            "iat": now,
            "exp": expiration,
            "type": "refresh",
        }

        return jwt.encode(payload, settings.secret_key, algorithm=JWTService.ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is expired or invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[JWTService.ALGORITHM],
            )
            return payload
        except JWTError as e:
            if "expired" in str(e).lower():
                raise ValueError("Token has expired")
            raise ValueError(f"Invalid token: {str(e)}")

    @staticmethod
    def decode_token_without_verification(token: str) -> dict[str, Any]:
        """
        Decode JWT token without verification (for debugging/inspection).

        Args:
            token: JWT token string

        Returns:
            Decoded token payload (unverified)
        """
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
