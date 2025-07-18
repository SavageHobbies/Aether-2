"""
Serialization utilities for converting between database models and schemas.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from core.database.models import Conversation, Idea, MemoryEntry, Task
from shared.schemas import (
    ConversationResponse,
    IdeaResponse,
    MemoryEntryResponse,
    TaskResponse,
    ValidationError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SerializationError(Exception):
    """Error during serialization/deserialization."""
    
    def __init__(self, message: str, model_type: Optional[str] = None, field: Optional[str] = None):
        self.message = message
        self.model_type = model_type
        self.field = field
        super().__init__(self.message)


class ModelSerializer:
    """Handles serialization between database models and response schemas."""
    
    @staticmethod
    def serialize_conversation(conversation: Conversation) -> ConversationResponse:
        """
        Convert Conversation model to ConversationResponse schema.
        
        Args:
            conversation: Database conversation model
        
        Returns:
            ConversationResponse schema
        
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Extract memory references and task IDs from relationships
            # Note: These may be empty if relationships aren't loaded
            memory_references = []
            extracted_tasks = []
            
            # Safely check for loaded relationships
            try:
                if hasattr(conversation, 'memory_references') and conversation.memory_references is not None:
                    memory_references = [str(ref.memory_entry_id) for ref in conversation.memory_references]
            except:
                # Relationship not loaded, skip
                pass
            
            try:
                if hasattr(conversation, 'extracted_tasks') and conversation.extracted_tasks is not None:
                    extracted_tasks = [str(task.id) for task in conversation.extracted_tasks]
            except:
                # Relationship not loaded, skip
                pass
            
            return ConversationResponse(
                id=str(conversation.id),
                session_id=str(conversation.session_id),
                user_input=conversation.user_input,
                ai_response=conversation.ai_response,
                context_metadata=conversation.context_metadata or {},
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                memory_references=memory_references,
                extracted_tasks=extracted_tasks
            )
            
        except Exception as e:
            raise SerializationError(
                f"Failed to serialize conversation: {e}",
                "Conversation", str(conversation.id) if hasattr(conversation, 'id') else None
            )
    
    @staticmethod
    def serialize_memory_entry(memory_entry: MemoryEntry) -> MemoryEntryResponse:
        """
        Convert MemoryEntry model to MemoryEntryResponse schema.
        
        Args:
            memory_entry: Database memory entry model
        
        Returns:
            MemoryEntryResponse schema
        
        Raises:
            SerializationError: If serialization fails
        """
        try:
            return MemoryEntryResponse(
                id=str(memory_entry.id),
                content=memory_entry.content,
                importance_score=memory_entry.importance_score,
                tags=memory_entry.tags or [],
                user_editable=memory_entry.user_editable,
                created_at=memory_entry.created_at,
                updated_at=memory_entry.updated_at
            )
            
        except Exception as e:
            raise SerializationError(
                f"Failed to serialize memory entry: {e}",
                "MemoryEntry", str(memory_entry.id) if hasattr(memory_entry, 'id') else None
            )
    
    @staticmethod
    def serialize_idea(idea: Idea) -> IdeaResponse:
        """
        Convert Idea model to IdeaResponse schema.
        
        Args:
            idea: Database idea model
        
        Returns:
            IdeaResponse schema
        
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Get converted task ID if exists
            converted_to_task_id = None
            try:
                if hasattr(idea, 'converted_task') and idea.converted_task:
                    converted_to_task_id = str(idea.converted_task.id)
            except:
                # Relationship not loaded, skip
                pass
            
            return IdeaResponse(
                id=str(idea.id),
                content=idea.content,
                source=idea.source,
                processed=idea.processed,
                category=idea.category,
                priority_score=idea.priority_score,
                extra_metadata=idea.extra_metadata or {},
                created_at=idea.created_at,
                updated_at=idea.updated_at,
                converted_to_task_id=converted_to_task_id
            )
            
        except Exception as e:
            raise SerializationError(
                f"Failed to serialize idea: {e}",
                "Idea", str(idea.id) if hasattr(idea, 'id') else None
            )
    
    @staticmethod
    def serialize_task(task: Task) -> TaskResponse:
        """
        Convert Task model to TaskResponse schema.
        
        Args:
            task: Database task model
        
        Returns:
            TaskResponse schema
        
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Extract dependency IDs
            dependencies = []
            try:
                if hasattr(task, 'dependencies') and task.dependencies:
                    dependencies = [str(dep.prerequisite_task_id) for dep in task.dependencies]
            except:
                # Relationship not loaded, skip
                pass
            
            return TaskResponse(
                id=str(task.id),
                title=task.title,
                description=task.description,
                priority=task.priority,
                status=task.status,
                due_date=task.due_date,
                source_conversation_id=str(task.source_conversation_id) if task.source_conversation_id else None,
                source_idea_id=str(task.source_idea_id) if task.source_idea_id else None,
                external_integrations=task.external_integrations or {},
                created_at=task.created_at,
                updated_at=task.updated_at,
                dependencies=dependencies
            )
            
        except Exception as e:
            raise SerializationError(
                f"Failed to serialize task: {e}",
                "Task", str(task.id) if hasattr(task, 'id') else None
            )
    
    @staticmethod
    def serialize_list(
        models: List[Any], 
        serializer_func: callable
    ) -> List[Any]:
        """
        Serialize a list of models using the provided serializer function.
        
        Args:
            models: List of database models
            serializer_func: Function to serialize individual models
        
        Returns:
            List of serialized schemas
        
        Raises:
            SerializationError: If any serialization fails
        """
        try:
            return [serializer_func(model) for model in models]
        except Exception as e:
            raise SerializationError(f"Failed to serialize list: {e}")


