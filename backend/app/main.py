"""
Alamo GAM - Main FastAPI Application

Management system for Positron GAM equipment.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import api_router
from app.services.splynx_provisioning import start_background_task, stop_background_task
from app.services.splynx_reconciliation import start_reconciliation_task, stop_reconciliation_task
from app.services.offline_detection import start_offline_detection, stop_offline_detection
from app.services.purge_service import start_purge_task, stop_purge_task
from app.services.polling_service import start_polling, stop_polling
from app.api.settings import ensure_default_settings
from app.core.database import async_session_maker

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress noisy SQLAlchemy query logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    logger.info("Database initialized")

    # Seed any new default settings (existing values are preserved)
    async with async_session_maker() as db:
        await ensure_default_settings(db)
    logger.info("Default settings ensured")

    # Start background tasks
    start_background_task()
    start_reconciliation_task()
    start_offline_detection()
    start_purge_task()
    start_polling()
    logger.info("Background tasks started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    stop_background_task()
    stop_reconciliation_task()
    stop_offline_detection()
    stop_purge_task()
    stop_polling()
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.brand_name,
    version=settings.app_version,
    description="GAM Device Management System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# System info endpoint
@app.get("/info")
async def system_info():
    """Get system information for branding."""
    return {
        "brand_name": settings.brand_name,
        "brand_logo_url": settings.brand_logo_url,
        "brand_primary_color": settings.brand_primary_color,
        "version": settings.app_version,
    }


# Include API routes
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
