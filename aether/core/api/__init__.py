"""
API module for Aether AI Companion.
"""

from .gateway import create_app, APIGateway
from .auth import AuthManager, JWTAuth
from .middleware import setup_middleware
from .routes import setup_routes

__all__ = [
    'create_app',
    'APIGateway', 
    'AuthManager',
    'JWTAuth',
    'setup_middleware',
    'setup_routes'
]