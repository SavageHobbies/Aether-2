"""
Configuration management for Aether AI Companion.
"""

import os
from pathlib import Path
from typing import Optional


class AppSettings:
    """Main application configuration."""
    
    def __init__(self):
        self.name = "Aether AI Companion"
        self.version = "0.1.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.host = os.getenv("HOST", "localhost")
        self.port = int(os.getenv("PORT", "8000"))
        
        # Security settings
        self.secret_key = os.getenv("SECRET_KEY", "aether-secret-key-change-in-production")
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        self.allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else None
        
        # Data directory
        data_dir_str = os.getenv("AETHER_DATA_DIR", str(Path.home() / ".aether"))
        self.data_dir = Path(data_dir_str)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database settings
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///aether.db")
        self.database_echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"


# Global settings instance
settings = AppSettings()


def get_settings() -> AppSettings:
    """Get application settings."""
    return settings


def load_env_file(env_file: str = ".env"):
    """Load environment variables from file."""
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)