class DataExporter:
    """Handles data export in various formats."""
    
    @staticmethod
    def to_json_dict(schema: Any) -> Dict[str, Any]:
        """
        Convert schema to JSON-serializable dictionary.
        
        Args:
            schema: Schema object
        
        Returns:
            JSON-serializable dictionary
        """
        if hasattr(schema, 'to_dict'):
            return schema.to_dict()
        
        # Fallback for objects without to_dict method
        result = {}
        for attr_name in dir(schema):
            if not attr_name.startswith('_') and not callable(getattr(schema, attr_name)):
                value = getattr(schema, attr_name)
                
                # Convert datetime to ISO string
                if isinstance(value, datetime):
                    result[attr_name] = value.isoformat()
                # Convert lists and dicts recursively
                elif isinstance(value, list):
                    result[attr_name] = [
                        item.isoformat() if isinstance(item, datetime) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    result[attr_name] = {
                        k: v.isoformat() if isinstance(v, datetime) else v
                        for k, v in value.items()
                    }
                else:
                    result[attr_name] = value
        
        return result
    
    @staticmethod
    def to_csv_row(schema: Any, fields: Optional[List[str]] = None) -> List[str]:
        """
        Convert schema to CSV row.
        
        Args:
            schema: Schema object
            fields: Specific fields to include (optional)
        
        Returns:
            List of string values for CSV row
        """
        data = DataExporter.to_json_dict(schema)
        
        if fields:
            return [str(data.get(field, '')) for field in fields]
        else:
            return [str(value) for value in data.values()]
    
    @staticmethod
    def export_conversations_csv(conversations: List[ConversationResponse]) -> str:
        """
        Export conversations to CSV format.
        
        Args:
            conversations: List of conversation responses
        
        Returns:
            CSV string
        """
        if not conversations:
            return ""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        fields = ['id', 'session_id', 'user_input', 'ai_response', 'created_at', 'updated_at']
        writer.writerow(fields)
        
        # Data rows
        for conversation in conversations:
            writer.writerow(DataExporter.to_csv_row(conversation, fields))
        
        return output.getvalue()
    
    @staticmethod
    def export_memories_csv(memories: List[MemoryEntryResponse]) -> str:
        """
        Export memory entries to CSV format.
        
        Args:
            memories: List of memory entry responses
        
        Returns:
            CSV string
        """
        if not memories:
            return ""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        fields = ['id', 'content', 'importance_score', 'tags', 'user_editable', 'created_at']
        writer.writerow(fields)
        
        # Data rows
        for memory in memories:
            row_data = DataExporter.to_csv_row(memory, fields)
            # Convert tags list to string
            if memory.tags:
                row_data[3] = '; '.join(memory.tags)
            writer.writerow(row_data)
        
        return output.getvalue()


class DataValidator:
    """Validates data integrity and consistency."""
    
    @staticmethod
    def validate_conversation_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate conversation data for consistency.
        
        Args:
            data: Conversation data dictionary
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        required_fields = ['user_input', 'ai_response', 'session_id']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Check data types and constraints
        if data.get('user_input') and len(data['user_input']) > 10000:
            errors.append("User input exceeds maximum length (10000 characters)")
        
        if data.get('ai_response') and len(data['ai_response']) > 10000:
            errors.append("AI response exceeds maximum length (10000 characters)")
        
        return errors
    
    @staticmethod
    def validate_memory_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate memory entry data for consistency.
        
        Args:
            data: Memory entry data dictionary
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not data.get('content'):
            errors.append("Missing required field: content")
        
        # Check importance score
        importance = data.get('importance_score', 1.0)
        if not isinstance(importance, (int, float)) or importance < 0.0 or importance > 1.0:
            errors.append("Importance score must be between 0.0 and 1.0")
        
        # Check content length
        if data.get('content') and len(data['content']) > 5000:
            errors.append("Content exceeds maximum length (5000 characters)")
        
        # Check tags
        tags = data.get('tags', [])
        if tags and len(tags) > 20:
            errors.append("Too many tags (maximum 20)")
        
        return errors
    
    @staticmethod
    def validate_cross_references(
        conversations: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        ideas: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Validate cross-references between different data types.
        
        Args:
            conversations: List of conversation data
            memories: List of memory data
            ideas: List of idea data
            tasks: List of task data
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Create ID sets for validation
        conversation_ids = {conv.get('id') for conv in conversations if conv.get('id')}
        memory_ids = {mem.get('id') for mem in memories if mem.get('id')}
        idea_ids = {idea.get('id') for idea in ideas if idea.get('id')}
        task_ids = {task.get('id') for task in tasks if task.get('id')}
        
        # Validate task references
        for task in tasks:
            if task.get('source_conversation_id') and task['source_conversation_id'] not in conversation_ids:
                errors.append(f"Task {task.get('id')} references non-existent conversation {task['source_conversation_id']}")
            
            if task.get('source_idea_id') and task['source_idea_id'] not in idea_ids:
                errors.append(f"Task {task.get('id')} references non-existent idea {task['source_idea_id']}")
        
        # Validate conversation memory references
        for conv in conversations:
            memory_refs = conv.get('memory_references', [])
            for mem_id in memory_refs:
                if mem_id not in memory_ids:
                    errors.append(f"Conversation {conv.get('id')} references non-existent memory {mem_id}")
        
        return errors