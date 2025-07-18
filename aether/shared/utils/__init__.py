"""
Utility functions for Aether AI Companion.
"""

from .logging import get_logger, setup_logging, setup_privacy_logging
from .simple_validation import (
    ValidationError,
    sanitize_input,
    validate_email,
    validate_uuid,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "setup_privacy_logging",
    "ValidationError",
    "sanitize_input",
    "validate_email",
    "validate_uuid",
]