"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from smartbook.config import settings
from smartbook.domain.database import engine
from smartbook.api.routes import health, guest_portal, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup: Database connection pool is already initialized
    yield
    # Shutdown: Close database connections
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Multi-tenant web application for automated group check-in and compliance management",
    version=settings.version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(guest_portal.router, prefix="/api/guest", tags=["Guest Portal"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
