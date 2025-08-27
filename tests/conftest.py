"""
Test configuration and fixtures
"""

import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db.database import get_db, Base
from src.core.config import settings

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Provide a clean database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Provide a test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["S3_BUCKET_NAME"] = "test-bucket"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["OAUTH2_TOKEN_URL"] = "https://test.auth.com/token"
    os.environ["OAUTH2_AUDIENCE"] = "test-audience"
    os.environ["OAUTH2_ISSUER"] = "https://test.auth.com"