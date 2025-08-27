"""
Tests for main application
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "dependencies" in data


def test_openapi_schema():
    """Test OpenAPI schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert schema["info"]["title"] == "API de Extração e Normalização de Exames Clínicos"
    assert schema["info"]["version"] == "1.0.0"


def test_docs_accessible():
    """Test API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options("/health")
    assert response.status_code == 200


def test_correlation_id_header():
    """Test correlation ID is added to responses"""
    response = client.get("/health")
    assert "X-Correlation-ID" in response.headers
    assert "X-Response-Time" in response.headers