"""Bootstrap database: create tables and load CSV seed data."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Time,
    create_engine,
)
from sqlalchemy.dialects.postgresql import BIGINT

from backend.app.db.utils import (
    chunked,
    get_database_url,
    normalized,
    parse_date,
    parse_decimal,
    parse_time,
    read_csv,
    utcnow_sql,
)

metadata = MetaData()


patients = Table(
    "patients",
    metadata,
    Column("patient_id", BIGINT, primary_key=True),
    Column("first_name", String(100), nullable=False),
    Column("last_name", String(100), nullable=False),
    Column("date_of_birth", Date, nullable=False),
    Column("primary_physician", String(200)),
    Column("insurance_provider", String(100)),
    Column("blood_type", String(10)),
    Column("allergies", String),
    Column("created_at", DateTime, server_default=utcnow_sql(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=utcnow_sql(),
        onupdate=utcnow_sql(),
        nullable=False,
    ),
    Column("deleted_at", DateTime),
    mysql_engine="InnoDB",
)

admissions = Table(
    "admissions",
    metadata,
    Column("hospitalization_case_number", BIGINT, primary_key=True),
    Column("patient_id", BIGINT, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
    Column("admission_date", Date, nullable=False),
    Column("admission_time", Time, nullable=False),
    Column("release_date", Date),
    Column("release_time", Time),
    Column("department", String(100)),
    Column("room_number", String(20)),
    Column("created_at", DateTime, server_default=utcnow_sql(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=utcnow_sql(),
        onupdate=utcnow_sql(),
        nullable=False,
    ),
    Column("deleted_at", DateTime),
    mysql_engine="InnoDB",
)

lab_tests = Table(
    "lab_tests",
    metadata,
    Column("test_id", BIGINT, primary_key=True),
    Column("patient_id", BIGINT, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
    Column("test_name", String(200), nullable=False),
    Column("order_date", Date, nullable=False),
    Column("order_time", Time, nullable=False),
    Column("ordering_physician", String(200)),
    Column("created_at", DateTime, server_default=utcnow_sql(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=utcnow_sql(),
        onupdate=utcnow_sql(),
        nullable=False,
    ),
    Column("deleted_at", DateTime),
    mysql_engine="InnoDB",
)

lab_results = Table(
    "lab_results",
    metadata,
    Column("result_id", BIGINT, primary_key=True),
    Column("test_id", BIGINT, ForeignKey("lab_tests.test_id", ondelete="CASCADE"), nullable=False),
    Column("result_value", Numeric(20, 10)),
    Column("result_unit", String(100)),
    Column("reference_range", String(255)),
    Column("result_status", String(50)),
    Column("performed_date", Date, nullable=False),
    Column("performed_time", Time, nullable=False),
    Column("reviewing_physician", String(200)),
    Column("created_at", DateTime, server_default=utcnow_sql(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=utcnow_sql(),
        onupdate=utcnow_sql(),
        nullable=False,
    ),
    Column("deleted_at", DateTime),
    mysql_engine="InnoDB",
)

patient_monitoring_snapshots = Table(
    "patient_monitoring_snapshots",
    metadata,
    Column("snapshot_id", Integer, primary_key=True, autoincrement=True),
    Column("response_created_at", DateTime, nullable=False),
    Column("hours_threshold", Integer, nullable=False, default=48),
    Column("payload", JSON, nullable=False),
    Column("created_at", DateTime, server_default=utcnow_sql(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=utcnow_sql(),
        onupdate=utcnow_sql(),
        nullable=False,
    ),
    Column("deleted_at", DateTime),
)

patient_detail_snapshots = Table(
    "patient_detail_snapshots",
    metadata,
    Column("snapshot_id", Integer, primary_key=True, autoincrement=True),
    Column("patient_id", BIGINT, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
    Column("response_created_at", DateTime, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("created_at", DateTime, server_default=utcnow_sql(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=utcnow_sql(),
        onupdate=utcnow_sql(),
        nullable=False,
    ),
    Column("deleted_at", DateTime),
)


def purge_existing_data(conn) -> None:
    """Remove existing rows so the script can be rerun safely."""
    for table in (
        patient_monitoring_snapshots,
        patient_detail_snapshots,
        lab_results,
        lab_tests,
        admissions,
        patients,
    ):
        conn.execute(table.delete())


def load_patients(rows: Iterable[Dict[str, str]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in rows:
        data.append(
            {
                "patient_id": int(row["patient_id"]),
                "first_name": row["first_name"].strip(),
                "last_name": row["last_name"].strip(),
                "date_of_birth": parse_date(row["date_of_birth"]),
                "primary_physician": normalized(row.get("primary_physician")),
                "insurance_provider": normalized(row.get("insurance_provider")),
                "blood_type": normalized(row.get("blood_type")),
                "allergies": normalized(row.get("allergies")),
            }
        )
    return data


def load_admissions(rows: Iterable[Dict[str, str]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in rows:
        release_date_raw: Optional[str] = row.get("release_date") or None
        release_time_raw: Optional[str] = row.get("release_time") or None
        data.append(
            {
                "hospitalization_case_number": int(row["hospitalization_case_number"]),
                "patient_id": int(row["patient_id"]),
                "admission_date": parse_date(row["admission_date"]),
                "admission_time": parse_time(row["admission_time"]),
                "release_date": parse_date(release_date_raw),
                "release_time": parse_time(release_time_raw),
                "department": normalized(row.get("department")),
                "room_number": normalized(row.get("room_number")),
            }
        )
    return data


def load_lab_tests(rows: Iterable[Dict[str, str]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in rows:
        data.append(
            {
                "test_id": int(row["test_id"]),
                "patient_id": int(row["patient_id"]),
                "test_name": row["test_name"].strip(),
                "order_date": parse_date(row["order_date"]),
                "order_time": parse_time(row["order_time"]),
                "ordering_physician": normalized(row.get("ordering_physician")),
            }
        )
    return data


def load_lab_results(rows: Iterable[Dict[str, str]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in rows:
        data.append(
            {
                "result_id": int(row["result_id"]),
                "test_id": int(row["test_id"]),
                "result_value": parse_decimal(row["result_value"]),
                "result_unit": normalized(row.get("result_unit")),
                "reference_range": normalized(row.get("reference_range")),
                "result_status": normalized(row.get("result_status")),
                "performed_date": parse_date(row["performed_date"]),
                "performed_time": parse_time(row["performed_time"]),
                "reviewing_physician": normalized(row.get("reviewing_physician")),
            }
        )
    return data


def main(force_reseed: bool = False) -> None:
    """
    Create database tables and load CSV seed data.
    
    Creates all tables if they don't exist. If force_reseed is True or tables are empty,
    loads data from CSV files. If force_reseed is False and data exists, skips loading.
    
    Args:
        force_reseed: If True, purge existing data and reload. If False, only load if
                     tables are empty. Defaults to False.
    """
    engine = create_engine(get_database_url())
    metadata.create_all(engine, checkfirst=True)

    with engine.begin() as conn:
        has_data = conn.execute(patients.select().limit(1)).first() is not None
        
        if force_reseed and has_data:
            print("Existing data found; purging tables before reseeding.")
            purge_existing_data(conn)
            has_data = False
        
        if not has_data:
            print("Loading data from CSV files...")
            patient_rows = load_patients(read_csv("patient_information.csv", drop_pk=["patient_id"]))
            admission_rows = load_admissions(read_csv("admissions.csv", drop_pk=["hospitalization_case_number"]))
            test_rows = load_lab_tests(read_csv("lab_tests.csv", drop_pk=["test_id"]))
            results_rows = load_lab_results(read_csv("lab_results.csv", drop_pk=["result_id"]))

            for batch in chunked(patient_rows):
                conn.execute(patients.insert(), batch)
            for batch in chunked(admission_rows):
                conn.execute(admissions.insert(), batch)
            for batch in chunked(test_rows):
                conn.execute(lab_tests.insert(), batch)
            for batch in chunked(results_rows):
                conn.execute(lab_results.insert(), batch)
            print("Database tables created and seeded successfully.")
        else:
            print("Database tables already contain data; skipping data load.")


if __name__ == "__main__":
    main()

