"""
Tasks routes for Aether AI Companion API.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from core.database.connection import get_database
from core.database.models import TaskModel
from shared.schemas.task import TaskResponse
from shared.serialization import ModelSerializer
from ..auth import get_current_user, require_read, require_write
from ..middleware import rate_limit_moderate

router = APIRouter()


class TaskCreate(BaseModel):
    """Request model for creating tasks."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: int = Field(..., ge=1, le=4)
    status: str = Field(default="pending")
    due_date: Optional[datetime] = None
    source_conversation_id: Optional[UUID] = None
    source_idea_id: Optional[UUID] = None
    external_integrations: Optional[dict] = None


class TaskUpdate(BaseModel):
    """Request model for updating tasks."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[int] = Field(None, ge=1, le=4)
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    external_integrations: Optional[dict] = None


@router.post("/", response_model=TaskResponse)
@rate_limit_moderate("50/minute")
async def create_task(
    task: TaskCreate,
    current_user: dict = Depends(require_write)
):
    """Create a new task."""
    session = get_database()
    try:
        db_task = TaskModel(
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            due_date=task.due_date,
            source_conversation_id=task.source_conversation_id,
            source_idea_id=task.source_idea_id,
            external_integrations=task.external_integrations or {}
        )
        
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        
        return ModelSerializer.serialize_task(db_task)
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )
    finally:
        session.close()


@router.get("/", response_model=List[TaskResponse])
@rate_limit_moderate()
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, ge=1, le=4, description="Filter by priority"),
    overdue: Optional[bool] = Query(None, description="Filter overdue tasks"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_read)
):
    """Get tasks with optional filtering."""
    session = get_database()
    try:
        query = session.query(TaskModel)
        
        if status:
            query = query.filter(TaskModel.status == status)
        if priority:
            query = query.filter(TaskModel.priority == priority)
        if overdue is not None:
            now = datetime.utcnow()
            if overdue:
                query = query.filter(TaskModel.due_date < now)
            else:
                query = query.filter(TaskModel.due_date >= now)
        
        tasks = (
            query.order_by(TaskModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return [ModelSerializer.serialize_task(task) for task in tasks]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )
    finally:
        session.close()


@router.get("/{task_id}", response_model=TaskResponse)
@rate_limit_moderate()
async def get_task(
    task_id: UUID,
    current_user: dict = Depends(require_read)
):
    """Get a specific task by ID."""
    session = get_database()
    try:
        task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return ModelSerializer.serialize_task(task)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )
    finally:
        session.close()


@router.put("/{task_id}", response_model=TaskResponse)
@rate_limit_moderate("30/minute")
async def update_task(
    task_id: UUID,
    update_data: TaskUpdate,
    current_user: dict = Depends(require_write)
):
    """Update a task."""
    session = get_database()
    try:
        task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update fields if provided
        if update_data.title is not None:
            task.title = update_data.title
        if update_data.description is not None:
            task.description = update_data.description
        if update_data.priority is not None:
            task.priority = update_data.priority
        if update_data.status is not None:
            task.status = update_data.status
        if update_data.due_date is not None:
            task.due_date = update_data.due_date
        if update_data.external_integrations is not None:
            task.external_integrations = update_data.external_integrations
        
        session.commit()
        session.refresh(task)
        
        return ModelSerializer.serialize_task(task)
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )
    finally:
        session.close()


@router.delete("/{task_id}")
@rate_limit_moderate("20/minute")
async def delete_task(
    task_id: UUID,
    current_user: dict = Depends(require_write)
):
    """Delete a task."""
    session = get_database()
    try:
        task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        session.delete(task)
        session.commit()
        
        return {
            "message": "Task deleted successfully",
            "task_id": str(task_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )
    finally:
        session.close()