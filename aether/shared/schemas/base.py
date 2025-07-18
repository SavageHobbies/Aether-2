"""
Base schemas and validation utilities for Aether AI Companion.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4


class ValidationError(Exception):
    """Custom validation error with field information."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)
    
    def __str__(self):
        if self.field:
            return f"Validation error in field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class BaseSchema:
    """Base schema class with common validation methods."""
    
    @staticmethod
    def validate_uuid(value: Union[str, UUID], field_name: str = "id") -> str:
        """
        Validate UUID format.
        
        Args:
            value: UUID value to validate
            field_name: Field name for error reporting
        
        Returns:
            String representation of UUID
        
        Raises:
            ValidationError: If UUID is invalid
        """
        if value is None:
            raise ValidationError("UUID cannot be None", field_name, value)
        
        try:
            if isinstance(value, UUID):
                return str(value)
            
            # Try to parse as UUID
            uuid_obj = UUID(str(value))
            return str(uuid_obj)
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid UUID format: {e}", field_name, value)
    
    @staticmethod
    def validate_string(
        value: Any, 
        field_name: str,
        min_length: int = 0,
        max_length: Optional[int] = None,
        allow_empty: bool = True,
        pattern: Optional[str] = None
    ) -> str:
        """
        Validate string field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
            min_length: Minimum string length
            max_length: Maximum string length
            allow_empty: Whether to allow empty strings
            pattern: Regex pattern to match
        
        Returns:
            Validated string
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError("String cannot be None", field_name, value)
        
        if not isinstance(value, str):
            value = str(value)
        
        # Check empty string
        if not allow_empty and not value.strip():
            raise ValidationError("String cannot be empty", field_name, value)
        
        # Check length
        if len(value) < min_length:
            raise ValidationError(
                f"String must be at least {min_length} characters long",
                field_name, value
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"String must be at most {max_length} characters long",
                field_name, value
            )
        
        # Check pattern
        if pattern and not re.match(pattern, value):
            raise ValidationError(
                f"String does not match required pattern: {pattern}",
                field_name, value
            )
        
        return value
    
    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> int:
        """
        Validate integer field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            Validated integer
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError("Integer cannot be None", field_name, value)
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Value must be an integer", field_name, value)
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"Integer must be at least {min_value}",
                field_name, value
            )
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"Integer must be at most {max_value}",
                field_name, value
            )
        
        return int_value
    
    @staticmethod
    def validate_float(
        value: Any,
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> float:
        """
        Validate float field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            Validated float
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError("Float cannot be None", field_name, value)
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError("Value must be a number", field_name, value)
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(
                f"Number must be at least {min_value}",
                field_name, value
            )
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(
                f"Number must be at most {max_value}",
                field_name, value
            )
        
        return float_value
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str) -> bool:
        """
        Validate boolean field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
        
        Returns:
            Validated boolean
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError("Boolean cannot be None", field_name, value)
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ("true", "1", "yes", "on"):
                return True
            elif lower_value in ("false", "0", "no", "off"):
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValidationError("Value must be a boolean", field_name, value)
    
    @staticmethod
    def validate_datetime(
        value: Any, 
        field_name: str,
        allow_none: bool = True
    ) -> Optional[datetime]:
        """
        Validate datetime field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
            allow_none: Whether to allow None values
        
        Returns:
            Validated datetime or None
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_none:
                return None
            raise ValidationError("Datetime cannot be None", field_name, value)
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
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
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        
        raise ValidationError("Invalid datetime format", field_name, value)
    
    @staticmethod
    def validate_list(
        value: Any,
        field_name: str,
        item_validator: Optional[callable] = None,
        min_length: int = 0,
        max_length: Optional[int] = None,
        allow_none: bool = True
    ) -> Optional[List[Any]]:
        """
        Validate list field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
            item_validator: Function to validate each item
            min_length: Minimum list length
            max_length: Maximum list length
            allow_none: Whether to allow None values
        
        Returns:
            Validated list or None
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_none:
                return None
            raise ValidationError("List cannot be None", field_name, value)
        
        if not isinstance(value, list):
            raise ValidationError("Value must be a list", field_name, value)
        
        if len(value) < min_length:
            raise ValidationError(
                f"List must have at least {min_length} items",
                field_name, value
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"List must have at most {max_length} items",
                field_name, value
            )
        
        # Validate each item if validator provided
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = item_validator(item)
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(
                        f"Item {i}: {e.message}",
                        f"{field_name}[{i}]", item
                    )
            return validated_items
        
        return value
    
    @staticmethod
    def validate_dict(
        value: Any,
        field_name: str,
        allow_none: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Validate dictionary field.
        
        Args:
            value: Value to validate
            field_name: Field name for error reporting
            allow_none: Whether to allow None values
        
        Returns:
            Validated dictionary or None
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_none:
                return None
            raise ValidationError("Dictionary cannot be None", field_name, value)
        
        if not isinstance(value, dict):
            raise ValidationError("Value must be a dictionary", field_name, value)
        
        return value
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text input for security.
        
        Args:
            text: Text to sanitize
        
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
        sanitized = text
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert schema to dictionary.
        
        Returns:
            Dictionary representation
        """
        result = {}
        
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                value = getattr(self, attr_name)
                
                # Convert datetime to ISO string
                if isinstance(value, datetime):
                    result[attr_name] = value.isoformat()
                # Convert UUID to string
                elif isinstance(value, UUID):
                    result[attr_name] = str(value)
                # Keep other values as-is
                else:
                    result[attr_name] = value
        
        return result
    
    def to_json(self) -> str:
        """
        Convert schema to JSON string.
        
        Returns:
            JSON representation
        """
        import json
        return json.dumps(self.to_dict(), default=str, indent=2)