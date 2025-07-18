"""
Idea schemas for Aether AI Companion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import BaseSchema, ValidationError


class IdeaCreate(BaseSchema):
    """Schema for creating a new idea."""
    
    def __init__(
        self,
        content: str,
        source: str,
        category: Optional[str] = None,
        priority_score: float = 0.0,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize idea creation schema.
        
        Args:
            content: Idea content
            source: Source of the idea (desktop, mobile, voice, web)
            category: Optional category
            priority_score: Priority score (0.0 to 1.0)
            extra_metadata: Optional metadata
        """
        self.content = self.validate_string(
            content, "content",
            min_length=1, max_length=5000, allow_empty=False
        )
        
        valid_sources = ["desktop", "mobile", "voice", "web"]
        self.source = self.validate_string(source, "source")
        if self.source not in valid_sources:
            raise ValidationError(
                f"Source must be one of: {', '.join(valid_sources)}",
                "source", source
            )
        
        if category is not None:
            self.category = self.validate_string(
                category, "category",
                min_length=1, max_length=100, allow_empty=False
            )
            self.category = self.sanitize_text(self.category).lower()
        else:
            self.category = None
        
        self.priority_score = self.validate_float(
            priority_score, "priority_score",
            min_value=0.0, max_value=1.0
        )
        
        self.extra_metadata = self.validate_dict(
            extra_metadata or {}, "extra_metadata"
        )
        
        # Sanitize content
        self.content = self.sanitize_text(self.content)


