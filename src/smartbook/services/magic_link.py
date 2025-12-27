"""
Magic link token generation service.

Provides cryptographically secure token generation for passwordless
guest portal access.
"""

import secrets
from datetime import datetime, date, timedelta

from smartbook.config import settings


class MagicLinkService:
    """Service for generating and validating magic link tokens."""

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure token.

        Uses secrets module with configured byte length (default: 32 bytes = 256 bits).
        Returns URL-safe token as hexadecimal string.

        Returns:
            Secure random token (64 hex characters for 32 bytes)
        """
        return secrets.token_urlsafe(settings.magic_link_token_bytes)

    @staticmethod
    def calculate_expiration(check_out_date: date) -> datetime:
        """
        Calculate token expiration datetime.

        Tokens expire at end of day on check-out date for security.
        This prevents post-stay access to personal data.

        Args:
            check_out_date: The booking check-out date

        Returns:
            Expiration datetime (end of check-out day)
        """
        # Set expiration to end of check-out day (23:59:59)
        return datetime.combine(check_out_date, datetime.max.time())

    @staticmethod
    def is_token_expired(expires_at: datetime) -> bool:
        """
        Check if a token has expired.

        Args:
            expires_at: Token expiration datetime

        Returns:
            True if expired, False otherwise
        """
        return datetime.now(expires_at.tzinfo) > expires_at

    @staticmethod
    def generate_magic_link_url(token: str, base_url: str = "") -> str:
        """
        Generate the full magic link URL.

        Args:
            token: The magic link token
            base_url: Base URL of the guest portal (optional)

        Returns:
            Full magic link URL
        """
        if not base_url:
            base_url = "https://checkin.schilpario.app"  # TODO: Make configurable

        return f"{base_url}/s/{token}"
