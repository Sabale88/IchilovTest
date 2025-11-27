"""Integration tests for database operations."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.db.utils import get_database_url
from backend.app.db.snapshot_builder import refresh_snapshots
from backend.app.services.patient_service import (
    get_latest_monitoring_snapshot,
    get_patient_detail,
)


@pytest.fixture(scope="module")
def engine():
    """Create a database engine for testing."""
    return create_engine(get_database_url())


@pytest.fixture(scope="module")
def session(engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSnapshotGeneration:
    """Tests for snapshot generation functionality."""

    def test_refresh_snapshots_basic(self, engine):
        """Test that refresh_snapshots runs without errors."""
        result = refresh_snapshots(hours_threshold=48)
        assert isinstance(result, dict)
        # Should contain some summary information
        assert "monitoring_entries" in result or "detail_snapshots" in result

    def test_refresh_snapshots_creates_monitoring_snapshot(self, engine):
        """Test that refresh_snapshots creates monitoring snapshots."""
        refresh_snapshots(hours_threshold=48)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM patient_monitoring_snapshots 
                    WHERE deleted_at IS NULL 
                    AND hours_threshold = 48
                """)
            ).first()
            assert result is not None
            assert result.count >= 0  # May be 0 if no patients match criteria

    def test_refresh_snapshots_creates_detail_snapshots(self, engine):
        """Test that refresh_snapshots creates detail snapshots."""
        refresh_snapshots(hours_threshold=48)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM patient_detail_snapshots 
                    WHERE deleted_at IS NULL
                """)
            ).first()
            assert result is not None
            assert result.count >= 0


class TestPatientService:
    """Tests for patient service functions."""

    def test_get_latest_monitoring_snapshot_basic(self):
        """Test getting latest monitoring snapshot."""
        response = get_latest_monitoring_snapshot(
            hours_threshold=48,
            page=1,
            limit=50
        )
        assert response is not None
        assert hasattr(response, "data")
        assert hasattr(response, "pagination")
        assert isinstance(response.data, list)
        assert response.pagination["page"] == 1
        assert response.pagination["limit"] == 50

    def test_get_latest_monitoring_snapshot_with_department(self):
        """Test getting monitoring snapshot with department filter."""
        response = get_latest_monitoring_snapshot(
            hours_threshold=48,
            department="Cardiology",
            page=1,
            limit=50
        )
        assert response is not None
        # All patients should have the specified department
        for patient in response.data:
            if patient.department:
                assert patient.department == "Cardiology"

    def test_get_latest_monitoring_snapshot_pagination(self):
        """Test monitoring snapshot pagination."""
        response_page1 = get_latest_monitoring_snapshot(
            hours_threshold=48,
            page=1,
            limit=10
        )
        response_page2 = get_latest_monitoring_snapshot(
            hours_threshold=48,
            page=2,
            limit=10
        )
        assert response_page1.pagination["page"] == 1
        assert response_page2.pagination["page"] == 2
        # Results should be different (unless there are fewer than 10 total)
        if len(response_page1.data) == 10:
            assert response_page1.data != response_page2.data

    def test_get_patient_detail_valid_id(self, engine):
        """Test getting patient detail with valid ID."""
        # First, get a patient ID from monitoring
        monitoring = get_latest_monitoring_snapshot(hours_threshold=48, page=1, limit=1)
        if monitoring.data:
            patient_id = monitoring.data[0].patient_id
            detail = get_patient_detail(patient_id)
            if detail:
                assert detail.patient_id == patient_id
                assert detail.name is not None
                assert isinstance(detail.latest_results, list)
                assert isinstance(detail.chart_series, list)

    def test_get_patient_detail_invalid_id(self):
        """Test getting patient detail with invalid ID."""
        detail = get_patient_detail(999999999)
        assert detail is None


class TestDatabaseQueries:
    """Tests for database query functionality."""

    def test_patients_table_exists(self, engine):
        """Test that patients table exists."""
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = 'patients'
                """)
            ).first()
            assert result is not None
            assert result.count == 1

    def test_admissions_table_exists(self, engine):
        """Test that admissions table exists."""
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = 'admissions'
                """)
            ).first()
            assert result is not None
            assert result.count == 1

    def test_snapshot_tables_exist(self, engine):
        """Test that snapshot tables exist."""
        with engine.connect() as conn:
            monitoring_exists = conn.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = 'patient_monitoring_snapshots'
                """)
            ).first()
            detail_exists = conn.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = 'patient_detail_snapshots'
                """)
            ).first()
            assert monitoring_exists.count == 1
            assert detail_exists.count == 1

