"""Health check routes."""
from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.patient import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="Service is operational")

