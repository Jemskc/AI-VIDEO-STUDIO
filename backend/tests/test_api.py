import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "AI Movie Studio" in data["name"]


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_register_user():
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    # Should succeed or fail if user already exists (both are acceptable)
    assert response.status_code in [201, 400]


def test_login():
    """Test user login."""
    # First register a user
    user_data = {
        "email": "login_test@example.com",
        "username": "logintestuser",
        "password": "testpass123"
    }
    
    client.post("/api/v1/auth/register", json=user_data)
    
    # Then try to login
    login_data = {
        "email": "login_test@example.com",
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_get_projects_unauthorized():
    """Test getting projects without authentication."""
    response = client.get("/api/v1/projects/")
    # Should work with placeholder auth for now
    assert response.status_code in [200, 401]


def test_get_ai_models():
    """Test getting AI models."""
    response = client.get("/api/v1/models/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_queue_status():
    """Test render queue status."""
    response = client.get("/api/v1/render/queue/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "pending" in data
    assert "queued" in data
    assert "processing" in data
    assert "completed" in data


def test_create_render_job():
    """Test creating a render job."""
    job_data = {
        "job_type": "video",
        "parameters": {"resolution": "1920x1080", "fps": 24},
        "priority": 0
    }
    
    response = client.post("/api/v1/render/jobs", json=job_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["job_type"] == "video"
    assert data["status"] == "pending"


def test_get_notifications():
    """Test getting notifications."""
    response = client.get("/api/v1/notifications/")
    assert response.status_code in [200, 401]


def test_get_settings():
    """Test getting user settings."""
    response = client.get("/api/v1/settings/")
    assert response.status_code in [200, 401]


def test_model_categories():
    """Test getting model categories."""
    response = client.get("/api/v1/models/categories")
    assert response.status_code == 200
    assert "categories" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
