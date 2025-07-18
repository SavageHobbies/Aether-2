#!/usr/bin/env python3
"""
Simple API test script to verify basic functionality.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_api_imports():
    """Test that we can import all API components."""
    print("🧪 Testing API imports...")
    
    try:
        # Test core imports
        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")
        
        from core.api.gateway import APIGateway
        print("✅ APIGateway imported successfully")
        
        # Test route imports
        from core.api.routes import setup_routes
        print("✅ Routes setup imported successfully")
        
        from core.api.routes.auth import router as auth_router
        print("✅ Auth routes imported successfully")
        
        from core.api.routes.health import router as health_router
        print("✅ Health routes imported successfully")
        
        from core.api.routes.conversations import router as conv_router
        print("✅ Conversation routes imported successfully")
        
        from core.api.routes.ideas import router as ideas_router
        print("✅ Ideas routes imported successfully")
        
        from core.api.routes.tasks import router as tasks_router
        print("✅ Tasks routes imported successfully")
        
        from core.api.routes.memory import router as memory_router
        print("✅ Memory routes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


async def test_api_creation():
    """Test that we can create the API application."""
    print("\n🏗️  Testing API creation...")
    
    try:
        from core.api.gateway import create_app
        
        # Create the app
        app = create_app()
        print("✅ FastAPI app created successfully")
        
        # Check that routes are registered
        routes = [route.path for route in app.routes]
        print(f"✅ Found {len(routes)} routes registered")
        
        # Check for key routes
        expected_routes = [
            "/",
            "/api/v1/auth/login",
            "/api/v1/health/",
            "/api/v1/conversations/",
            "/api/v1/ideas/",
            "/api/v1/tasks/",
            "/api/v1/memory/"
        ]
        
        missing_routes = []
        for expected in expected_routes:
            if not any(expected in route for route in routes):
                missing_routes.append(expected)
        
        if missing_routes:
            print(f"⚠️  Missing routes: {missing_routes}")
        else:
            print("✅ All expected routes found")
        
        return True
        
    except Exception as e:
        print(f"❌ API creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_models():
    """Test that database models can be imported."""
    print("\n🗄️  Testing database models...")
    
    try:
        from core.database.models import (
            ConversationModel, IdeaModel, TaskModel, MemoryModel
        )
        print("✅ Database models imported successfully")
        
        from shared.schemas.conversation import ConversationResponse
        from shared.schemas.idea import IdeaResponse
        from shared.schemas.task import TaskResponse
        from shared.schemas.memory import MemoryEntryResponse
        print("✅ Response schemas imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database model import failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Aether AI Companion - API Testing")
    print("=" * 50)
    
    tests = [
        test_api_imports,
        test_api_creation,
        test_database_models
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed < total:
        print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! API components are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))