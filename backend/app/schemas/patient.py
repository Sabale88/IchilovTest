"""Patient-related Pydantic schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PatientMonitoringItem(BaseModel):
    """Single patient in monitoring list."""

    patient_id: int
    case_number: int
    name: str
    age: Optional[int]
    department: Optional[str]
    room_number: Optional[str]
    admission_datetime: Optional[str]
    admission_length: str
    last_test_datetime: Optional[str]
    time_since_last_test: Optional[str]
    last_test_name: Optional[str]
    primary_physician: Optional[str]
    needs_alert: bool = True


class PatientMonitoringResponse(BaseModel):
    """Monitoring endpoint response."""

    data: list[PatientMonitoringItem]
    pagination: dict[str, int]


class LabResultItem(BaseModel):
    """Single lab result entry."""

    test_name: str
    order_date: Optional[str]
    order_time: Optional[str]
    ordering_physician: Optional[str]
    result_value: Optional[float]
    result_unit: Optional[str]
    reference_range: Optional[str]
    result_status: Optional[str]
    performed_date: Optional[str]
    performed_time: Optional[str]
    reviewing_physician: Optional[str]


class ChartPoint(BaseModel):
    """Chart data point."""

    timestamp: str
    value: Optional[float]
    result_status: Optional[str]


class ChartSeries(BaseModel):
    """Chart series for a test."""

    test_name: str
    points: list[ChartPoint]


class LastTestSummary(BaseModel):
    """Summary of last test."""

    test_name: str
    last_test_datetime: str
    hours_since_last_test: Optional[float]


class PatientDetailResponse(BaseModel):
    """Patient detail endpoint response."""

    patient_id: int
    name: str
    age: Optional[int]
    primary_physician: Optional[str]
    insurance_provider: Optional[str]
    blood_type: Optional[str]
    allergies: Optional[str]
    department: Optional[str]
    room_number: Optional[str]
    admission_datetime: Optional[str]
    hours_since_admission: Optional[float]
    last_test: Optional[LastTestSummary]
    latest_results: list[LabResultItem]
    chart_series: list[ChartSeries]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str

