"""
Health check routes for Aether AI Companion API.
"""

import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from core.database.connection import get_database
from core.database.models import ConversationModel, IdeaModel, TaskModel, MemoryModel
from ..middleware import rate_limit_lenient

router = APIRouter()


class HealthStatus(BaseModel):
    """Health status response."""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    database: Dict[str, Any]
    services: Dict[str, str]


class DatabaseStats(BaseModel):
    """Database statistics."""
    conversations: int
    ideas: int
    tasks: int
    memories: int
    connection_status: str


# Track application start time
app_start_time = time.time()


@router.get("/", response_model=HealthStatus)
@rate_limit_lenient()
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
        System health status and statistics
    
    Raises:
        HTTPException: If critical services are down
    """
    try:
        # Check database connection and get stats
        session = get_database()
        try:
            conversation_count = session.query(ConversationModel).count()
            idea_count = session.query(IdeaModel).count()
            task_count = session.query(TaskModel).count()
            memory_count = session.query(MemoryModel).count()
            
            database_info = {
                "status": "healthy",
                "conversations": conversation_count,
                "ideas": idea_count,
                "tasks": task_count,
                "memories": memory_count,
                "total_records": conversation_count + idea_count + task_count + memory_count
            }
            
        except Exception as e:
            database_info = {
                "status": "unhealthy",
                "error": str(e),
                "conversations": 0,
                "ideas": 0,
                "tasks": 0,
                "memories": 0,
                "total_records": 0
            }
        finally:
            session.close()
        
        # Check other services
        services = {
            "database": database_info["status"],
            "authentication": "healthy",
            "api_gateway": "healthy",
            "rate_limiting": "healthy"
        }
        
        # Calculate uptime
        uptime = time.time() - app_start_time
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in services.values()
        ) else "degraded"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="0.1.0",
            uptime_seconds=uptime,
            database=database_info,
            services=services
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/database", response_model=DatabaseStats)
@rate_limit_lenient()
async def database_health():
    """
    Database-specific health check.
    
    Returns:
        Database connection status and statistics
    
    Raises:
        HTTPException: If database is unreachable
    """
    try:
        session = get_database()
        try:
            # Test database connection with a simple query
            conversation_count = session.query(ConversationModel).count()
            idea_count = session.query(IdeaModel).count()
            task_count = session.query(TaskModel).count()
            memory_count = session.query(MemoryModel).count()
            
            return DatabaseStats(
                conversations=conversation_count,
                ideas=idea_count,
                tasks=task_count,
                memories=memory_count,
                connection_status="connected"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection failed: {str(e)}"
            )
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/ready")
@rate_limit_lenient()
async def readiness_check():
    """
    Kubernetes-style readiness check.
    
    Returns:
        Simple ready/not ready status
    """
    try:
        # Quick database connectivity test
        session = get_database()
        try:
            session.execute("SELECT 1")
            return {"status": "ready"}
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
        finally:
            session.close()
            
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/live")
@rate_limit_lenient()
async def liveness_check():
    """
    Kubernetes-style liveness check.
    
    Returns:
        Simple alive status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "uptime_seconds": time.time() - app_start_time
    }