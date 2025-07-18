#!/usr/bin/env python3
"""
Basic API test to verify core functionality without complex dependencies.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_database_models():
    """Test that database models can be imported."""
    print("🗄️  Testing database models...")
    
    try:
        from core.database.models import (
            Conversation, MemoryEntry, Idea, Task
        )
        print("✅ Database models imported successfully")
        print(f"   - Conversation: {Conversation.__tablename__}")
        print(f"   - MemoryEntry: {MemoryEntry.__tablename__}")
        print(f"   - Idea: {Idea.__tablename__}")
        print(f"   - Task: {Task.__tablename__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database model import failed: {e}")
        return False


def test_basic_imports():
    """Test basic imports without FastAPI."""
    print("🧪 Testing basic imports...")
    
    try:
        # Test SQLAlchemy
        from sqlalchemy import create_engine
        print("✅ SQLAlchemy imported successfully")
        
        # Test database connection utilities
        from core.database.connection import DatabaseManager
        print("✅ Database connection utilities imported")
        
        # Test schemas
        from shared.schemas.base import BaseSchema
        print("✅ Base schemas imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False


def test_serialization():
    """Test serialization utilities."""
    print("📦 Testing serialization...")
    
    try:
        from shared.serialization import ModelSerializer
        print("✅ ModelSerializer imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization test failed: {e}")
        return False


def test_database_setup():
    """Test database setup without actually connecting."""
    print("🔧 Testing database setup...")
    
    try:
        from core.database.connection import DatabaseManager
        from shared.config.settings import get_settings
        
        # Get settings
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.name}")
        
        # Create database manager (without connecting)
        db_manager = DatabaseManager(database_url="sqlite:///test.db")
        print("✅ Database manager created")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Aether AI Companion - Basic API Testing")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_database_models,
        test_serialization,
        test_database_setup
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
            print()
    
    print("=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed < total:
        print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All basic tests passed! Core components are working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())