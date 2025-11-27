"""Patient service for retrieving snapshot data."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import MetaData, Table, create_engine, desc, text
from sqlalchemy.orm import Session

from backend.app.db.snapshot_builder import refresh_snapshots
from backend.app.db.utils import get_database_url
from backend.app.schemas.patient import PatientDetailResponse, PatientMonitoringResponse


def _parse_duration_hours(duration: Optional[str]) -> Optional[int]:
    """
    Convert a formatted duration string (e.g. '1w, 2d, 3h') back to hours.

    Returns None for missing or sentinel values like 'N/A' or 'No tests'.
    """
    if not duration or duration in {"N/A", "No tests"}:
        return None
    total_hours = 0
    for part in duration.split(","):
        token = part.strip()
        if not token:
            continue
        suffix = token[-1]
        try:
            value = int(token[:-1])
        except ValueError:
            continue
        if suffix == "y":
            total_hours += value * 365 * 24
        elif suffix == "w":
            total_hours += value * 7 * 24
        elif suffix == "d":
            total_hours += value * 24
        elif suffix == "h":
            total_hours += value
    return total_hours or None


def get_latest_monitoring_snapshot(
    hours_threshold: int = 48,
    department: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> PatientMonitoringResponse:
    """
    Retrieve the latest patient monitoring snapshot with optional filtering and pagination.
    
    Queries the patient_monitoring_snapshots table for the most recent snapshot matching
    the hours_threshold. If no snapshot exists, attempts to generate one automatically.
    Applies department filtering and pagination to the results.
    
    Args:
        hours_threshold: Minimum hours since admission/last test threshold. Defaults to 48.
        department: Optional department name to filter by. If None, returns all departments.
        page: Page number for pagination (1-indexed). Defaults to 1.
        limit: Maximum number of results per page. Defaults to 50.
    
    Returns:
        PatientMonitoringResponse containing:
        - data: List of patient monitoring records
        - pagination: Dictionary with page, limit, and total count
    
    Note:
        Automatically generates snapshots if none exist for the given threshold.
    """
    engine = create_engine(get_database_url())
    metadata = MetaData()
    with engine.connect() as conn:
        table = Table("patient_monitoring_snapshots", metadata, autoload_with=conn)
        query = (
            table.select()
            .where(table.c.deleted_at.is_(None))
            .where(table.c.hours_threshold == hours_threshold)
            .order_by(desc(table.c.response_created_at))
        )
        result = conn.execute(query).first()
        if not result:
            # No snapshot found, try to generate one
            try:
                refresh_snapshots(hours_threshold=hours_threshold)
                # Retry query after generating snapshot
                result = conn.execute(query).first()
                if not result:
                    return PatientMonitoringResponse(data=[], pagination={"page": page, "limit": limit, "total": 0})
            except Exception as e:
                import traceback
                print(f"Error generating snapshots: {e}")
                traceback.print_exc()
                return PatientMonitoringResponse(data=[], pagination={"page": page, "limit": limit, "total": 0})
        payload = result.payload
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        patients = payload.get("patients", [])
        normalized_patients = []
        for patient in patients:
            entry = dict(patient)
            if (not entry.get("time_since_last_test") or entry.get("time_since_last_test") == "N/A") and not entry.get(
                "last_test_datetime"
            ):
                entry["time_since_last_test"] = "No tests"
            if "needs_alert" not in entry:
                duration_hours = _parse_duration_hours(entry.get("time_since_last_test"))
                entry["needs_alert"] = True if duration_hours is None else duration_hours >= hours_threshold
            else:
                entry["needs_alert"] = bool(entry["needs_alert"])
            normalized_patients.append(entry)
        patients = normalized_patients
        if department:
            patients = [p for p in patients if p.get("department") == department]
        total = len(patients)
        start = (page - 1) * limit
        end = start + limit
        paginated = patients[start:end]
        return PatientMonitoringResponse(
            data=paginated,
            pagination={"page": page, "limit": limit, "total": total},
        )


def get_patient_detail(patient_id: int) -> Optional[PatientDetailResponse]:
    """
    Retrieve detailed patient information from the latest snapshot.
    
    Queries the patient_detail_snapshots table for the most recent snapshot for the
    given patient_id. If no snapshot exists, attempts to generate one automatically.
    Returns comprehensive patient information including lab results and chart data.
    
    Args:
        patient_id: Unique identifier of the patient.
    
    Returns:
        PatientDetailResponse containing:
        - Patient demographics (name, age, insurance, blood type, allergies)
        - Admission information (department, room, admission datetime)
        - Latest lab results per test type
        - Chart series data for lab results over time
        - Last test summary
        None if patient not found or snapshot generation fails.
    
    Note:
        Automatically generates snapshots if none exist for the patient.
    """
    engine = create_engine(get_database_url())
    metadata = MetaData()
    with engine.connect() as conn:
        table = Table("patient_detail_snapshots", metadata, autoload_with=conn)
        query = (
            table.select()
            .where(table.c.patient_id == patient_id)
            .where(table.c.deleted_at.is_(None))
            .order_by(desc(table.c.response_created_at))
        )
        result = conn.execute(query).first()
        if not result:
            # No snapshot found, try to generate one
            try:
                refresh_snapshots()
                # Retry query after generating snapshot
                result = conn.execute(query).first()
                if not result:
                    return None
            except Exception as e:
                import traceback
                print(f"Error generating snapshots: {e}")
                traceback.print_exc()
                return None
        payload = result.payload
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        return PatientDetailResponse(**payload)

