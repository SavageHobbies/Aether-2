"""
API routes for Aether AI Companion.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .conversations import router as conversations_router
from .ideas import router as ideas_router
from .tasks import router as tasks_router
from .memory import router as memory_router
from .health import router as health_router


def setup_routes() -> APIRouter:
    """
    Set up all API routes.
    
    Returns:
        Main API router with all sub-routes
    """
    api_router = APIRouter(prefix="/api/v1")
    
    # Include all route modules
    api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    api_router.include_router(health_router, prefix="/health", tags=["Health"])
    api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
    api_router.include_router(ideas_router, prefix="/ideas", tags=["Ideas"])
    api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
    api_router.include_router(memory_router, prefix="/memory", tags=["Memory"])
    
    return api_router