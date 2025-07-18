"""
Unit tests for validation and serialization functionality.
"""

import os
import sys
import unittest
from datetime import datetime
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.schemas import (
    ValidationError,
    ConversationCreate,
    ConversationResponse,
    MemoryEntryCreate,
    MemoryEntryResponse,
    MemorySearchRequest,
    IdeaCreate,
    IdeaResponse,
    TaskCreate,
    TaskResponse
)
from shared.schemas.base import BaseSchema
from shared.serialization import ModelSerializer, DataExporter, DataValidator


class TestBaseValidation(unittest.TestCase):
    """Test base validation functionality."""
    
    def test_validate_uuid(self):
        """Test UUID validation."""
        # Valid UUID
        valid_uuid = str(uuid4())
        result = BaseSchema.validate_uuid(valid_uuid, "test_field")
        self.assertEqual(result, valid_uuid)
        
        # Invalid UUID
        with self.assertRaises(ValidationError):
            BaseSchema.validate_uuid("invalid-uuid", "test_field")
        
        # None UUID
        with self.assertRaises(ValidationError):
            BaseSchema.validate_uuid(None, "test_field")
    
    def test_validate_string(self):
        """Test string validation."""
        # Valid string
        result = BaseSchema.validate_string("test string", "test_field")
        self.assertEqual(result, "test string")
        
        # Empty string with allow_empty=False
        with self.assertRaises(ValidationError):
            BaseSchema.validate_string("", "test_field", allow_empty=False)
        
        # String too long
        with self.assertRaises(ValidationError):
            BaseSchema.validate_string("x" * 100, "test_field", max_length=50)
        
        # String too short
        with self.assertRaises(ValidationError):
            BaseSchema.validate_string("x", "test_field", min_length=5)
    
    def test_validate_integer(self):
        """Test integer validation."""
        # Valid integer
        result = BaseSchema.validate_integer(42, "test_field")
        self.assertEqual(result, 42)
        
        # String number
        result = BaseSchema.validate_integer("42", "test_field")
        self.assertEqual(result, 42)
        
        # Out of range
        with self.assertRaises(ValidationError):
            BaseSchema.validate_integer(5, "test_field", min_value=10)
        
        with self.assertRaises(ValidationError):
            BaseSchema.validate_integer(15, "test_field", max_value=10)
    
    def test_validate_float(self):
        """Test float validation."""
        # Valid float
        result = BaseSchema.validate_float(3.14, "test_field")
        self.assertEqual(result, 3.14)
        
        # Out of range
        with self.assertRaises(ValidationError):
            BaseSchema.validate_float(0.5, "test_field", min_value=1.0)
    
    def test_validate_boolean(self):
        """Test boolean validation."""
        # Valid boolean
        self.assertTrue(BaseSchema.validate_boolean(True, "test_field"))
        self.assertFalse(BaseSchema.validate_boolean(False, "test_field"))
        
        # String boolean
        self.assertTrue(BaseSchema.validate_boolean("true", "test_field"))
        self.assertFalse(BaseSchema.validate_boolean("false", "test_field"))
        
        # Integer boolean
        self.assertTrue(BaseSchema.validate_boolean(1, "test_field"))
        self.assertFalse(BaseSchema.validate_boolean(0, "test_field"))
    
    def test_validate_datetime(self):
        """Test datetime validation."""
        # Valid datetime
        now = datetime.now()
        result = BaseSchema.validate_datetime(now, "test_field")
        self.assertEqual(result, now)
        
        # ISO string
        iso_string = "2023-12-01T10:30:00"
        result = BaseSchema.validate_datetime(iso_string, "test_field")
        self.assertIsInstance(result, datetime)
        
        # None with allow_none=True
        result = BaseSchema.validate_datetime(None, "test_field", allow_none=True)
        self.assertIsNone(result)
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        # Dangerous characters
        dangerous_text = "<script>alert('xss')</script>"
        sanitized = BaseSchema.sanitize_text(dangerous_text)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        
        # Whitespace normalization
        messy_text = "  multiple   spaces  "
        sanitized = BaseSchema.sanitize_text(messy_text)
        self.assertEqual(sanitized, "multiple spaces")


