"""Patient API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from backend.app.schemas.patient import PatientDetailResponse, PatientMonitoringResponse
from backend.app.services.patient_service import get_latest_monitoring_snapshot, get_patient_detail

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/monitoring", response_model=PatientMonitoringResponse)
async def get_patients_monitoring(
    hours_threshold: int = Query(48, ge=1, description="Hours threshold for filtering"),
    department: Optional[str] = Query(None, description="Filter by department"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=10000, description="Items per page"),
) -> PatientMonitoringResponse:
    """Get patients requiring attention (hospitalized >48h without new tests)."""
    return get_latest_monitoring_snapshot(
        hours_threshold=hours_threshold,
        department=department,
        page=page,
        limit=limit,
    )


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_details(patient_id: int = Path(..., ge=1, description="Patient ID")) -> PatientDetailResponse:
    """Get detailed patient information with lab results and charts."""
    detail = get_patient_detail(patient_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return detail

