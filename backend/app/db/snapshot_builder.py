"""Generate patient monitoring snapshots and patient detail payloads."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import MetaData, Table, create_engine, text

from backend.app.db.utils import get_database_url


def _coerce_date(value: Any) -> Optional[date]:
    """
    Coerce a value to a date object, handling multiple input types.
    
    Accepts date objects, datetime objects, or date strings in various formats.
    String formats attempted: d.m.yyyy, yyyy-mm-dd, mm/dd/yyyy.
    
    Args:
        value: Date, datetime, string, or None to coerce.
        
    Returns:
        Date object if coercion succeeds, None otherwise.
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _coerce_time(value: Any) -> Optional[time]:
    """
    Coerce a value to a time object, handling multiple input types.
    
    Accepts time objects, datetime objects, or time strings in various formats.
    String formats attempted: HH:MM:SS, HH:MM, I:M:S p, I:M p.
    
    Args:
        value: Time, datetime, string, or None to coerce.
        
    Returns:
        Time object if coercion succeeds, None otherwise.
    """
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                try:
                    return datetime.strptime(value, "%I:%M:%S %p").time()
                except ValueError:
                    try:
                        return datetime.strptime(value, "%I:%M %p").time()
                    except ValueError:
                        continue
    return None


def _combine_datetime(d: Any, t: Any) -> Optional[datetime]:
    """
    Combine separate date and time values into a datetime object.
    
    If time is None or cannot be coerced, uses time.min (00:00:00).
    Returns None if date cannot be coerced.
    
    Args:
        d: Date value (date, datetime, or string).
        t: Time value (time, datetime, or string).
        
    Returns:
        Combined datetime object, or None if date cannot be coerced.
    """
    coerced_date = _coerce_date(d)
    if coerced_date is None:
        return None
    coerced_time = _coerce_time(t) or time.min
    return datetime.combine(coerced_date, coerced_time)


def _hours_between(start: Optional[datetime], end: datetime) -> Optional[float]:
    """
    Calculate the number of hours between two datetime objects.
    
    Args:
        start: Starting datetime, or None.
        end: Ending datetime.
        
    Returns:
        Hours as a float rounded to 2 decimal places, or None if start is None.
    """
    if start is None:
        return None
    delta = end - start
    return round(delta.total_seconds() / 3600.0, 2)


def _format_duration(hours: Optional[float]) -> str:
    """Format duration in hours to '3y, 2w, 5d, 6h' format."""
    if hours is None or hours < 0:
        return "N/A"
    
    total_hours = int(hours)
    years = total_hours // (365 * 24)
    remaining_hours = total_hours % (365 * 24)
    weeks = remaining_hours // (7 * 24)
    remaining_hours = remaining_hours % (7 * 24)
    days = remaining_hours // 24
    hours_remaining = remaining_hours % 24
    
    parts = []
    if years > 0:
        parts.append(f"{years}y")
    if weeks > 0:
        parts.append(f"{weeks}w")
    if days > 0:
        parts.append(f"{days}d")
    if hours_remaining > 0 or not parts:
        parts.append(f"{hours_remaining}h")
    
    return ", ".join(parts)


