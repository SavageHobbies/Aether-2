"""
Task schemas for Aether AI Companion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import BaseSchema, ValidationError


class TaskCreate(BaseSchema):
    """Schema for creating a new task."""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        due_date: Optional[datetime] = None,
        source_conversation_id: Optional[str] = None,
        source_idea_id: Optional[str] = None,
        external_integrations: Optional[Dict[str, str]] = None
    ):
        """
        Initialize task creation schema.
        
        Args:
            title: Task title
            description: Task description
            priority: Priority level (1=low, 2=medium, 3=high, 4=urgent)
            due_date: Due date (optional)
            source_conversation_id: Source conversation ID (optional)
            source_idea_id: Source idea ID (optional)
            external_integrations: External system integrations (optional)
        """
        self.title = self.validate_string(
            title, "title",
            min_length=1, max_length=200, allow_empty=False
        )
        self.description = self.validate_string(
            description, "description",
            max_length=2000
        )
        self.priority = self.validate_integer(
            priority, "priority",
            min_value=1, max_value=4
        )
        self.due_date = self.validate_datetime(due_date, "due_date")
        
        if source_conversation_id is not None:
            self.source_conversation_id = self.validate_uuid(
                source_conversation_id, "source_conversation_id"
            )
        else:
            self.source_conversation_id = None
        
        if source_idea_id is not None:
            self.source_idea_id = self.validate_uuid(source_idea_id, "source_idea_id")
        else:
            self.source_idea_id = None
        
        self.external_integrations = self.validate_dict(
            external_integrations or {}, "external_integrations"
        )
        
        # Sanitize text fields
        self.title = self.sanitize_text(self.title)
        self.description = self.sanitize_text(self.description)


class TaskUpdate(BaseSchema):
    """Schema for updating an existing task."""
    
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        due_date: Optional[datetime] = None,
        external_integrations: Optional[Dict[str, str]] = None
    ):
        """
        Initialize task update schema.
        
        Args:
            title: Updated title (optional)
            description: Updated description (optional)
            priority: Updated priority (optional)
            status: Updated status (optional)
            due_date: Updated due date (optional)
            external_integrations: Updated integrations (optional)
        """
        if title is not None:
            self.title = self.validate_string(
                title, "title",
                min_length=1, max_length=200, allow_empty=False
            )
            self.title = self.sanitize_text(self.title)
        else:
            self.title = None
        
        if description is not None:
            self.description = self.validate_string(
                description, "description",
                max_length=2000
            )
            self.description = self.sanitize_text(self.description)
        else:
            self.description = None
        
        if priority is not None:
            self.priority = self.validate_integer(
                priority, "priority",
                min_value=1, max_value=4
            )
        else:
            self.priority = None
        
        if status is not None:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            self.status = self.validate_string(status, "status")
            if self.status not in valid_statuses:
                raise ValidationError(
                    f"Status must be one of: {', '.join(valid_statuses)}",
                    "status", status
                )
        else:
            self.status = None
        
        self.due_date = self.validate_datetime(due_date, "due_date") if due_date is not None else None
        
        self.external_integrations = self.validate_dict(
            external_integrations, "external_integrations"
        ) if external_integrations is not None else None


class TaskResponse(BaseSchema):
    """Schema for task response data."""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        priority: int,
        status: str,
        due_date: Optional[datetime],
        source_conversation_id: Optional[str],
        source_idea_id: Optional[str],
        external_integrations: Dict[str, str],
        created_at: datetime,
        updated_at: datetime,
        dependencies: Optional[List[str]] = None
    ):
        """
        Initialize task response schema.
        
        Args:
            id: Task ID
            title: Task title
            description: Task description
            priority: Priority level
            status: Task status
            due_date: Due date
            source_conversation_id: Source conversation ID
            source_idea_id: Source idea ID
            external_integrations: External integrations
            created_at: Creation timestamp
            updated_at: Update timestamp
            dependencies: Task dependencies
        """
        self.id = self.validate_uuid(id, "id")
        self.title = self.validate_string(title, "title")
        self.description = self.validate_string(description, "description")
        self.priority = self.validate_integer(
            priority, "priority",
            min_value=1, max_value=4
        )
        
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        self.status = self.validate_string(status, "status")
        if self.status not in valid_statuses:
            raise ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}",
                "status", status
            )
        
        self.due_date = self.validate_datetime(due_date, "due_date")
        
        if source_conversation_id:
            self.source_conversation_id = self.validate_uuid(
                source_conversation_id, "source_conversation_id"
            )
        else:
            self.source_conversation_id = None
        
        if source_idea_id:
            self.source_idea_id = self.validate_uuid(source_idea_id, "source_idea_id")
        else:
            self.source_idea_id = None
        
        self.external_integrations = self.validate_dict(external_integrations, "external_integrations")
        self.created_at = self.validate_datetime(created_at, "created_at", allow_none=False)
        self.updated_at = self.validate_datetime(updated_at, "updated_at", allow_none=False)
        
        self.dependencies = self.validate_list(
            dependencies or [], "dependencies",
            item_validator=lambda x: self.validate_uuid(x, "dependency_id")
        )


class TaskSearchRequest(BaseSchema):
    """Schema for task search requests."""
    
    def __init__(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """
        Initialize task search request.
        
        Args:
            query: Text search query
            status: Filter by status
            priority: Filter by priority
            due_before: Filter by due date before
            due_after: Filter by due date after
            source_type: Filter by source type (conversation/idea)
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
        
        if status is not None:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            self.status = self.validate_string(status, "status")
            if self.status not in valid_statuses:
                raise ValidationError(
                    f"Status must be one of: {', '.join(valid_statuses)}",
                    "status", status
                )
        else:
            self.status = None
        
        if priority is not None:
            self.priority = self.validate_integer(
                priority, "priority",
                min_value=1, max_value=4
            )
        else:
            self.priority = None
        
        self.due_before = self.validate_datetime(due_before, "due_before")
        self.due_after = self.validate_datetime(due_after, "due_after")
        
        if source_type is not None:
            valid_source_types = ["conversation", "idea", "manual"]
            self.source_type = self.validate_string(source_type, "source_type")
            if self.source_type not in valid_source_types:
                raise ValidationError(
                    f"source_type must be one of: {', '.join(valid_source_types)}",
                    "source_type", source_type
                )
        else:
            self.source_type = None
        
        self.limit = self.validate_integer(limit, "limit", min_value=1, max_value=1000)
        self.offset = self.validate_integer(offset, "offset", min_value=0)
        
        valid_sort_fields = ["created_at", "updated_at", "due_date", "priority", "title"]
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
        
        # Validate date range
        if self.due_before and self.due_after and self.due_after > self.due_before:
            raise ValidationError("due_after must be before due_before", "date_range")