class IdeaUpdate(BaseSchema):
    """Schema for updating an existing idea."""
    
    def __init__(
        self,
        content: Optional[str] = None,
        category: Optional[str] = None,
        priority_score: Optional[float] = None,
        processed: Optional[bool] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize idea update schema.
        
        Args:
            content: Updated content (optional)
            category: Updated category (optional)
            priority_score: Updated priority score (optional)
            processed: Updated processed status (optional)
            extra_metadata: Updated metadata (optional)
        """
        if content is not None:
            self.content = self.validate_string(
                content, "content",
                min_length=1, max_length=5000, allow_empty=False
            )
            self.content = self.sanitize_text(self.content)
        else:
            self.content = None
        
        if category is not None:
            self.category = self.validate_string(
                category, "category",
                min_length=1, max_length=100, allow_empty=False
            )
            self.category = self.sanitize_text(self.category).lower()
        else:
            self.category = None
        
        if priority_score is not None:
            self.priority_score = self.validate_float(
                priority_score, "priority_score",
                min_value=0.0, max_value=1.0
            )
        else:
            self.priority_score = None
        
        if processed is not None:
            self.processed = self.validate_boolean(processed, "processed")
        else:
            self.processed = None
        
        self.extra_metadata = self.validate_dict(
            extra_metadata, "extra_metadata"
        ) if extra_metadata is not None else None


class IdeaResponse(BaseSchema):
    """Schema for idea response data."""
    
    def __init__(
        self,
        id: str,
        content: str,
        source: str,
        processed: bool,
        category: Optional[str],
        priority_score: float,
        extra_metadata: Dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
        converted_to_task_id: Optional[str] = None
    ):
        """
        Initialize idea response schema.
        
        Args:
            id: Idea ID
            content: Idea content
            source: Source of idea
            processed: Whether idea has been processed
            category: Idea category
            priority_score: Priority score
            extra_metadata: Extra metadata
            created_at: Creation timestamp
            updated_at: Update timestamp
            converted_to_task_id: ID of converted task (if any)
        """
        self.id = self.validate_uuid(id, "id")
        self.content = self.validate_string(content, "content")
        self.source = self.validate_string(source, "source")
        self.processed = self.validate_boolean(processed, "processed")
        self.category = self.validate_string(category, "category") if category else None
        self.priority_score = self.validate_float(
            priority_score, "priority_score",
            min_value=0.0, max_value=1.0
        )
        self.extra_metadata = self.validate_dict(extra_metadata, "extra_metadata")
        self.created_at = self.validate_datetime(created_at, "created_at", allow_none=False)
        self.updated_at = self.validate_datetime(updated_at, "updated_at", allow_none=False)
        
        if converted_to_task_id:
            self.converted_to_task_id = self.validate_uuid(converted_to_task_id, "converted_to_task_id")
        else:
            self.converted_to_task_id = None


class IdeaSearchRequest(BaseSchema):
    """Schema for idea search requests."""
    
    def __init__(
        self,
        query: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        processed: Optional[bool] = None,
        min_priority: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """
        Initialize idea search request.
        
        Args:
            query: Text search query
            source: Filter by source
            category: Filter by category
            processed: Filter by processed status
            min_priority: Minimum priority score
            limit: Maximum results
            offset: Result offset for pagination
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
        """
        if query is not None:
            self.query = self.validate_string(
                query, "query", max_length=1000
            )
            self.query = self.sanitize_text(self.query)
        else:
            self.query = None
        
        if source is not None:
            valid_sources = ["desktop", "mobile", "voice", "web"]
            self.source = self.validate_string(source, "source")
            if self.source not in valid_sources:
                raise ValidationError(
                    f"Source must be one of: {', '.join(valid_sources)}",
                    "source", source
                )
        else:
            self.source = None
        
        if category is not None:
            self.category = self.validate_string(category, "category")
            self.category = self.sanitize_text(self.category).lower()
        else:
            self.category = None
        
        if processed is not None:
            self.processed = self.validate_boolean(processed, "processed")
        else:
            self.processed = None
        
        if min_priority is not None:
            self.min_priority = self.validate_float(
                min_priority, "min_priority",
                min_value=0.0, max_value=1.0
            )
        else:
            self.min_priority = None
        
        self.limit = self.validate_integer(limit, "limit", min_value=1, max_value=1000)
        self.offset = self.validate_integer(offset, "offset", min_value=0)
        
        valid_sort_fields = ["created_at", "updated_at", "priority_score", "content"]
        self.sort_by = self.validate_string(sort_by, "sort_by")
        if self.sort_by not in valid_sort_fields:
            raise ValidationError(
                f"sort_by must be one of: {', '.join(valid_sort_fields)}",
                "sort_by", sort_by
            )
        
        valid_sort_orders = ["asc", "desc"]
        self.sort_order = self.validate_string(sort_order, "sort_order")
        if self.sort_order not in valid_sort_orders:
            raise ValidationError(
                f"sort_order must be one of: {', '.join(valid_sort_orders)}",
                "sort_order", sort_order
            )


class IdeaBatchRequest(BaseSchema):
    """Schema for batch idea operations."""
    
    def __init__(
        self,
        idea_ids: List[str],
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize batch idea request.
        
        Args:
            idea_ids: List of idea IDs
            operation: Operation to perform
            parameters: Operation parameters
        """
        self.idea_ids = self.validate_list(
            idea_ids, "idea_ids",
            item_validator=lambda x: self.validate_uuid(x, "idea_id"),
            min_length=1, max_length=100
        )
        
        valid_operations = ["delete", "mark_processed", "convert_to_tasks", "update_category", "export"]
        self.operation = self.validate_string(operation, "operation")
        if self.operation not in valid_operations:
            raise ValidationError(
                f"Operation must be one of: {', '.join(valid_operations)}",
                "operation", operation
            )
        
        self.parameters = self.validate_dict(parameters, "parameters")


class IdeaConversionRequest(BaseSchema):
    """Schema for converting ideas to tasks."""
    
    def __init__(
        self,
        idea_id: str,
        task_title: Optional[str] = None,
        task_description: Optional[str] = None,
        task_priority: int = 2,
        due_date: Optional[datetime] = None
    ):
        """
        Initialize idea conversion request.
        
        Args:
            idea_id: ID of idea to convert
            task_title: Custom task title (optional)
            task_description: Custom task description (optional)
            task_priority: Task priority (1-4)
            due_date: Task due date (optional)
        """
        self.idea_id = self.validate_uuid(idea_id, "idea_id")
        
        if task_title is not None:
            self.task_title = self.validate_string(
                task_title, "task_title",
                min_length=1, max_length=200, allow_empty=False
            )
            self.task_title = self.sanitize_text(self.task_title)
        else:
            self.task_title = None
        
        if task_description is not None:
            self.task_description = self.validate_string(
                task_description, "task_description",
                max_length=2000
            )
            self.task_description = self.sanitize_text(self.task_description)
        else:
            self.task_description = None
        
        self.task_priority = self.validate_integer(
            task_priority, "task_priority",
            min_value=1, max_value=4
        )
        
        self.due_date = self.validate_datetime(due_date, "due_date")