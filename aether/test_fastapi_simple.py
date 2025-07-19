#!/usr/bin/env python3
"""
Simple FastAPI test to isolate the Pydantic compatibility issue.
"""

def test_fastapi_basic():
    """Test basic FastAPI functionality."""
    print("Testing basic FastAPI import...")
    
    try:
        from fastapi import FastAPI
        print("✓ FastAPI import successful")
        
        app = FastAPI()
        print("✓ FastAPI app creation successful")
        
        @app.get("/")
        def read_root():
            return {"Hello": "World"}
        
        print("✓ FastAPI route definition successful")
        
        # Test with TestClient
        from fastapi.testclient import TestClient
        print("✓ TestClient import successful")
        
        client = TestClient(app)
        print("✓ TestClient creation successful")
        
        response = client.get("/")
        print(f"✓ Test request successful: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        return True
        
    except Exception as e:
        print(f"✗ FastAPI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_basic():
    """Test basic Pydantic functionality."""
    print("\nTesting basic Pydantic functionality...")
    
    try:
        from pydantic import BaseModel
        print("✓ Pydantic BaseModel import successful")
        
        class TestModel(BaseModel):
            name: str
            age: int
        
        print("✓ Pydantic model definition successful")
        
        test_instance = TestModel(name="Test", age=25)
        print(f"✓ Pydantic model instantiation successful: {test_instance}")
        
        return True
        
    except Exception as e:
        print(f"✗ Pydantic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run FastAPI compatibility tests."""
    print("=" * 50)
    print("FASTAPI/PYDANTIC COMPATIBILITY TEST")
    print("=" * 50)
    
    pydantic_ok = test_pydantic_basic()
    fastapi_ok = test_fastapi_basic()
    
    print("\n" + "=" * 50)
    print("COMPATIBILITY TEST RESULTS")
    print("=" * 50)
    print(f"Pydantic: {'✓ WORKING' if pydantic_ok else '✗ BROKEN'}")
    print(f"FastAPI:  {'✓ WORKING' if fastapi_ok else '✗ BROKEN'}")
    
    if pydantic_ok and fastapi_ok:
        print("\n🎉 FastAPI/Pydantic compatibility is working!")
        return True
    else:
        print("\n⚠️ FastAPI/Pydantic compatibility issues detected")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)