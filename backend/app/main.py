"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import health, patients
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    On startup:
    - Creates all database tables
    - Loads data from CSV files
    - Generates initial snapshots
    """
    # Startup
    logger.info("Starting up application...")
    try:
        # Import here to avoid circular imports
        from backend.app.db.bootstrap_db import main as bootstrap_main
        from backend.app.db.snapshot_builder import refresh_snapshots
        
        logger.info("Creating database tables and loading data...")
        # Only load data if tables are empty (don't force reseed on every startup)
        bootstrap_main(force_reseed=False)
        
        logger.info("Generating initial snapshots...")
        refresh_snapshots(hours_threshold=48)
        
        logger.info("Application startup complete.")
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        # Don't raise - allow app to start even if bootstrap fails
        # This allows the app to run in environments where DB might not be ready
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Patient Monitoring System API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(patients.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Patient Monitoring System API", "version": "1.0.0"}

