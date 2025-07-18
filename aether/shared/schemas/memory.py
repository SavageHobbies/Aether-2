"""
Memory entry schemas for Aether AI Companion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import BaseSchema, ValidationError


class MemoryEntryCreate(BaseSchema):
    """Schema for creating a new memory entry."""
    
    def __init__(
        self,
        content: str,
        importance_score: float = 1.0,
        tags: Optional[List[str]] = None,
        user_editable: bool = True
    ):
        """
        Initialize memory entry creation schema.
        
        Args:
            content: Memory content
            importance_score: Importance score (0.0 to 1.0)
            tags: Optional tags
            user_editable: Whether user can edit this memory
        """
        self.content = self.validate_string(
            content, "content",
            min_length=1, max_length=5000, allow_empty=False
        )
        self.importance_score = self.validate_float(
            importance_score, "importance_score",
            min_value=0.0, max_value=1.0
        )
        self.tags = self.validate_list(
            tags or [], "tags",
            item_validator=lambda x: self.validate_string(
                x, "tag", min_length=1, max_length=50, allow_empty=False
            ),
            max_length=20
        )
        self.user_editable = self.validate_boolean(user_editable, "user_editable")
        
        # Sanitize content
        self.content = self.sanitize_text(self.content)
        
        # Validate and sanitize tags
        if self.tags:
            sanitized_tags = []
            for tag in self.tags:
                sanitized_tag = self.sanitize_text(tag).lower()
                if sanitized_tag and sanitized_tag not in sanitized_tags:
                    sanitized_tags.append(sanitized_tag)
            self.tags = sanitized_tags


class MemoryEntryUpdate(BaseSchema):
    """Schema for updating an existing memory entry."""
    
    def __init__(
        self,
        content: Optional[str] = None,
        importance_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        user_editable: Optional[bool] = None
    ):
        """
        Initialize memory entry update schema.
        
        Args:
            content: Updated content (optional)
            importance_score: Updated importance score (optional)
            tags: Updated tags (optional)
            user_editable: Updated editability flag (optional)
        """
        if content is not None:
            self.content = self.validate_string(
                content, "content",
                min_length=1, max_length=5000, allow_empty=False
            )
            self.content = self.sanitize_text(self.content)
        else:
            self.content = None
        
        if importance_score is not None:
            self.importance_score = self.validate_float(
                importance_score, "importance_score",
                min_value=0.0, max_value=1.0
            )
        else:
            self.importance_score = None
        
        if tags is not None:
            self.tags = self.validate_list(
                tags, "tags",
                item_validator=lambda x: self.validate_string(
                    x, "tag", min_length=1, max_length=50, allow_empty=False
                ),
                max_length=20
            )
            # Sanitize tags
            if self.tags:
                sanitized_tags = []
                for tag in self.tags:
                    sanitized_tag = self.sanitize_text(tag).lower()
                    if sanitized_tag and sanitized_tag not in sanitized_tags:
                        sanitized_tags.append(sanitized_tag)
                self.tags = sanitized_tags
        else:
            self.tags = None
        
        if user_editable is not None:
            self.user_editable = self.validate_boolean(user_editable, "user_editable")
        else:
            self.user_editable = None


class MemoryEntryResponse(BaseSchema):
    """Schema for memory entry response data."""
    
    def __init__(
        self,
        id: str,
        content: str,
        importance_score: float,
        tags: List[str],
        user_editable: bool,
        created_at: datetime,
        updated_at: datetime
    ):
        """
        Initialize memory entry response schema.
        
        Args:
            id: Memory entry ID
            content: Memory content
            importance_score: Importance score
            tags: Tags list
            user_editable: Whether user can edit
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        self.id = self.validate_uuid(id, "id")
        self.content = self.validate_string(content, "content")
        self.importance_score = self.validate_float(
            importance_score, "importance_score",
            min_value=0.0, max_value=1.0
        )
        self.tags = self.validate_list(tags or [], "tags")
        self.user_editable = self.validate_boolean(user_editable, "user_editable")
        self.created_at = self.validate_datetime(created_at, "created_at", allow_none=False)
        self.updated_at = self.validate_datetime(updated_at, "updated_at", allow_none=False)


