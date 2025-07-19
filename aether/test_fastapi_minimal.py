#!/usr/bin/env python3
"""
Minimal FastAPI test to isolate the Pydantic compatibility issue.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports without any project code."""
    try:
        print("Testing basic imports...")
        
        # Test pydantic first
        import pydantic
        print(f"✅ Pydantic {pydantic.VERSION} imported successfully")
        
        # Test pydantic BaseModel
        from pydantic import BaseModel
        print("✅ Pydantic BaseModel imported successfully")
        
        # Test basic model creation
        class TestModel(BaseModel):
            name: str
            value: int = 42
        
        test_instance = TestModel(name="test")
        print(f"✅ Pydantic model created: {test_instance}")
        
        # Test FastAPI import
        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")
        
        # Test FastAPI app creation
        app = FastAPI()
        print("✅ FastAPI app created successfully")
        
        # Test route creation
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        print("✅ FastAPI route created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during basic imports: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_project_imports():
    """Test imports with project code."""
    try:
        print("\nTesting with project imports...")
        
        # Test shared imports
        from shared.config import get_settings
        print("✅ Shared config imported successfully")
        
        # Test database imports
        from core.database.connection import get_database
        print("✅ Database connection imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during project imports: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 FastAPI Compatibility Test")
    print("=" * 50)
    
    # Test basic imports first
    basic_success = test_basic_imports()
    
    if basic_success:
        print("\n🎉 Basic FastAPI/Pydantic compatibility: SUCCESS")
        
        # Test with project imports
        project_success = test_with_project_imports()
        
        if project_success:
            print("🎉 Project imports: SUCCESS")
            print("\n✅ ALL TESTS PASSED - FastAPI compatibility issue is FIXED!")
        else:
            print("❌ Project imports failed - issue is in project code")
    else:
        print("\n❌ Basic FastAPI/Pydantic compatibility failed")
        print("This indicates a fundamental environment issue")