"""
Input validation utilities for Aether AI Companion.
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


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format (basic validation).
    
    Args:
        api_key: API key to validate
    
    Returns:
        True if valid format, False otherwise
    """
    if not isinstance(api_key, str):
        return False
    
    # Basic validation: should be alphanumeric with some special chars
    # and reasonable length
    if len(api_key) < 10 or len(api_key) > 200:
        return False
    
    # Should contain only safe characters
    safe_pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(safe_pattern, api_key))


def validate_json(json_string: str) -> bool:
    """
    Validate JSON string format.
    
    Args:
        json_string: String to validate as JSON
    
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(json_string)
        return True
    except (ValueError, TypeError):
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid URL, False otherwise
    """
    url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return bool(re.match(url_pattern, url))


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format (basic international format).
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid phone number, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Should be 7-15 digits
    if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
        return False
    
    return True


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "score": 0,
        "issues": []
    }
    
    if len(password) < 8:
        result["issues"].append("Password must be at least 8 characters long")
        result["valid"] = False
    else:
        result["score"] += 1
    
    if not re.search(r'[a-z]', password):
        result["issues"].append("Password must contain lowercase letters")
        result["valid"] = False
    else:
        result["score"] += 1
    
    if not re.search(r'[A-Z]', password):
        result["issues"].append("Password must contain uppercase letters")
        result["valid"] = False
    else:
        result["score"] += 1
    
    if not re.search(r'\d', password):
        result["issues"].append("Password must contain numbers")
        result["valid"] = False
    else:
        result["score"] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["issues"].append("Password must contain special characters")
        result["valid"] = False
    else:
        result["score"] += 1
    
    return result


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.txt', '.pdf'])
    
    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    
    extension = '.' + filename.split('.')[-1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]


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


def validate_tags(tags: List[str], max_tags: int = 20, max_tag_length: int = 50) -> Dict[str, Any]:
    """
    Validate tags list.
    
    Args:
        tags: List of tags to validate
        max_tags: Maximum number of tags
        max_tag_length: Maximum length per tag
    
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "issues": [],
        "sanitized_tags": []
    }
    
    if not isinstance(tags, list):
        result["issues"].append("Tags must be a list")
        result["valid"] = False
        return result
    
    if len(tags) > max_tags:
        result["issues"].append(f"Too many tags (maximum {max_tags})")
        result["valid"] = False
    
    seen_tags = set()
    for tag in tags:
        if not isinstance(tag, str):
            result["issues"].append("All tags must be strings")
            result["valid"] = False
            continue
        
        sanitized_tag = sanitize_input(tag).lower()
        
        if not sanitized_tag:
            result["issues"].append("Empty tags are not allowed")
            result["valid"] = False
            continue
        
        if len(sanitized_tag) > max_tag_length:
            result["issues"].append(f"Tag '{sanitized_tag}' is too long (maximum {max_tag_length} characters)")
            result["valid"] = False
            continue
        
        if sanitized_tag in seen_tags:
            continue  # Skip duplicates
        
        seen_tags.add(sanitized_tag)
        result["sanitized_tags"].append(sanitized_tag)
    
    return result


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


def validate_datetime_string(datetime_string: str) -> bool:
    """
    Validate datetime string in ISO format.
    
    Args:
        datetime_string: Datetime string to validate
    
    Returns:
        True if valid datetime, False otherwise
    """
    if not isinstance(datetime_string, str):
        return False
    
    # Try common datetime formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO with microseconds and Z
        "%Y-%m-%dT%H:%M:%SZ",     # ISO with Z
        "%Y-%m-%dT%H:%M:%S.%f",   # ISO with microseconds
        "%Y-%m-%dT%H:%M:%S",      # ISO basic
        "%Y-%m-%d %H:%M:%S",      # SQL format
        "%Y-%m-%d",               # Date only
    ]
    
    for fmt in formats:
        try:
            datetime.strptime(datetime_string, fmt)
            return True
        except ValueError:
            continue
    
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


class InputValidator:
    """Comprehensive input validator for all data types."""
    
    @staticmethod
    def validate_conversation_input(data: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Validate context_metadata
        if "context_metadata" in data:
            if not isinstance(data["context_metadata"], dict):
                result["errors"].append("context_metadata must be a dictionary")
                result["valid"] = False
            else:
                result["sanitized_data"]["context_metadata"] = data["context_metadata"]
        
        return result
    
    @staticmethod
    def validate_idea_input(data: Dict[str, Any]) -> Dict[str, Any]:
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
    def validate_task_input(data: Dict[str, Any]) -> Dict[str, Any]:
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
        
        if "due_date" in data and data["due_date"]:
            if not validate_datetime_string(data["due_date"]):
                result["errors"].append("Invalid due_date format")
                result["valid"] = False
            else:
                result["sanitized_data"]["due_date"] = data["due_date"]
        
        return result
    
    @staticmethod
    def validate_memory_input(data: Dict[str, Any]) -> Dict[str, Any]:
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
            tag_validation = validate_tags(data["tags"])
            if not tag_validation["valid"]:
                result["errors"].extend(tag_validation["issues"])
                result["valid"] = False
            else:
                result["sanitized_data"]["tags"] = tag_validation["sanitized_tags"]
        
        if "user_editable" in data:
            if not isinstance(data["user_editable"], bool):
                result["errors"].append("user_editable must be a boolean")
                result["valid"] = False
            else:
                result["sanitized_data"]["user_editable"] = data["user_editable"]
        
        return result