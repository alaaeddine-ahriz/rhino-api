"""Pytest configuration and shared fixtures for API tests."""
import pytest
import os
import shutil
import tempfile
import time
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(scope="function")
def clean_database():
    """Clean the test database before each test."""    
    # Import here to avoid circular imports
    from app.db import session
    from sqlmodel import create_engine, SQLModel
    
    # Dispose of any existing engine connections
    try:
        session.engine.dispose()
    except:
        pass
    
    # Give SQLite time to release any locks
    time.sleep(0.2)
    
    # Remove test database if it exists
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except (OSError, PermissionError):
            # If can't remove, try to unlock and remove after delay
            time.sleep(1.0)
            try:
                os.remove("test.db")
            except:
                pass
    
    # Create a fresh engine for this test
    session.engine = create_engine(
        "sqlite:///./test.db",
        echo=True,
        poolclass=None,  # Disable connection pooling
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
            "isolation_level": "IMMEDIATE"
        }
    )
    
    # Create all tables in the fresh database
    import app.db.models  # Import models to ensure they're registered
    SQLModel.metadata.create_all(session.engine)
    
    yield
    
    # Clean up after test
    try:
        session.engine.dispose()
    except:
        pass
    
    # Force cleanup after test with proper delay
    time.sleep(0.2)
    try:
        if os.path.exists("test.db"):
            os.remove("test.db")
    except:
        pass


@pytest.fixture(scope="function")
def test_users(clean_database, test_client):
    """Create test users for different roles."""
    # Ensure clean_database fixture runs first
    users = {}
    
    # Create student user
    response = test_client.post("/api/users/register", json={
        "username": "test_student",
        "email": "test_student@example.com",
        "role": "student",
        "subscriptions": ["SYD", "TCP"]
    })
    if response.status_code == 200:
        users["student"] = {
            "id": response.json()["data"]["user_id"],
            "username": "test_student",
            "role": "student"
        }
    
    # Create teacher user
    response = test_client.post("/api/users/register", json={
        "username": "test_teacher",
        "email": "test_teacher@example.com",
        "role": "teacher",
        "subscriptions": ["SYD", "TCP"]
    })
    if response.status_code == 200:
        users["teacher"] = {
            "id": response.json()["data"]["user_id"],
            "username": "test_teacher",
            "role": "teacher"
        }
    
    # Create admin user
    response = test_client.post("/api/users/register", json={
        "username": "test_admin",
        "email": "test_admin@example.com",
        "role": "admin",
        "subscriptions": []
    })
    if response.status_code == 200:
        users["admin"] = {
            "id": response.json()["data"]["user_id"],
            "username": "test_admin",
            "role": "admin"
        }
    
    return users


@pytest.fixture(scope="function") 
def sample_challenge_data():
    """Provide sample challenge data for tests."""
    return {
        "ref": "TEST-CHALLENGE-001",
        "question": "Explain the difference between TCP and UDP protocols.",
        "matiere": "SYD",
        "date": "2024-06-10",
        "type": "knowledge"
    }


@pytest.fixture(scope="function")
def sample_document_content():
    """Provide sample document content for testing."""
    return b"This is a test document content for testing purposes. It contains sample information about networking concepts."


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "auth: marks tests for authentication functionality"
    )
    config.addinivalue_line(
        "markers", "documents: marks tests for document management"
    )
    config.addinivalue_line(
        "markers", "challenges: marks tests for challenges functionality"
    )
    config.addinivalue_line(
        "markers", "permissions: marks tests for permission/role checking"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests that require full system integration"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that are slow running"
    ) 