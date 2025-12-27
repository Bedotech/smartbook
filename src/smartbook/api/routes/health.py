"""
Health check endpoints.
"""

from fastapi import APIRouter

from smartbook.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "smartbook-api",
        "version": settings.version,
    }


@router.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        API metadata
    """
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": "Multi-tenant group check-in and compliance for Italian hospitality",
        "docs": "/api/docs",
        "health": "/api/health",
    }
