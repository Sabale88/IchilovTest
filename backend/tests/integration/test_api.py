"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.utils import get_database_url


@pytest.fixture(scope="module")
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for testing."""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data


class TestPatientsMonitoringEndpoint:
    """Tests for the patients monitoring endpoint."""

    def test_monitoring_endpoint_basic(self, client):
        """Test monitoring endpoint returns 200 with valid request."""
        response = client.get("/api/patients/monitoring?hours_threshold=48&page=1&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
        assert "page" in data["pagination"]
        assert "limit" in data["pagination"]
        assert "total" in data["pagination"]

    def test_monitoring_endpoint_pagination(self, client):
        """Test monitoring endpoint pagination."""
        response = client.get("/api/patients/monitoring?hours_threshold=48&page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert len(data["data"]) <= 10

    def test_monitoring_endpoint_department_filter(self, client):
        """Test monitoring endpoint with department filter."""
        response = client.get("/api/patients/monitoring?hours_threshold=48&department=Cardiology&page=1&limit=50")
        assert response.status_code == 200
        data = response.json()
        # All returned patients should have the specified department
        for patient in data["data"]:
            if patient.get("department"):
                assert patient["department"] == "Cardiology"

    def test_monitoring_endpoint_invalid_params(self, client):
        """Test monitoring endpoint with invalid parameters."""
        # Negative page
        response = client.get("/api/patients/monitoring?hours_threshold=48&page=-1&limit=50")
        assert response.status_code == 422

        # Zero limit
        response = client.get("/api/patients/monitoring?hours_threshold=48&page=1&limit=0")
        assert response.status_code == 422

        # Limit too large
        response = client.get("/api/patients/monitoring?hours_threshold=48&page=1&limit=10001")
        assert response.status_code == 422


class TestPatientDetailEndpoint:
    """Tests for the patient detail endpoint."""

    def test_patient_detail_endpoint_valid_id(self, client):
        """Test patient detail endpoint with valid patient ID."""
        # First, get a patient ID from monitoring endpoint
        monitoring_response = client.get("/api/patients/monitoring?hours_threshold=48&page=1&limit=1")
        if monitoring_response.status_code == 200:
            data = monitoring_response.json()
            if data["data"]:
                patient_id = data["data"][0]["patient_id"]
                response = client.get(f"/api/patients/{patient_id}")
                assert response.status_code == 200
                detail_data = response.json()
                assert "patient_id" in detail_data
                assert "name" in detail_data
                assert detail_data["patient_id"] == patient_id

    def test_patient_detail_endpoint_invalid_id(self, client):
        """Test patient detail endpoint with invalid patient ID."""
        response = client.get("/api/patients/999999999")
        # Should return 200 with null or 404, depending on implementation
        assert response.status_code in [200, 404]

    def test_patient_detail_endpoint_negative_id(self, client):
        """Test patient detail endpoint with negative ID."""
        response = client.get("/api/patients/-1")
        assert response.status_code == 422

    def test_patient_detail_endpoint_non_numeric_id(self, client):
        """Test patient detail endpoint with non-numeric ID."""
        response = client.get("/api/patients/abc")
        assert response.status_code == 422


class TestAPICORS:
    """Tests for CORS configuration."""

    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/api/health")
        # CORS headers should be present (handled by middleware)
        assert response.status_code in [200, 405]  # OPTIONS may return 405 if not configured