class TaskBatchRequest(BaseSchema):
    """Schema for batch task operations."""
    
    def __init__(
        self,
        task_ids: List[str],
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize batch task request.
        
        Args:
            task_ids: List of task IDs
            operation: Operation to perform
            parameters: Operation parameters
        """
        self.task_ids = self.validate_list(
            task_ids, "task_ids",
            item_validator=lambda x: self.validate_uuid(x, "task_id"),
            min_length=1, max_length=100
        )
        
        valid_operations = ["delete", "update_status", "update_priority", "set_due_date", "export"]
        self.operation = self.validate_string(operation, "operation")
        if self.operation not in valid_operations:
            raise ValidationError(
                f"Operation must be one of: {', '.join(valid_operations)}",
                "operation", operation
            )
        
        self.parameters = self.validate_dict(parameters, "parameters")


class TaskDependencyRequest(BaseSchema):
    """Schema for task dependency operations."""
    
    def __init__(
        self,
        dependent_task_id: str,
        prerequisite_task_id: str,
        dependency_type: str = "blocks"
    ):
        """
        Initialize task dependency request.
        
        Args:
            dependent_task_id: ID of dependent task
            prerequisite_task_id: ID of prerequisite task
            dependency_type: Type of dependency
        """
        self.dependent_task_id = self.validate_uuid(dependent_task_id, "dependent_task_id")
        self.prerequisite_task_id = self.validate_uuid(prerequisite_task_id, "prerequisite_task_id")
        
        if self.dependent_task_id == self.prerequisite_task_id:
            raise ValidationError("Task cannot depend on itself", "task_ids")
        
        valid_types = ["blocks", "related", "subtask"]
        self.dependency_type = self.validate_string(dependency_type, "dependency_type")
        if self.dependency_type not in valid_types:
            raise ValidationError(
                f"Dependency type must be one of: {', '.join(valid_types)}",
                "dependency_type", dependency_type
            )