class TestConversationSchemas(unittest.TestCase):
    """Test conversation schema validation."""
    
    def test_conversation_create_valid(self):
        """Test valid conversation creation."""
        session_id = str(uuid4())
        schema = ConversationCreate(
            session_id=session_id,
            user_input="Hello, Aether!",
            ai_response="Hello! How can I help you?",
            context_metadata={"test": True}
        )
        
        self.assertEqual(schema.session_id, session_id)
        self.assertEqual(schema.user_input, "Hello, Aether!")
        self.assertEqual(schema.ai_response, "Hello! How can I help you?")
        self.assertEqual(schema.context_metadata, {"test": True})
    
    def test_conversation_create_invalid(self):
        """Test invalid conversation creation."""
        # Empty user input
        with self.assertRaises(ValidationError):
            ConversationCreate(
                session_id=str(uuid4()),
                user_input="",
                ai_response="Response"
            )
        
        # Invalid session ID
        with self.assertRaises(ValidationError):
            ConversationCreate(
                session_id="invalid-uuid",
                user_input="Input",
                ai_response="Response"
            )
    
    def test_conversation_response(self):
        """Test conversation response schema."""
        conv_id = str(uuid4())
        session_id = str(uuid4())
        now = datetime.now()
        
        schema = ConversationResponse(
            id=conv_id,
            session_id=session_id,
            user_input="Test input",
            ai_response="Test response",
            context_metadata={},
            created_at=now,
            updated_at=now
        )
        
        self.assertEqual(schema.id, conv_id)
        self.assertEqual(schema.session_id, session_id)


class TestMemorySchemas(unittest.TestCase):
    """Test memory schema validation."""
    
    def test_memory_create_valid(self):
        """Test valid memory creation."""
        schema = MemoryEntryCreate(
            content="Test memory content",
            importance_score=0.8,
            tags=["test", "memory"],
            user_editable=True
        )
        
        self.assertEqual(schema.content, "Test memory content")
        self.assertEqual(schema.importance_score, 0.8)
        self.assertEqual(schema.tags, ["test", "memory"])
        self.assertTrue(schema.user_editable)
    
    def test_memory_create_invalid(self):
        """Test invalid memory creation."""
        # Invalid importance score
        with self.assertRaises(ValidationError):
            MemoryEntryCreate(
                content="Test content",
                importance_score=1.5  # > 1.0
            )
        
        # Empty content
        with self.assertRaises(ValidationError):
            MemoryEntryCreate(content="")
    
    def test_memory_search_request(self):
        """Test memory search request validation."""
        schema = MemorySearchRequest(
            query="test query",
            limit=5,
            threshold=0.7,
            importance_filter=0.5
        )
        
        self.assertEqual(schema.query, "test query")
        self.assertEqual(schema.limit, 5)
        self.assertEqual(schema.threshold, 0.7)
        self.assertEqual(schema.importance_filter, 0.5)


class TestIdeaSchemas(unittest.TestCase):
    """Test idea schema validation."""
    
    def test_idea_create_valid(self):
        """Test valid idea creation."""
        schema = IdeaCreate(
            content="Build a new feature",
            source="desktop",
            category="feature",
            priority_score=0.9
        )
        
        self.assertEqual(schema.content, "Build a new feature")
        self.assertEqual(schema.source, "desktop")
        self.assertEqual(schema.category, "feature")
        self.assertEqual(schema.priority_score, 0.9)
    
    def test_idea_create_invalid_source(self):
        """Test invalid idea source."""
        with self.assertRaises(ValidationError):
            IdeaCreate(
                content="Test idea",
                source="invalid_source"
            )


