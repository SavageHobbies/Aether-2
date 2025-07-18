"""
Simple validation utilities without external dependencies.
"""

import re
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime
import json


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
    sanitized = text
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    # Limit length
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: String to validate as UUID
    
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid email, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_content_length(content: str, min_length: int = 0, max_length: int = 10000) -> bool:
    """
    Validate content length.
    
    Args:
        content: Content to validate
        min_length: Minimum length
        max_length: Maximum length
    
    Returns:
        True if length is valid, False otherwise
    """
    if not isinstance(content, str):
        return False
    
    return min_length <= len(content) <= max_length


def validate_priority(priority: Union[int, str]) -> bool:
    """
    Validate priority value (1-4).
    
    Args:
        priority: Priority value to validate
    
    Returns:
        True if valid priority, False otherwise
    """
    try:
        priority_int = int(priority)
        return 1 <= priority_int <= 4
    except (ValueError, TypeError):
        return False


def validate_importance_score(score: Union[float, int, str]) -> bool:
    """
    Validate importance score (0.0-1.0).
    
    Args:
        score: Score to validate
    
    Returns:
        True if valid score, False otherwise
    """
    try:
        score_float = float(score)
        return 0.0 <= score_float <= 1.0
    except (ValueError, TypeError):
        return False


def validate_source_type(source: str) -> bool:
    """
    Validate source type for ideas.
    
    Args:
        source: Source type to validate
    
    Returns:
        True if valid source, False otherwise
    """
    valid_sources = ["desktop", "mobile", "voice", "web"]
    return source in valid_sources


def validate_task_status(status: str) -> bool:
    """
    Validate task status.
    
    Args:
        status: Status to validate
    
    Returns:
        True if valid status, False otherwise
    """
    valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
    return status in valid_statuses