class MemorySearchRequest(BaseSchema):
    """Schema for memory search requests."""
    
    def __init__(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        importance_filter: Optional[float] = None,
        tags_filter: Optional[List[str]] = None,
        user_editable_only: bool = False
    ):
        """
        Initialize memory search request.
        
        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity threshold
            importance_filter: Minimum importance score
            tags_filter: Filter by tags
            user_editable_only: Only return user-editable memories
        """
        self.query = self.validate_string(
            query, "query",
            min_length=1, max_length=1000, allow_empty=False
        )
        self.limit = self.validate_integer(limit, "limit", min_value=1, max_value=100)
        self.threshold = self.validate_float(
            threshold, "threshold",
            min_value=0.0, max_value=1.0
        )
        
        if importance_filter is not None:
            self.importance_filter = self.validate_float(
                importance_filter, "importance_filter",
                min_value=0.0, max_value=1.0
            )
        else:
            self.importance_filter = None
        
        if tags_filter is not None:
            self.tags_filter = self.validate_list(
                tags_filter, "tags_filter",
                item_validator=lambda x: self.validate_string(
                    x, "tag", min_length=1, max_length=50, allow_empty=False
                ),
                max_length=10
            )
            # Sanitize tags
            if self.tags_filter:
                self.tags_filter = [self.sanitize_text(tag).lower() for tag in self.tags_filter]
        else:
            self.tags_filter = None
        
        self.user_editable_only = self.validate_boolean(user_editable_only, "user_editable_only")
        
        # Sanitize query
        self.query = self.sanitize_text(self.query)


class MemorySearchResponse(BaseSchema):
    """Schema for memory search response."""
    
    def __init__(
        self,
        memory_entry: MemoryEntryResponse,
        similarity_score: float,
        matched_tags: Optional[List[str]] = None
    ):
        """
        Initialize memory search response.
        
        Args:
            memory_entry: Memory entry data
            similarity_score: Similarity score
            matched_tags: Tags that matched the search
        """
        if not isinstance(memory_entry, MemoryEntryResponse):
            raise ValidationError("memory_entry must be a MemoryEntryResponse", "memory_entry")
        
        self.memory_entry = memory_entry
        self.similarity_score = self.validate_float(
            similarity_score, "similarity_score",
            min_value=0.0, max_value=1.0
        )
        self.matched_tags = self.validate_list(
            matched_tags or [], "matched_tags"
        )


class MemoryBatchRequest(BaseSchema):
    """Schema for batch memory operations."""
    
    def __init__(
        self,
        memory_ids: List[str],
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize batch memory request.
        
        Args:
            memory_ids: List of memory IDs
            operation: Operation to perform
            parameters: Operation parameters
        """
        self.memory_ids = self.validate_list(
            memory_ids, "memory_ids",
            item_validator=lambda x: self.validate_uuid(x, "memory_id"),
            min_length=1, max_length=100
        )
        
        valid_operations = ["delete", "update_importance", "add_tags", "remove_tags", "export"]
        self.operation = self.validate_string(operation, "operation")
        if self.operation not in valid_operations:
            raise ValidationError(
                f"Operation must be one of: {', '.join(valid_operations)}",
                "operation", operation
            )
        
        self.parameters = self.validate_dict(parameters, "parameters")


class MemoryConnectionRequest(BaseSchema):
    """Schema for creating memory connections."""
    
    def __init__(
        self,
        from_memory_id: str,
        to_memory_id: str,
        connection_strength: float = 1.0,
        connection_type: str = "related"
    ):
        """
        Initialize memory connection request.
        
        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            connection_strength: Connection strength (0.0 to 1.0)
            connection_type: Type of connection
        """
        self.from_memory_id = self.validate_uuid(from_memory_id, "from_memory_id")
        self.to_memory_id = self.validate_uuid(to_memory_id, "to_memory_id")
        
        if self.from_memory_id == self.to_memory_id:
            raise ValidationError("Cannot create connection to self", "memory_ids")
        
        self.connection_strength = self.validate_float(
            connection_strength, "connection_strength",
            min_value=0.0, max_value=1.0
        )
        
        valid_types = ["related", "similar", "opposite", "causal", "temporal"]
        self.connection_type = self.validate_string(connection_type, "connection_type")
        if self.connection_type not in valid_types:
            raise ValidationError(
                f"Connection type must be one of: {', '.join(valid_types)}",
                "connection_type", connection_type
            )