class TestTaskSchemas(unittest.TestCase):
    """Test task schema validation."""
    
    def test_task_create_valid(self):
        """Test valid task creation."""
        schema = TaskCreate(
            title="Complete project",
            description="Finish the project by deadline",
            priority=3,
            due_date=datetime.now()
        )
        
        self.assertEqual(schema.title, "Complete project")
        self.assertEqual(schema.description, "Finish the project by deadline")
        self.assertEqual(schema.priority, 3)
    
    def test_task_create_invalid_priority(self):
        """Test invalid task priority."""
        with self.assertRaises(ValidationError):
            TaskCreate(
                title="Test task",
                priority=5  # > 4
            )


class TestSerialization(unittest.TestCase):
    """Test serialization functionality."""
    
    def test_to_json_dict(self):
        """Test JSON dictionary conversion."""
        schema = MemoryEntryCreate(
            content="Test content",
            importance_score=0.8,
            tags=["test"]
        )
        
        json_dict = schema.to_dict()
        
        self.assertIsInstance(json_dict, dict)
        self.assertEqual(json_dict['content'], "Test content")
        self.assertEqual(json_dict['importance_score'], 0.8)
        self.assertEqual(json_dict['tags'], ["test"])
    
    def test_to_json_string(self):
        """Test JSON string conversion."""
        schema = MemoryEntryCreate(
            content="Test content",
            importance_score=0.8
        )
        
        json_string = schema.to_json()
        
        self.assertIsInstance(json_string, str)
        self.assertIn("Test content", json_string)


class TestDataValidator(unittest.TestCase):
    """Test data validation functionality."""
    
    def test_validate_conversation_data(self):
        """Test conversation data validation."""
        # Valid data
        valid_data = {
            'user_input': 'Hello',
            'ai_response': 'Hi there!',
            'session_id': str(uuid4())
        }
        errors = DataValidator.validate_conversation_data(valid_data)
        self.assertEqual(len(errors), 0)
        
        # Invalid data - missing field
        invalid_data = {
            'user_input': 'Hello'
            # Missing ai_response and session_id
        }
        errors = DataValidator.validate_conversation_data(invalid_data)
        self.assertGreater(len(errors), 0)
    
    def test_validate_memory_data(self):
        """Test memory data validation."""
        # Valid data
        valid_data = {
            'content': 'Test memory',
            'importance_score': 0.8,
            'tags': ['test']
        }
        errors = DataValidator.validate_memory_data(valid_data)
        self.assertEqual(len(errors), 0)
        
        # Invalid data - bad importance score
        invalid_data = {
            'content': 'Test memory',
            'importance_score': 1.5  # > 1.0
        }
        errors = DataValidator.validate_memory_data(invalid_data)
        self.assertGreater(len(errors), 0)


class TestDataExporter(unittest.TestCase):
    """Test data export functionality."""
    
    def test_export_conversations_csv(self):
        """Test conversation CSV export."""
        conversations = [
            ConversationResponse(
                id=str(uuid4()),
                session_id=str(uuid4()),
                user_input="Hello",
                ai_response="Hi",
                context_metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        csv_output = DataExporter.export_conversations_csv(conversations)
        
        self.assertIsInstance(csv_output, str)
        self.assertIn("Hello", csv_output)
        self.assertIn("Hi", csv_output)
    
    def test_export_memories_csv(self):
        """Test memory CSV export."""
        memories = [
            MemoryEntryResponse(
                id=str(uuid4()),
                content="Test memory",
                importance_score=0.8,
                tags=["test"],
                user_editable=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        csv_output = DataExporter.export_memories_csv(memories)
        
        self.assertIsInstance(csv_output, str)
        self.assertIn("Test memory", csv_output)
        self.assertIn("test", csv_output)


if __name__ == "__main__":
    unittest.main(verbosity=2)