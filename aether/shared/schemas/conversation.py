"""
Conversation schemas for Aether AI Companion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import BaseSchema, ValidationError


class ConversationCreate(BaseSchema):
    """Schema for creating a new conversation."""
    
    def __init__(
        self,
        session_id: str,
        user_input: str,
        ai_response: str,
        context_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize conversation creation schema.
        
        Args:
            session_id: Session identifier
            user_input: User's input message
            ai_response: AI's response message
            context_metadata: Optional context metadata
        """
        self.session_id = self.validate_uuid(session_id, "session_id")
        self.user_input = self.validate_string(
            user_input, "user_input", 
            min_length=1, max_length=10000, allow_empty=False
        )
        self.ai_response = self.validate_string(
            ai_response, "ai_response",
            min_length=1, max_length=10000, allow_empty=False
        )
        self.context_metadata = self.validate_dict(
            context_metadata or {}, "context_metadata"
        )
        
        # Sanitize text inputs
        self.user_input = self.sanitize_text(self.user_input)
        self.ai_response = self.sanitize_text(self.ai_response)


class ConversationUpdate(BaseSchema):
    """Schema for updating an existing conversation."""
    
    def __init__(
        self,
        user_input: Optional[str] = None,
        ai_response: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize conversation update schema.
        
        Args:
            user_input: Updated user input (optional)
            ai_response: Updated AI response (optional)
            context_metadata: Updated context metadata (optional)
        """
        if user_input is not None:
            self.user_input = self.validate_string(
                user_input, "user_input",
                min_length=1, max_length=10000, allow_empty=False
            )
            self.user_input = self.sanitize_text(self.user_input)
        else:
            self.user_input = None
        
        if ai_response is not None:
            self.ai_response = self.validate_string(
                ai_response, "ai_response",
                min_length=1, max_length=10000, allow_empty=False
            )
            self.ai_response = self.sanitize_text(self.ai_response)
        else:
            self.ai_response = None
        
        self.context_metadata = self.validate_dict(
            context_metadata, "context_metadata"
        ) if context_metadata is not None else None


class ConversationResponse(BaseSchema):
    """Schema for conversation response data."""
    
    def __init__(
        self,
        id: str,
        session_id: str,
        user_input: str,
        ai_response: str,
        context_metadata: Dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
        memory_references: Optional[List[str]] = None,
        extracted_tasks: Optional[List[str]] = None
    ):
        """
        Initialize conversation response schema.
        
        Args:
            id: Conversation ID
            session_id: Session ID
            user_input: User's input
            ai_response: AI's response
            context_metadata: Context metadata
            created_at: Creation timestamp
            updated_at: Update timestamp
            memory_references: Referenced memory IDs
            extracted_tasks: Extracted task IDs
        """
        self.id = self.validate_uuid(id, "id")
        self.session_id = self.validate_uuid(session_id, "session_id")
        self.user_input = self.validate_string(user_input, "user_input")
        self.ai_response = self.validate_string(ai_response, "ai_response")
        self.context_metadata = self.validate_dict(context_metadata, "context_metadata")
        self.created_at = self.validate_datetime(created_at, "created_at", allow_none=False)
        self.updated_at = self.validate_datetime(updated_at, "updated_at", allow_none=False)
        
        # Validate reference lists
        self.memory_references = self.validate_list(
            memory_references or [], "memory_references",
            item_validator=lambda x: self.validate_uuid(x, "memory_reference")
        )
        self.extracted_tasks = self.validate_list(
            extracted_tasks or [], "extracted_tasks",
            item_validator=lambda x: self.validate_uuid(x, "extracted_task")
        )


class ConversationSearchRequest(BaseSchema):
    """Schema for conversation search requests."""
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """
        Initialize conversation search request.
        
        Args:
            session_id: Filter by session ID
            query: Text search query
            limit: Maximum results
            offset: Result offset for pagination
            start_date: Filter by start date
            end_date: Filter by end date
        """
        self.session_id = self.validate_uuid(session_id, "session_id") if session_id else None
        self.query = self.validate_string(
            query, "query", max_length=1000
        ) if query else None
        self.limit = self.validate_integer(limit, "limit", min_value=1, max_value=1000)
        self.offset = self.validate_integer(offset, "offset", min_value=0)
        self.start_date = self.validate_datetime(start_date, "start_date")
        self.end_date = self.validate_datetime(end_date, "end_date")
        
        # Validate date range
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("start_date must be before end_date", "date_range")


class ConversationBatchRequest(BaseSchema):
    """Schema for batch conversation operations."""
    
    def __init__(
        self,
        conversation_ids: List[str],
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize batch conversation request.
        
        Args:
            conversation_ids: List of conversation IDs
            operation: Operation to perform
            parameters: Operation parameters
        """
        self.conversation_ids = self.validate_list(
            conversation_ids, "conversation_ids",
            item_validator=lambda x: self.validate_uuid(x, "conversation_id"),
            min_length=1, max_length=100
        )
        
        valid_operations = ["delete", "export", "update_metadata", "extract_tasks"]
        self.operation = self.validate_string(operation, "operation")
        if self.operation not in valid_operations:
            raise ValidationError(
                f"Operation must be one of: {', '.join(valid_operations)}",
                "operation", operation
            )
        
        self.parameters = self.validate_dict(parameters, "parameters")