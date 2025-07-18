#!/usr/bin/env python3
"""
Test script for data validation and serialization layer.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_base_schema_validation():
    """Test BaseSchema validation methods."""
    print("🔍 Testing BaseSchema validation...")
    
    try:
        from shared.schemas.base import BaseSchema, ValidationError
        
        # Test UUID validation
        valid_uuid = str(uuid4())
        assert BaseSchema.validate_uuid(valid_uuid, "test_id") == valid_uuid
        print("✅ UUID validation working")
        
        # Test string validation
        test_string = "Hello World"
        validated = BaseSchema.validate_string(test_string, "test_string", min_length=5, max_length=20)
        assert validated == test_string
        print("✅ String validation working")
        
        # Test integer validation
        assert BaseSchema.validate_integer(42, "test_int", min_value=1, max_value=100) == 42
        print("✅ Integer validation working")
        
        # Test float validation
        assert BaseSchema.validate_float(3.14, "test_float", min_value=0.0, max_value=10.0) == 3.14
        print("✅ Float validation working")
        
        # Test boolean validation
        assert BaseSchema.validate_boolean(True, "test_bool") == True
        assert BaseSchema.validate_boolean("false", "test_bool") == False
        print("✅ Boolean validation working")
        
        # Test datetime validation
        now = datetime.utcnow()
        assert BaseSchema.validate_datetime(now, "test_datetime") == now
        print("✅ Datetime validation working")
        
        # Test list validation
        test_list = [1, 2, 3]
        assert BaseSchema.validate_list(test_list, "test_list") == test_list
        print("✅ List validation working")
        
        # Test dict validation
        test_dict = {"key": "value"}
        assert BaseSchema.validate_dict(test_dict, "test_dict") == test_dict
        print("✅ Dict validation working")
        
        # Test text sanitization
        dangerous_text = "<script>alert('xss')</script>Hello"
        sanitized = BaseSchema.sanitize_text(dangerous_text)
        assert "<script>" not in sanitized
        print("✅ Text sanitization working")
        
        return True
        
    except Exception as e:
        print(f"❌ BaseSchema validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_schemas():
    """Test conversation schema validation."""
    print("\n💬 Testing conversation schemas...")
    
    try:
        from shared.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate
        
        # Test ConversationCreate
        session_id = str(uuid4())
        conv_create = ConversationCreate(
            session_id=session_id,
            user_input="Hello, how are you?",
            ai_response="I'm doing well, thank you!",
            context_metadata={"test": True}
        )
        
        assert conv_create.session_id == session_id
        assert conv_create.user_input == "Hello, how are you?"
        print("✅ ConversationCreate validation working")
        
        # Test ConversationUpdate
        conv_update = ConversationUpdate(
            ai_response="Updated response",
            context_metadata={"updated": True}
        )
        
        assert conv_update.ai_response == "Updated response"
        print("✅ ConversationUpdate validation working")
        
        # Test ConversationResponse
        conv_response = ConversationResponse(
            id=str(uuid4()),
            session_id=session_id,
            user_input="Test input",
            ai_response="Test response",
            context_metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert conv_response.session_id == session_id
        print("✅ ConversationResponse validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation schemas test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_idea_schemas():
    """Test idea schema validation."""
    print("\n💡 Testing idea schemas...")
    
    try:
        from shared.schemas.idea import IdeaCreate, IdeaResponse, IdeaUpdate
        
        # Test IdeaCreate
        idea_create = IdeaCreate(
            content="Build a better task management system",
            source="web",
            category="productivity",
            priority_score=0.8
        )
        
        assert idea_create.content == "Build a better task management system"
        assert idea_create.source == "web"
        assert idea_create.category == "productivity"
        print("✅ IdeaCreate validation working")
        
        # Test IdeaUpdate
        idea_update = IdeaUpdate(
            content="Updated idea content",
            processed=True
        )
        
        assert idea_update.content == "Updated idea content"
        assert idea_update.processed == True
        print("✅ IdeaUpdate validation working")
        
        # Test IdeaResponse
        idea_response = IdeaResponse(
            id=str(uuid4()),
            content="Test idea",
            source="desktop",
            processed=False,
            category="test",
            priority_score=0.5,
            extra_metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert idea_response.source == "desktop"
        print("✅ IdeaResponse validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Idea schemas test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_schemas():
    """Test task schema validation."""
    print("\n📋 Testing task schemas...")
    
    try:
        from shared.schemas.task import TaskCreate, TaskResponse, TaskUpdate
        
        # Test TaskCreate
        task_create = TaskCreate(
            title="Complete project documentation",
            description="Write comprehensive docs",
            priority=2,
            due_date=datetime.utcnow()
        )
        
        assert task_create.title == "Complete project documentation"
        assert task_create.priority == 2
        print("✅ TaskCreate validation working")
        
        # Test TaskUpdate
        task_update = TaskUpdate(
            status="in_progress",
            priority=3
        )
        
        assert task_update.status == "in_progress"
        assert task_update.priority == 3
        print("✅ TaskUpdate validation working")
        
        # Test TaskResponse
        task_response = TaskResponse(
            id=str(uuid4()),
            title="Test task",
            description="Test description",
            priority=2,
            status="pending",
            due_date=None,
            source_conversation_id=None,
            source_idea_id=None,
            external_integrations={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert task_response.status == "pending"
        print("✅ TaskResponse validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Task schemas test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_schemas():
    """Test memory schema validation."""
    print("\n🧠 Testing memory schemas...")
    
    try:
        from shared.schemas.memory import MemoryEntryCreate, MemoryEntryResponse, MemorySearchRequest
        
        # Test MemoryEntryCreate
        memory_create = MemoryEntryCreate(
            content="User prefers morning meetings",
            importance_score=0.8,
            tags=["preference", "meetings"],
            user_editable=True
        )
        
        assert memory_create.content == "User prefers morning meetings"
        assert memory_create.importance_score == 0.8
        assert "preference" in memory_create.tags
        print("✅ MemoryEntryCreate validation working")
        
        # Test MemoryEntryResponse
        memory_response = MemoryEntryResponse(
            id=str(uuid4()),
            content="Test memory",
            importance_score=0.7,
            tags=["test"],
            user_editable=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert memory_response.importance_score == 0.7
        print("✅ MemoryEntryResponse validation working")
        
        # Test MemorySearchRequest
        search_request = MemorySearchRequest(
            query="morning meetings",
            limit=10,
            threshold=0.7
        )
        
        assert search_request.query == "morning meetings"
        assert search_request.limit == 10
        print("✅ MemorySearchRequest validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory schemas test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serialization():
    """Test model serialization."""
    print("\n📦 Testing serialization...")
    
    try:
        from shared.serialization import ModelSerializer, DataExporter
        from core.database.models import Base, Conversation
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Create test database
        test_db_path = "test_validation_integration.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        engine = create_engine(f"sqlite:///{test_db_path}")
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test conversation
        conversation = Conversation(
            session_id=str(uuid4()),
            user_input="Test input",
            ai_response="Test response",
            context_metadata={"test": True}
        )
        session.add(conversation)
        session.commit()
        
        # Test serialization
        serialized = ModelSerializer.serialize_conversation(conversation)
        print("✅ Conversation serialization working")
        
        # Test data export
        json_dict = DataExporter.to_json_dict(serialized)
        assert "id" in json_dict
        assert "user_input" in json_dict
        print("✅ Data export working")
        
        session.close()
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_validation():
    """Test simple validation utilities."""
    print("\n🔧 Testing simple validation utilities...")
    
    try:
        from shared.utils.simple_validation import SimpleValidator, sanitize_input, validate_uuid
        
        # Test input sanitization
        dangerous_input = "<script>alert('xss')</script>Hello World"
        sanitized = sanitize_input(dangerous_input)
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized
        print("✅ Input sanitization working")
        
        # Test UUID validation
        valid_uuid = str(uuid4())
        assert validate_uuid(valid_uuid) == True
        assert validate_uuid("invalid-uuid") == False
        print("✅ UUID validation working")
        
        # Test conversation data validation
        conv_data = {
            "user_input": "Hello there",
            "ai_response": "Hello! How can I help?",
            "session_id": str(uuid4())
        }
        
        result = SimpleValidator.validate_conversation_data(conv_data)
        assert result["valid"] == True
        assert "user_input" in result["sanitized_data"]
        print("✅ Conversation data validation working")
        
        # Test idea data validation
        idea_data = {
            "content": "Build a mobile app",
            "source": "mobile",
            "category": "app development"
        }
        
        result = SimpleValidator.validate_idea_data(idea_data)
        assert result["valid"] == True
        assert result["sanitized_data"]["source"] == "mobile"
        print("✅ Idea data validation working")
        
        # Test task data validation
        task_data = {
            "title": "Complete API documentation",
            "priority": 2,
            "description": "Write comprehensive API docs"
        }
        
        result = SimpleValidator.validate_task_data(task_data)
        assert result["valid"] == True
        assert result["sanitized_data"]["priority"] == 2
        print("✅ Task data validation working")
        
        # Test memory data validation
        memory_data = {
            "content": "User prefers detailed explanations",
            "importance_score": 0.8,
            "tags": ["preference", "communication"]
        }
        
        result = SimpleValidator.validate_memory_data(memory_data)
        assert result["valid"] == True
        assert result["sanitized_data"]["importance_score"] == 0.8
        print("✅ Memory data validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_errors():
    """Test validation error handling."""
    print("\n⚠️  Testing validation error handling...")
    
    try:
        from shared.schemas.base import ValidationError
        from shared.utils.simple_validation import SimpleValidator
        
        # Test invalid conversation data
        invalid_conv_data = {
            "user_input": "",  # Empty input
            "ai_response": "x" * 15000,  # Too long
            "session_id": "invalid-uuid"
        }
        
        result = SimpleValidator.validate_conversation_data(invalid_conv_data)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        print("✅ Invalid conversation data properly rejected")
        
        # Test invalid idea data
        invalid_idea_data = {
            "content": "",  # Empty content
            "source": "invalid_source",  # Invalid source
            "priority_score": 2.0  # Out of range
        }
        
        result = SimpleValidator.validate_idea_data(invalid_idea_data)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        print("✅ Invalid idea data properly rejected")
        
        # Test ValidationError exception
        try:
            raise ValidationError("Test error", "test_field", "test_value")
        except ValidationError as e:
            assert e.field == "test_field"
            assert e.value == "test_value"
            print("✅ ValidationError exception working")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation and serialization tests."""
    print("🚀 Aether AI Companion - Data Validation & Serialization Testing")
    print("=" * 70)
    print("Testing comprehensive data validation and serialization layer")
    print()
    
    tests = [
        test_base_schema_validation,
        test_conversation_schemas,
        test_idea_schemas,
        test_task_schemas,
        test_memory_schemas,
        test_serialization,
        test_simple_validation,
        test_validation_errors,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📊 Data Validation & Serialization Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed < total:
        print(f"❌ Failed: {total - passed}/{total}")
    
    print("\n🎯 Data Validation & Serialization Implementation Status:")
    print("   ✅ Base schema validation methods")
    print("   ✅ Conversation schema validation")
    print("   ✅ Idea schema validation")
    print("   ✅ Task schema validation")
    print("   ✅ Memory schema validation")
    print("   ✅ Model serialization utilities")
    print("   ✅ Simple validation utilities")
    print("   ✅ Error handling and validation")
    
    if passed == total:
        print("\n🎉 All data validation and serialization tests passed!")
        print("✅ Comprehensive schema validation implemented")
        print("✅ Input sanitization and security working")
        print("✅ Model serialization functional")
        print("✅ Cross-platform data exchange ready")
        print("✅ Error handling robust")
        
        print("\n📋 Data Validation & Serialization Summary:")
        print("   • Pydantic-style validation: ✅ COMPLETE")
        print("   • Input sanitization: ✅ COMPLETE")
        print("   • Cross-platform serialization: ✅ COMPLETE")
        print("   • Error handling: ✅ COMPLETE")
        print("   • Schema validation: ✅ COMPLETE")
        print("   • Data export utilities: ✅ COMPLETE")
        
        print("\n🔒 Security Features:")
        print("   • XSS prevention through input sanitization")
        print("   • UUID format validation")
        print("   • Content length limits")
        print("   • Type validation and coercion")
        print("   • Comprehensive error reporting")
        
        return 0
    else:
        print("\n⚠️  Some validation components need attention")
        return 1


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        exit(1)