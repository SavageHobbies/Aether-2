"""
Logging utilities for Aether AI Companion.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# from aether.shared.config.settings import get_settings


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        format_string: Custom format string for log messages
    
    Returns:
        Configured logger instance
    """
    # settings = get_settings()
    
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set up application logger
    app_logger = logging.getLogger("aether")
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"aether.{name}")


class PrivacyFilter(logging.Filter):
    """
    Logging filter to remove sensitive information from logs.
    """
    
    SENSITIVE_FIELDS = [
        "password", "token", "key", "secret", "api_key",
        "client_secret", "auth", "credential"
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to remove sensitive information.
        
        Args:
            record: Log record to filter
        
        Returns:
            True if record should be logged, False otherwise
        """
        # Check if message contains sensitive information
        message = str(record.getMessage()).lower()
        
        for field in self.SENSITIVE_FIELDS:
            if field in message:
                # Replace sensitive content with placeholder
                record.msg = str(record.msg).replace(
                    record.args[0] if record.args else "",
                    "[REDACTED]"
                )
                break
        
        return True


def setup_privacy_logging():
    """Set up privacy-compliant logging with sensitive data filtering."""
    privacy_filter = PrivacyFilter()
    
    # Add privacy filter to all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(privacy_filter)