class ValidationError(Exception):
    """Custom validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)
    
    def __str__(self):
        if self.field:
            return f"Validation error in field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class SimpleValidator:
    """Simple input validator for all data types."""
    
    @staticmethod
    def validate_conversation_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate conversation input data.
        
        Args:
            data: Input data to validate
        
        Returns:
            Dictionary with validation results
        """
        result = {"valid": True, "errors": [], "sanitized_data": {}}
        
        # Validate required fields
        required_fields = ["user_input", "ai_response"]
        for field in required_fields:
            if field not in data or not data[field]:
                result["errors"].append(f"Missing required field: {field}")
                result["valid"] = False
        
        # Validate and sanitize user_input
        if "user_input" in data:
            if not validate_content_length(data["user_input"], 1, 10000):
                result["errors"].append("User input must be 1-10000 characters")
                result["valid"] = False
            else:
                result["sanitized_data"]["user_input"] = sanitize_input(data["user_input"])
        
        # Validate and sanitize ai_response
        if "ai_response" in data:
            if not validate_content_length(data["ai_response"], 1, 10000):
                result["errors"].append("AI response must be 1-10000 characters")
                result["valid"] = False
            else:
                result["sanitized_data"]["ai_response"] = sanitize_input(data["ai_response"])
        
        # Validate session_id if provided
        if "session_id" in data and data["session_id"]:
            if not validate_uuid(data["session_id"]):
                result["errors"].append("Invalid session_id format")
                result["valid"] = False
            else:
                result["sanitized_data"]["session_id"] = data["session_id"]
        
        return result
    
    @staticmethod
    def validate_idea_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate idea input data.
        
        Args:
            data: Input data to validate
        
        Returns:
            Dictionary with validation results
        """
        result = {"valid": True, "errors": [], "sanitized_data": {}}
        
        # Validate required fields
        if "content" not in data or not data["content"]:
            result["errors"].append("Missing required field: content")
            result["valid"] = False
        elif not validate_content_length(data["content"], 1, 5000):
            result["errors"].append("Content must be 1-5000 characters")
            result["valid"] = False
        else:
            result["sanitized_data"]["content"] = sanitize_input(data["content"])
        
        if "source" not in data or not data["source"]:
            result["errors"].append("Missing required field: source")
            result["valid"] = False
        elif not validate_source_type(data["source"]):
            result["errors"].append("Invalid source type")
            result["valid"] = False
        else:
            result["sanitized_data"]["source"] = data["source"]
        
        # Validate optional fields
        if "category" in data and data["category"]:
            if not validate_content_length(data["category"], 1, 100):
                result["errors"].append("Category must be 1-100 characters")
                result["valid"] = False
            else:
                result["sanitized_data"]["category"] = sanitize_input(data["category"]).lower()
        
        if "priority_score" in data:
            if not validate_importance_score(data["priority_score"]):
                result["errors"].append("Priority score must be between 0.0 and 1.0")
                result["valid"] = False
            else:
                result["sanitized_data"]["priority_score"] = float(data["priority_score"])
        
        return result
    
    @staticmethod
    def validate_task_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task input data.
        
        Args:
            data: Input data to validate
        
        Returns:
            Dictionary with validation results
        """
        result = {"valid": True, "errors": [], "sanitized_data": {}}
        
        # Validate required fields
        if "title" not in data or not data["title"]:
            result["errors"].append("Missing required field: title")
            result["valid"] = False
        elif not validate_content_length(data["title"], 1, 200):
            result["errors"].append("Title must be 1-200 characters")
            result["valid"] = False
        else:
            result["sanitized_data"]["title"] = sanitize_input(data["title"])
        
        if "priority" not in data:
            result["errors"].append("Missing required field: priority")
            result["valid"] = False
        elif not validate_priority(data["priority"]):
            result["errors"].append("Priority must be 1-4")
            result["valid"] = False
        else:
            result["sanitized_data"]["priority"] = int(data["priority"])
        
        # Validate optional fields
        if "description" in data:
            if not validate_content_length(data["description"], 0, 2000):
                result["errors"].append("Description must be 0-2000 characters")
                result["valid"] = False
            else:
                result["sanitized_data"]["description"] = sanitize_input(data["description"])
        
        if "status" in data and data["status"]:
            if not validate_task_status(data["status"]):
                result["errors"].append("Invalid task status")
                result["valid"] = False
            else:
                result["sanitized_data"]["status"] = data["status"]
        
        return result
    
    @staticmethod
    def validate_memory_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate memory input data.
        
        Args:
            data: Input data to validate
        
        Returns:
            Dictionary with validation results
        """
        result = {"valid": True, "errors": [], "sanitized_data": {}}
        
        # Validate required fields
        if "content" not in data or not data["content"]:
            result["errors"].append("Missing required field: content")
            result["valid"] = False
        elif not validate_content_length(data["content"], 1, 5000):
            result["errors"].append("Content must be 1-5000 characters")
            result["valid"] = False
        else:
            result["sanitized_data"]["content"] = sanitize_input(data["content"])
        
        # Validate optional fields
        if "importance_score" in data:
            if not validate_importance_score(data["importance_score"]):
                result["errors"].append("Importance score must be between 0.0 and 1.0")
                result["valid"] = False
            else:
                result["sanitized_data"]["importance_score"] = float(data["importance_score"])
        
        if "tags" in data and data["tags"]:
            if not isinstance(data["tags"], list):
                result["errors"].append("Tags must be a list")
                result["valid"] = False
            else:
                sanitized_tags = []
                for tag in data["tags"]:
                    if isinstance(tag, str):
                        sanitized_tag = sanitize_input(tag).lower()
                        if sanitized_tag and len(sanitized_tag) <= 50:
                            sanitized_tags.append(sanitized_tag)
                result["sanitized_data"]["tags"] = sanitized_tags
        
        if "user_editable" in data:
            if not isinstance(data["user_editable"], bool):
                result["errors"].append("user_editable must be a boolean")
                result["valid"] = False
            else:
                result["sanitized_data"]["user_editable"] = data["user_editable"]
        
        return result