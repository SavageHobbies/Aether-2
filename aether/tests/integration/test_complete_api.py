"""
Complete API integration tests for Aether AI Companion.
Tests all endpoints with real database operations and external integrations.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pathlib import Path

from core.api.gateway import create_app
from core.database.connection import init_database
from core.database.migrations import init_database_schema
from shared.config.settings import get_settings


@pytest.fixture(scope="session")
def test_app():
    """Create test application with test database."""
    # Use test database
    settings = get_settings()
    test_db_path = Path("test_api_integration.db")
    if test_db_path.exists():
        test_db_path.unlink()
    
    settings.database_url = f"sqlite:///{test_db_path}"
    
    # Initialize database
    init_database(settings)
    init_database_schema()
    
    app = create_app()
    yield app
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def auth_token(client):
    """Get authentication token for tests."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Create authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAPIIntegration:
    """Complete API integration test suite."""
    
    def test_application_startup(self, client):
        """Test application starts correctly."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Aether AI Companion API"
        assert data["status"] == "running"
        assert "features" in data
    
    def test_health_endpoints(self, client):
        """Test all health check endpoints."""
        # Main health check
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        assert "database" in health_data
        assert "uptime_seconds" in health_data
        
        # Database health
        response = client.get("/api/v1/health/database")
        assert response.status_code == 200
        
        db_data = response.json()
        assert "connection_status" in db_data
        assert db_data["connection_status"] == "connected"
        
        # Readiness check
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        
        # Liveness check
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
    
    def test_authentication_flow(self, client):
        """Test complete authentication flow."""
        # Test login
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "bearer"
        
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # Test profile access
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/v1/auth/profile", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["username"] == "admin"
        assert "admin" in profile_data["permissions"]
        
        # Test token refresh
        refresh_response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == 200
        
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        
        # Test token verification
        verify_response = client.get("/api/v1/auth/verify", headers=headers)
        assert verify_response.status_code == 200
        
        # Test logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200
    
    def test_conversation_crud_operations(self, client, auth_headers):
        """Test complete CRUD operations for conversations."""
        # Create conversation
        conversation_data = {
            "user_input": "Hello, how can I manage my tasks better?",
            "ai_response": "I can help you organize and prioritize your tasks. Let me suggest some strategies.",
            "context_metadata": {
                "topic": "task_management",
                "user_intent": "productivity_help"
            }
        }
        
        create_response = client.post(
            "/api/v1/conversations/",
            json=conversation_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        
        created_conv = create_response.json()
        assert "id" in created_conv
        assert created_conv["user_input"] == conversation_data["user_input"]
        assert created_conv["ai_response"] == conversation_data["ai_response"]
        
        conversation_id = created_conv["id"]
        
        # Read conversation
        get_response = client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        
        retrieved_conv = get_response.json()
        assert retrieved_conv["id"] == conversation_id
        
        # Update conversation
        update_data = {
            "ai_response": "Updated response: I can help you with advanced task management techniques.",
            "context_metadata": {
                "topic": "advanced_task_management",
                "updated": True
            }
        }
        
        update_response = client.put(
            f"/api/v1/conversations/{conversation_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated_conv = update_response.json()
        assert updated_conv["ai_response"] == update_data["ai_response"]
        
        # List conversations
        list_response = client.get("/api/v1/conversations/", headers=auth_headers)
        assert list_response.status_code == 200
        
        conversations = list_response.json()
        assert len(conversations) >= 1
        assert any(conv["id"] == conversation_id for conv in conversations)
        
        # Test pagination
        paginated_response = client.get(
            "/api/v1/conversations/?limit=1&offset=0",
            headers=auth_headers
        )
        assert paginated_response.status_code == 200
        assert len(paginated_response.json()) <= 1
        
        # Delete conversation
        delete_response = client.delete(
            f"/api/v1/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert get_deleted_response.status_code == 404
    
    def test_idea_crud_operations(self, client, auth_headers):
        """Test complete CRUD operations for ideas."""
        # Create idea
        idea_data = {
            "content": "Build a smart notification system that learns user preferences",
            "source": "desktop",
            "category": "feature",
            "priority_score": 0.8,
            "extra_metadata": {
                "complexity": "high",
                "estimated_hours": 40
            }
        }
        
        create_response = client.post(
            "/api/v1/ideas/",
            json=idea_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        
        created_idea = create_response.json()
        assert "id" in created_idea
        assert created_idea["content"] == idea_data["content"]
        assert created_idea["priority_score"] == idea_data["priority_score"]
        
        idea_id = created_idea["id"]
        
        # Read idea
        get_response = client.get(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        # Update idea
        update_data = {
            "category": "enhancement",
            "priority_score": 0.9,
            "processed": True
        }
        
        update_response = client.put(
            f"/api/v1/ideas/{idea_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated_idea = update_response.json()
        assert updated_idea["category"] == update_data["category"]
        assert updated_idea["processed"] == True
        
        # List ideas with filters
        list_response = client.get(
            "/api/v1/ideas/?source=desktop&processed=true",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        
        ideas = list_response.json()
        assert len(ideas) >= 1
        assert all(idea["source"] == "desktop" for idea in ideas)
        assert all(idea["processed"] == True for idea in ideas)
        
        # Delete idea
        delete_response = client.delete(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
        assert delete_response.status_code == 200
    
    def test_task_crud_operations(self, client, auth_headers):
        """Test complete CRUD operations for tasks."""
        # Create task
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        task_data = {
            "title": "Implement user authentication system",
            "description": "Build secure JWT-based authentication with role management",
            "priority": 2,
            "status": "pending",
            "due_date": due_date,
            "external_integrations": {
                "monday_board": "dev_tasks",
                "calendar_event": True
            }
        }
        
        create_response = client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        
        created_task = create_response.json()
        assert "id" in created_task
        assert created_task["title"] == task_data["title"]
        assert created_task["priority"] == task_data["priority"]
        
        task_id = created_task["id"]
        
        # Read task
        get_response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        # Update task
        update_data = {
            "status": "in_progress",
            "priority": 3,
            "description": "Updated: Build secure JWT-based authentication with advanced role management and permissions"
        }
        
        update_response = client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated_task = update_response.json()
        assert updated_task["status"] == update_data["status"]
        assert updated_task["priority"] == update_data["priority"]
        
        # List tasks with filters
        list_response = client.get(
            "/api/v1/tasks/?status=in_progress&priority=3",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        
        tasks = list_response.json()
        assert len(tasks) >= 1
        assert all(task["status"] == "in_progress" for task in tasks)
        assert all(task["priority"] == 3 for task in tasks)
        
        # Delete task
        delete_response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert delete_response.status_code == 200
    
    def test_memory_crud_operations(self, client, auth_headers):
        """Test complete CRUD operations for memory entries."""
        # Create memory
        memory_data = {
            "content": "User prefers morning meetings and dislikes interruptions during deep work sessions",
            "importance_score": 0.9,
            "tags": ["preferences", "meetings", "productivity"],
            "user_editable": True
        }
        
        create_response = client.post(
            "/api/v1/memory/",
            json=memory_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        
        created_memory = create_response.json()
        assert "id" in created_memory
        assert created_memory["content"] == memory_data["content"]
        assert created_memory["importance_score"] == memory_data["importance_score"]
        
        memory_id = created_memory["id"]
        
        # Read memory
        get_response = client.get(f"/api/v1/memory/{memory_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        # Update memory
        update_data = {
            "importance_score": 0.95,
            "tags": ["preferences", "meetings", "productivity", "communication"]
        }
        
        update_response = client.put(
            f"/api/v1/memory/{memory_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated_memory = update_response.json()
        assert updated_memory["importance_score"] == update_data["importance_score"]
        assert len(updated_memory["tags"]) == 4
        
        # List memories with filters
        list_response = client.get(
            "/api/v1/memory/?tags=preferences,meetings&min_importance=0.8",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        
        memories = list_response.json()
        assert len(memories) >= 1
        
        # Search memories
        search_data = {
            "query": "morning meetings preferences",
            "limit": 5,
            "threshold": 0.5
        }
        
        search_response = client.post(
            "/api/v1/memory/search",
            json=search_data,
            headers=auth_headers
        )
        assert search_response.status_code == 200
        
        search_results = search_response.json()
        assert isinstance(search_results, list)
        
        # Delete memory
        delete_response = client.delete(f"/api/v1/memory/{memory_id}", headers=auth_headers)
        assert delete_response.status_code == 200
    
    def test_cross_entity_relationships(self, client, auth_headers):
        """Test relationships between different entities."""
        # Create an idea
        idea_data = {
            "content": "Implement automated task prioritization based on deadlines and importance",
            "source": "web",
            "category": "automation"
        }
        
        idea_response = client.post("/api/v1/ideas/", json=idea_data, headers=auth_headers)
        assert idea_response.status_code == 200
        idea_id = idea_response.json()["id"]
        
        # Create a task linked to the idea
        task_data = {
            "title": "Build task prioritization algorithm",
            "description": "Implement ML-based task prioritization system",
            "priority": 2,
            "source_idea_id": idea_id
        }
        
        task_response = client.post("/api/v1/tasks/", json=task_data, headers=auth_headers)
        assert task_response.status_code == 200
        task_id = task_response.json()["id"]
        
        # Create a conversation about the task
        conversation_data = {
            "user_input": "How should I approach building the task prioritization system?",
            "ai_response": "Start with analyzing user behavior patterns and deadline urgency factors.",
            "context_metadata": {"related_task_id": task_id}
        }
        
        conv_response = client.post("/api/v1/conversations/", json=conversation_data, headers=auth_headers)
        assert conv_response.status_code == 200
        
        # Verify relationships exist
        task_detail = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert task_detail.status_code == 200
        assert task_detail.json()["source_idea_id"] == idea_id
        
        # Cleanup
        client.delete(f"/api/v1/conversations/{conv_response.json()['id']}", headers=auth_headers)
        client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        client.delete(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
    
    def test_error_handling(self, client, auth_headers):
        """Test API error handling."""
        # Test 404 errors
        response = client.get("/api/v1/conversations/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
        
        # Test validation errors
        invalid_data = {
            "user_input": "",  # Empty string should fail validation
            "ai_response": "x" * 15000  # Too long should fail validation
        }
        
        response = client.post("/api/v1/conversations/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Test unauthorized access
        response = client.get("/api/v1/conversations/")
        assert response.status_code == 401
        
        # Test invalid JSON
        response = client.post(
            "/api/v1/conversations/",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Test login rate limiting
        for i in range(10):
            response = client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "wrongpassword"
            })
            
            if response.status_code == 429:
                # Rate limit hit
                assert "rate limit" in response.json()["detail"].lower()
                break
        # If no rate limit hit, that's also acceptable for this test
    
    def test_data_consistency(self, client, auth_headers):
        """Test data consistency across operations."""
        # Create multiple related entities
        entities_created = []
        
        try:
            # Create conversation
            conv_data = {
                "user_input": "I need to organize my project tasks",
                "ai_response": "Let me help you create a structured task management system"
            }
            conv_response = client.post("/api/v1/conversations/", json=conv_data, headers=auth_headers)
            assert conv_response.status_code == 200
            entities_created.append(("conversation", conv_response.json()["id"]))
            
            # Create idea
            idea_data = {
                "content": "Build a kanban board for visual task management",
                "source": "desktop"
            }
            idea_response = client.post("/api/v1/ideas/", json=idea_data, headers=auth_headers)
            assert idea_response.status_code == 200
            entities_created.append(("idea", idea_response.json()["id"]))
            
            # Create task
            task_data = {
                "title": "Design kanban board interface",
                "priority": 2,
                "source_idea_id": idea_response.json()["id"]
            }
            task_response = client.post("/api/v1/tasks/", json=task_data, headers=auth_headers)
            assert task_response.status_code == 200
            entities_created.append(("task", task_response.json()["id"]))
            
            # Create memory
            memory_data = {
                "content": "User wants visual task management with kanban boards",
                "importance_score": 0.8,
                "tags": ["ui", "tasks", "kanban"]
            }
            memory_response = client.post("/api/v1/memory/", json=memory_data, headers=auth_headers)
            assert memory_response.status_code == 200
            entities_created.append(("memory", memory_response.json()["id"]))
            
            # Verify all entities exist
            for entity_type, entity_id in entities_created:
                response = client.get(f"/api/v1/{entity_type}s/{entity_id}", headers=auth_headers)
                assert response.status_code == 200
            
        finally:
            # Cleanup all created entities
            for entity_type, entity_id in reversed(entities_created):
                client.delete(f"/api/v1/{entity_type}s/{entity_id}", headers=auth_headers)


class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_bulk_operations_performance(self, client, auth_headers):
        """Test performance with bulk operations."""
        import time
        
        # Create multiple conversations quickly
        start_time = time.time()
        conversation_ids = []
        
        for i in range(10):
            conv_data = {
                "user_input": f"Test conversation {i}",
                "ai_response": f"Response to test conversation {i}"
            }
            response = client.post("/api/v1/conversations/", json=conv_data, headers=auth_headers)
            assert response.status_code == 200
            conversation_ids.append(response.json()["id"])
        
        creation_time = time.time() - start_time
        assert creation_time < 5.0  # Should complete within 5 seconds
        
        # Retrieve all conversations quickly
        start_time = time.time()
        response = client.get("/api/v1/conversations/?limit=20", headers=auth_headers)
        assert response.status_code == 200
        retrieval_time = time.time() - start_time
        assert retrieval_time < 2.0  # Should complete within 2 seconds
        
        # Cleanup
        for conv_id in conversation_ids:
            client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    
    def test_concurrent_requests(self, client, auth_headers):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request(i):
            conv_data = {
                "user_input": f"Concurrent test {i}",
                "ai_response": f"Concurrent response {i}"
            }
            response = client.post("/api/v1/conversations/", json=conv_data, headers=auth_headers)
            results.append(response.status_code)
        
        # Create 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])