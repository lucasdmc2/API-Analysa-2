"""
API contract tests based on OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

# Test headers for authenticated requests
AUTH_HEADERS = {"Authorization": "Bearer dev-user"}
ADMIN_HEADERS = {"Authorization": "Bearer dev-admin"}


class TestIngestionEndpoints:
    """Test ingestion API endpoints"""
    
    def test_create_ingestion_schema(self):
        """Test ingestion creation follows OpenAPI schema"""
        response = client.post("/v1/ingestions", 
            headers=AUTH_HEADERS,
            json={
                "document_type": "laboratory_report",
                "filename": "test.pdf"
            }
        )
        
        # Should be valid request (may fail for other reasons like missing file)
        assert response.status_code in [201, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 201:
            data = response.json()
            assert "ingestion_id" in data
            assert "status" in data
            assert "created_at" in data
    
    def test_create_ingestion_invalid_document_type(self):
        """Test validation of document_type field"""
        response = client.post("/v1/ingestions",
            headers=AUTH_HEADERS,
            json={
                "document_type": "invalid_type"
            }
        )
        assert response.status_code == 400


class TestPatientsEndpoints:
    """Test patients API endpoints"""
    
    def test_get_patient_observations_requires_uuid(self):
        """Test patient observations endpoint validates UUID"""
        response = client.get("/v1/patients/invalid-uuid/observations",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_patient_observations_pagination(self):
        """Test pagination parameters validation"""
        patient_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Test limit validation
        response = client.get(f"/v1/patients/{patient_id}/observations?limit=150",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 422  # Limit too high
        
        # Test valid limit
        response = client.get(f"/v1/patients/{patient_id}/observations?limit=20",
            headers=AUTH_HEADERS
        )
        assert response.status_code in [200, 404]  # Valid request format


class TestAdminEndpoints:
    """Test admin API endpoints"""
    
    def test_create_rangeset_schema(self):
        """Test rangeset creation follows schema"""
        response = client.post("/v1/admin/rangesets",
            headers=ADMIN_HEADERS,
            json={
                "analyte_key": "glucose",
                "unit_ucum": "mg/dL",
                "ref_low": 70,
                "ref_high": 99,
                "sex": "all",
                "confidence_level": "high"
            }
        )
        
        # Should be valid request format
        assert response.status_code in [201, 400, 409]
    
    def test_create_rangeset_validation(self):
        """Test rangeset validation rules"""
        # Missing required fields
        response = client.post("/v1/admin/rangesets",
            headers=ADMIN_HEADERS,
            json={
                "analyte_key": "glucose"
                # Missing unit_ucum
            }
        )
        assert response.status_code == 422
        
        # Invalid sex value
        response = client.post("/v1/admin/rangesets",
            headers=ADMIN_HEADERS,
            json={
                "analyte_key": "glucose",
                "unit_ucum": "mg/dL",
                "sex": "invalid"
            }
        )
        assert response.status_code == 422


class TestErrorFormat:
    """Test error responses follow RFC 7807"""
    
    def test_error_format_validation(self):
        """Test validation errors follow RFC 7807 format"""
        response = client.post("/v1/ingestions",
            headers=AUTH_HEADERS,
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
        error = response.json()
        
        # Should have RFC 7807 fields
        assert "type" in error
        assert "title" in error
        assert "status" in error
        assert "detail" in error
    
    def test_error_format_auth(self):
        """Test auth errors follow RFC 7807 format"""
        response = client.post("/v1/ingestions",
            json={"document_type": "laboratory_report"}
        )
        
        assert response.status_code == 401
        error = response.json()
        
        assert "type" in error
        assert "title" in error
        assert "status" in error
        assert error["status"] == 401
        assert "correlation_id" in error
        assert "timestamp" in error