"""
Tests for authentication and authorization
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_protected_endpoint_without_token():
    """Test protected endpoint returns 401 without token"""
    response = client.post("/v1/ingestions", json={
        "document_type": "laboratory_report"
    })
    assert response.status_code == 401
    
    error = response.json()
    assert error["type"].endswith("token-missing")
    assert error["title"] == "Token de acesso ausente"


def test_protected_endpoint_with_invalid_token():
    """Test protected endpoint returns 401 with invalid token"""
    response = client.post("/v1/ingestions", 
        headers={"Authorization": "Bearer invalid-token"},
        json={"document_type": "laboratory_report"}
    )
    assert response.status_code == 401
    
    error = response.json()
    assert error["type"].endswith("token-invalid")


def test_protected_endpoint_with_valid_token():
    """Test protected endpoint works with valid dev token"""
    response = client.post("/v1/ingestions",
        headers={"Authorization": "Bearer dev-user"},
        json={"document_type": "laboratory_report"}
    )
    # Should not be 401 (auth works), may be 400 for other validation
    assert response.status_code != 401


def test_admin_endpoint_requires_admin_scope():
    """Test admin endpoint requires admin scope"""
    # Try with regular user token
    response = client.post("/v1/admin/rangesets",
        headers={"Authorization": "Bearer dev-user"},
        json={
            "analyte_key": "test",
            "unit_ucum": "mg/dL",
            "ref_low": 10,
            "ref_high": 20
        }
    )
    assert response.status_code == 403
    
    error = response.json()
    assert error["type"].endswith("insufficient-scope")


def test_admin_endpoint_with_admin_token():
    """Test admin endpoint works with admin token"""
    response = client.post("/v1/admin/rangesets",
        headers={"Authorization": "Bearer dev-admin"},
        json={
            "analyte_key": "test",
            "unit_ucum": "mg/dL",
            "ref_low": 10,
            "ref_high": 20
        }
    )
    # Should not be 403 (auth works), may be other errors
    assert response.status_code != 403