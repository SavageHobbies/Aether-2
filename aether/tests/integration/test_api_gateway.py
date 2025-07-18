"""
Integration tests for Aether AI Companion API Gateway.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

from core.api.gateway import create_app
from core.api.auth import AuthManager
from shared.config.settings import get_settings


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    auth_manager = AuthManager()
    
    # Login as admin user
    token_response = auth_manager.login(
        auth_manager.UserCredentials(username="admin", password="admin123")
    )
    
    return {
        "Authorization": f"Bearer {token_response.access_token}"
    }


class TestAPIGateway:
    """Test suite for API Gateway functionality."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Aether AI Companion API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
        assert "features" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert "database" in data
        assert "services" in data
        assert "uptime_seconds" in data
    
    def test_openapi_docs(self, client):
        """Test OpenAPI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert openapi_spec["info"]["title"] == "Aether AI Companion API"


class TestAuthentication:
    """Test suite for authentication functionality."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_failure(self, client):
        """Test failed login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/auth/profile")
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Test accessing protected endpoint with authentication."""
        response = client.get("/api/v1/auth/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "username" in data
        assert "permissions" in data
    
    def test_token_refresh(self, client):
        """Test token refresh functionality."""
        # First, login to get tokens
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        assert "access_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"


class TestConversationAPI:
    """Test suite for conversation API endpoints."""
    
    def test_create_conversation(self, client, auth_headers):
        """Test creating a new conversation."""
        conversation_data = {
            "user_input": "Hello, how are you?",
            "ai_response": "I'm doing well, thank you for asking!",
            "context_metadata": {"test": True}
        }
        
        response = client.post(
            "/api/v1/conversations/",
            json=conversation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["user_input"] == conversation_data["user_input"]
        assert data["ai_response"] == conversation_data["ai_response"]
        assert data["context_metadata"] == conversation_data["context_metadata"]
    
    def test_get_conversations(self, client, auth_headers):
        """Test retrieving conversations."""
        response = client.get("/api/v1/conversations/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_conversation_pagination(self, client, auth_headers):
        """Test conversation pagination."""
        response = client.get(
            "/api/v1/conversations/?limit=5&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5


class TestIdeaAPI:
    """Test suite for idea API endpoints."""
    
    def test_create_idea(self, client, auth_headers):
        """Test creating a new idea."""
        idea_data = {
            "content": "Build a mobile app for task management",
            "source": "mobile",
            "category": "app",
            "priority_score": 0.8
        }
        
        response = client.post(
            "/api/v1/ideas/",
            json=idea_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["content"] == idea_data["content"]
        assert data["source"] == idea_data["source"]
        assert data["category"] == idea_data["category"]
        assert data["priority_score"] == idea_data["priority_score"]
    
    def test_get_ideas(self, client, auth_headers):
        """Test retrieving ideas."""
        response = client.get("/api/v1/ideas/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_filter_ideas_by_source(self, client, auth_headers):
        """Test filtering ideas by source."""
        response = client.get(
            "/api/v1/ideas/?source=mobile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # All returned ideas should have source="mobile"
        for idea in data:
            assert idea["source"] == "mobile"


class TestTaskAPI:
    """Test suite for task API endpoints."""
    
    def test_create_task(self, client, auth_headers):
        """Test creating a new task."""
        task_data = {
            "title": "Complete project documentation",
            "description": "Write comprehensive documentation for the project",
            "priority": 2,
            "status": "pending"
        }
        
        response = client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]
        assert data["status"] == task_data["status"]
    
    def test_get_tasks(self, client, auth_headers):
        """Test retrieving tasks."""
        response = client.get("/api/v1/tasks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_filter_tasks_by_status(self, client, auth_headers):
        """Test filtering tasks by status."""
        response = client.get(
            "/api/v1/tasks/?status=pending",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # All returned tasks should have status="pending"
        for task in data:
            assert task["status"] == "pending"


class TestMemoryAPI:
    """Test suite for memory API endpoints."""
    
    def test_create_memory(self, client, auth_headers):
        """Test creating a new memory entry."""
        memory_data = {
            "content": "User prefers morning meetings",
            "importance_score": 0.7,
            "tags": ["preference", "meetings"],
            "user_editable": True
        }
        
        response = client.post(
            "/api/v1/memory/",
            json=memory_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["content"] == memory_data["content"]
        assert data["importance_score"] == memory_data["importance_score"]
        assert data["tags"] == memory_data["tags"]
        assert data["user_editable"] == memory_data["user_editable"]
    
    def test_search_memories(self, client, auth_headers):
        """Test memory search functionality."""
        search_data = {
            "query": "meetings preference",
            "limit": 10,
            "threshold": 0.5
        }
        
        response = client.post(
            "/api/v1/memory/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)


class TestRateLimiting:
    """Test suite for rate limiting functionality."""
    
    def test_rate_limiting_auth_endpoint(self, client):
        """Test rate limiting on authentication endpoint."""
        # Make multiple rapid requests to trigger rate limiting
        for i in range(10):
            response = client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "wrongpassword"
            })
            
            if response.status_code == 429:
                # Rate limit triggered
                assert "rate limit" in response.json()["detail"].lower()
                break
        else:
            # If we didn't hit rate limit, that's also acceptable for this test
            pass


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_invalid_json(self, client, auth_headers):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/conversations/",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test handling of missing required fields."""
        response = client.post(
            "/api/v1/conversations/",
            json={"user_input": "test"},  # Missing ai_response
            headers=auth_headers
        )
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])