def _calculate_age(date_of_birth: Optional[date], reference_date: datetime) -> Optional[int]:
    """
    Calculate age in years from date of birth to a reference date.
    
    Accounts for whether the birthday has occurred in the reference year.
    
    Args:
        date_of_birth: Birth date, or None.
        reference_date: Date to calculate age as of.
        
    Returns:
        Age in years as an integer, or None if date_of_birth is None.
    """
    if date_of_birth is None:
        return None
    age = reference_date.year - date_of_birth.year
    if (reference_date.month, reference_date.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age


def _max_datetime(*values: Optional[datetime]) -> Optional[datetime]:
    """
    Find the maximum (latest) datetime from a variable number of datetime values.
    
    Filters out None values before finding the maximum.
    
    Args:
        *values: Variable number of datetime objects or None.
        
    Returns:
        The latest datetime, or None if all values are None.
    """
    filtered = [v for v in values if v is not None]
    if not filtered:
        return None
    return max(filtered)


def _to_float(value: Any) -> Optional[float]:
    """
    Convert a value to a float, handling Decimal and other numeric types.
    
    Args:
        value: Value to convert (Decimal, numeric, string, or None).
        
    Returns:
        Float value if conversion succeeds, None otherwise.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_date(value: Any) -> Optional[str]:
    coerced = _coerce_date(value)
    return coerced.strftime("%d.%m.%Y") if coerced else None


def _format_time(value: Any) -> Optional[str]:
    coerced = _coerce_time(value)
    if coerced is None:
        return None
    return coerced.strftime("%H:%M")


def _organize_tests(rows: Sequence[Dict[str, Any]]) -> Tuple[Dict[int, List[Dict[str, Any]]], Dict[int, Dict[str, Any]]]:
    """
    Organize lab test rows by patient and identify the most recent test per patient.
    
    Groups all tests by patient_id and determines the latest test event (based on
    order or performed datetime) for each patient. Adds internal datetime fields
    to each test record for processing.
    
    Args:
        rows: Sequence of lab test/result dictionaries with patient_id, order_date,
              order_time, performed_date, performed_time, and test_name.
        
    Returns:
        Tuple of:
        - Dictionary mapping patient_id to list of all test records with added
          _order_dt, _result_dt, and _event_dt fields.
        - Dictionary mapping patient_id to the most recent test info (timestamp,
          test_name, order_datetime, result_datetime).
    """
    patient_tests: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    last_tests: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        patient_id = row["patient_id"]
        order_dt = _combine_datetime(row.get("order_date"), row.get("order_time"))
        result_dt = _combine_datetime(row.get("performed_date"), row.get("performed_time"))
        event_ts = _max_datetime(order_dt, result_dt)
        payload = dict(row)
        payload["_order_dt"] = order_dt
        payload["_result_dt"] = result_dt
        payload["_event_dt"] = event_ts
        patient_tests[patient_id].append(payload)
        if event_ts is None:
            continue
        current = last_tests.get(patient_id)
        if current is None or event_ts > current["timestamp"]:
            last_tests[patient_id] = {
                "timestamp": event_ts,
                "test_name": row["test_name"],
                "order_datetime": order_dt,
                "result_datetime": result_dt,
            }
    return patient_tests, last_tests


def _is_active(admission_row: Dict[str, Any], now: datetime, grace: timedelta) -> bool:
    """
    Determine if an admission is considered active.
    
    An admission is active if:
    - No release date/time is set, OR
    - The release occurred within the grace period (e.g., within 2 hours of now).
    
    Args:
        admission_row: Dictionary containing release_date and release_time.
        now: Current datetime for comparison.
        grace: Time delta representing the grace period after release.
        
    Returns:
        True if admission is active, False otherwise.
    """
    release_dt = _combine_datetime(admission_row.get("release_date"), admission_row.get("release_time"))
    if release_dt is None:
        return True
    return now - release_dt <= grace


def _build_detail_payload(
    admission_row: Dict[str, Any],
    tests: List[Dict[str, Any]],
    last_test: Optional[Dict[str, Any]],
    now: datetime,
    admission_dt: Optional[datetime],
    hours_since_admission: Optional[float],
) -> Dict[str, Any]:
    latest_per_test: Dict[str, Dict[str, Any]] = {}
    chart_points: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for record in tests:
        event_ts = record.get("_event_dt")
        if event_ts is None:
            continue
        test_name = record["test_name"]
        entry = {
            "test_name": test_name,
            "order_date": _format_date(record.get("order_date")),
            "order_time": _format_time(record.get("order_time")),
            "ordering_physician": record.get("ordering_physician"),
            "result_value": _to_float(record.get("result_value")),
            "result_unit": record.get("result_unit"),
            "reference_range": record.get("reference_range"),
            "result_status": record.get("result_status"),
            "performed_date": _format_date(record.get("performed_date")),
            "performed_time": _format_time(record.get("performed_time")),
            "reviewing_physician": record.get("reviewing_physician"),
        }
        entry["_event_dt"] = event_ts
        current = latest_per_test.get(test_name)
        if current is None or event_ts > current["_event_dt"]:
            latest_per_test[test_name] = entry

        chart_points[test_name].append(
            {
                "timestamp": event_ts.strftime("%d.%m.%Y %H:%M:%S"),
                "value": _to_float(record.get("result_value")),
                "result_status": record.get("result_status"),
            }
        )

    latest_results: List[Dict[str, Any]] = []
    for test_name, result in sorted(latest_per_test.items(), key=lambda item: item[1]["_event_dt"], reverse=True):
        formatted = {k: v for k, v in result.items() if k != "_event_dt"}
        latest_results.append(formatted)

    series = []
    for test_name, points in chart_points.items():
        ordered_points = sorted(points, key=lambda p: p["timestamp"])
        series.append({"test_name": test_name, "points": ordered_points})

    last_test_summary = None
    if last_test:
        last_test_summary = {
            "test_name": last_test["test_name"],
            "last_test_datetime": last_test["timestamp"].strftime("%d.%m.%Y %H:%M:%S"),
            "hours_since_last_test": _hours_between(last_test["timestamp"], now),
        }

    date_of_birth = _coerce_date(admission_row.get("date_of_birth"))
    age = _calculate_age(date_of_birth, now) if date_of_birth else None

    return {
        "patient_id": admission_row["patient_id"],
        "name": f"{admission_row['first_name']} {admission_row['last_name']}",
        "age": age,
        "primary_physician": admission_row.get("primary_physician"),
        "insurance_provider": admission_row.get("insurance_provider"),
        "blood_type": admission_row.get("blood_type"),
        "allergies": admission_row.get("allergies"),
        "department": admission_row.get("department"),
        "room_number": admission_row.get("room_number"),
        "admission_datetime": admission_dt.strftime("%d.%m.%Y %H:%M:%S") if admission_dt else None,
        "hours_since_admission": hours_since_admission,
        "last_test": last_test_summary,
        "latest_results": latest_results,
        "chart_series": series,
    }


def refresh_snapshots(hours_threshold: int = 48, release_grace_minutes: int = 120) -> Dict[str, Any]:
    """
    Recompute and persist both monitoring and detail snapshots.
    
    Queries the database for active admissions and lab tests, processes the data
    to identify patients requiring attention (hospitalized >48h without new tests),
    and stores pre-computed JSON payloads in snapshot tables for efficient
    frontend retrieval.
    
    Args:
        hours_threshold: Minimum hours since admission/last test to include patient.
                         Defaults to 48.
        release_grace_minutes: Minutes after release to still consider admission active.
                               Defaults to 120 (2 hours).
    
    Returns:
        Dictionary with summary statistics (e.g., number of patients processed).
    """
    engine = create_engine(get_database_url())
    now = datetime.now()
    grace = timedelta(minutes=release_grace_minutes)

    admissions_query = text(
        """
        SELECT
            p.patient_id,
            p.first_name,
            p.last_name,
            p.date_of_birth,
            p.primary_physician,
            p.insurance_provider,
            p.blood_type,
            p.allergies,
            a.hospitalization_case_number,
            a.department,
            a.room_number,
            a.admission_date,
            a.admission_time,
            a.release_date,
            a.release_time
        FROM admissions a
        JOIN patients p ON p.patient_id = a.patient_id
        """
    )

    labs_query = text(
        """
        SELECT
            lt.patient_id,
            lt.test_id,
            lt.test_name,
            lt.order_date,
            lt.order_time,
            lt.ordering_physician,
            lr.result_id,
            lr.result_value,
            lr.result_unit,
            lr.reference_range,
            lr.result_status,
            lr.performed_date,
            lr.performed_time,
            lr.reviewing_physician
        FROM lab_tests lt
        LEFT JOIN lab_results lr ON lr.test_id = lt.test_id
        """
    )

    with engine.begin() as conn:
        metadata = MetaData()
        monitoring_table = Table("patient_monitoring_snapshots", metadata, autoload_with=conn)
        detail_table = Table("patient_detail_snapshots", metadata, autoload_with=conn)

        admissions_rows = conn.execute(admissions_query).mappings().all()
        lab_rows = conn.execute(labs_query).mappings().all()

        patient_tests, last_tests = _organize_tests(lab_rows)

        monitoring_entries: List[Dict[str, Any]] = []
        detail_snapshots: List[Tuple[int, Dict[str, Any]]] = []

        for admission in admissions_rows:
            admission_dt = _combine_datetime(admission.get("admission_date"), admission.get("admission_time"))
            if admission_dt is None:
                continue
            if not _is_active(admission, now, grace):
                continue

            hours_since_admission = _hours_between(admission_dt, now) or 0.0
            if hours_since_admission < hours_threshold:
                continue

            last_test = last_tests.get(admission["patient_id"])
            hours_since_last_test = _hours_between(last_test["timestamp"], now) if last_test else None
            needs_alert = hours_since_last_test is None or hours_since_last_test >= hours_threshold

            date_of_birth = _coerce_date(admission.get("date_of_birth"))
            age = _calculate_age(date_of_birth, now) if date_of_birth else None
            time_since_last_test = (
                _format_duration(hours_since_last_test) if hours_since_last_test is not None else "No tests"
            )
            
            entry = {
                "patient_id": admission["patient_id"],
                "case_number": admission["hospitalization_case_number"],
                "name": f"{admission['first_name']} {admission['last_name']}",
                "age": age,
                "department": admission.get("department"),
                "room_number": admission.get("room_number"),
                "admission_datetime": admission_dt.strftime("%d.%m.%Y %H:%M:%S"),
                "admission_length": _format_duration(hours_since_admission),
                "last_test_datetime": last_test["timestamp"].strftime("%d.%m.%Y %H:%M:%S") if last_test else None,
                "time_since_last_test": time_since_last_test,
                "last_test_name": last_test["test_name"] if last_test else None,
                "primary_physician": admission.get("primary_physician"),
                "needs_alert": needs_alert,
            }
            monitoring_entries.append(entry)

            detail_payload = _build_detail_payload(
                admission,
                patient_tests.get(admission["patient_id"], []),
                last_test,
                now,
                admission_dt,
                hours_since_admission,
            )
            detail_snapshots.append((admission["patient_id"], detail_payload))

        # Store hours for sorting before formatting
        for entry in monitoring_entries:
            patient_id = entry["patient_id"]
            admission_for_patient = next((a for a in admissions_rows if a["patient_id"] == patient_id), None)
            if admission_for_patient:
                admission_dt = _combine_datetime(
                    admission_for_patient.get("admission_date"),
                    admission_for_patient.get("admission_time")
                )
                hours_since_admission = _hours_between(admission_dt, now) or 0.0
                last_test = last_tests.get(patient_id)
                last_hours = _hours_between(last_test["timestamp"], now) if last_test else None
                entry["_sort_hours_admission"] = hours_since_admission
                entry["_sort_hours_last_test"] = last_hours
        
        def _monitor_sort_key(item: Dict[str, Any]) -> Tuple[int, float]:
            alert_bucket = 0 if item.get("needs_alert", True) else 1
            last_hours = item.get("_sort_hours_last_test")
            if last_hours is None:
                return (alert_bucket, -item.get("_sort_hours_admission", 0.0))
            return (alert_bucket, -last_hours)

        monitoring_entries = sorted(monitoring_entries, key=_monitor_sort_key)
        # Remove sorting helper fields
        for entry in monitoring_entries:
            entry.pop("_sort_hours_admission", None)
            entry.pop("_sort_hours_last_test", None)
        # Remove sorting helper fields
        for entry in monitoring_entries:
            entry.pop("_sort_hours_admission", None)
            entry.pop("_sort_hours_last_test", None)

        monitoring_payload = {
            "generated_at": now.strftime("%d.%m.%Y %H:%M:%S"),
            "hours_threshold": hours_threshold,
            "patients": monitoring_entries,
        }

        inserted = conn.execute(
            monitoring_table.insert().values(
                response_created_at=now,
                hours_threshold=hours_threshold,
                payload=monitoring_payload,
            )
        )

        for patient_id, payload in detail_snapshots:
            conn.execute(
                detail_table.insert().values(
                    patient_id=patient_id,
                    response_created_at=now,
                    payload=payload,
                )
            )

        return {
            "monitoring_snapshot_id": inserted.inserted_primary_key[0] if inserted.inserted_primary_key else None,
            "patient_count": len(monitoring_entries),
            "detail_snapshots": len(detail_snapshots),
        }


def main() -> None:
    summary = refresh_snapshots()
    print(
        f"Created monitoring snapshot {summary['monitoring_snapshot_id']} "
        f"for {summary['patient_count']} patients and {summary['detail_snapshots']} detail payloads."
    )


if __name__ == "__main__":
    main()

