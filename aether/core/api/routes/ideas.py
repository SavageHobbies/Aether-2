"""
Ideas routes for Aether AI Companion API.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from uuid import UUID

from core.database.connection import get_database
from core.database.models import IdeaModel
from shared.schemas.idea import IdeaResponse
from shared.serialization import ModelSerializer
from ..auth import get_current_user, require_read, require_write
from ..middleware import rate_limit_moderate

router = APIRouter()


class IdeaCreate(BaseModel):
    """Request model for creating ideas."""
    content: str = Field(..., min_length=1, max_length=5000)
    source: str = Field(..., regex=r'^(desktop|mobile|voice|web)$')
    category: Optional[str] = None
    priority_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    extra_metadata: Optional[dict] = None


class IdeaUpdate(BaseModel):
    """Request model for updating ideas."""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    category: Optional[str] = None
    priority_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    processed: Optional[bool] = None
    extra_metadata: Optional[dict] = None


@router.post("/", response_model=IdeaResponse)
@rate_limit_moderate("100/minute")
async def create_idea(
    idea: IdeaCreate,
    current_user: dict = Depends(require_write)
):
    """
    Create a new idea entry.
    
    Args:
        idea: Idea data
        current_user: Current authenticated user
    
    Returns:
        Created idea
    """
    session = get_database()
    try:
        db_idea = IdeaModel(
            content=idea.content,
            source=idea.source,
            category=idea.category,
            priority_score=idea.priority_score or 0.5,
            extra_metadata=idea.extra_metadata or {}
        )
        
        session.add(db_idea)
        session.commit()
        session.refresh(db_idea)
        
        return ModelSerializer.serialize_idea(db_idea)
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create idea: {str(e)}"
        )
    finally:
        session.close()


@router.get("/", response_model=List[IdeaResponse])
@rate_limit_moderate()
async def get_ideas(
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_read)
):
    """Get ideas with optional filtering."""
    session = get_database()
    try:
        query = session.query(IdeaModel)
        
        if processed is not None:
            query = query.filter(IdeaModel.processed == processed)
        if source:
            query = query.filter(IdeaModel.source == source)
        if category:
            query = query.filter(IdeaModel.category == category)
        
        ideas = (
            query.order_by(IdeaModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return [ModelSerializer.serialize_idea(idea) for idea in ideas]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ideas: {str(e)}"
        )
    finally:
        session.close()


@router.get("/{idea_id}", response_model=IdeaResponse)
@rate_limit_moderate()
async def get_idea(
    idea_id: UUID,
    current_user: dict = Depends(require_read)
):
    """Get a specific idea by ID."""
    session = get_database()
    try:
        idea = session.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
        
        if not idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )
        
        return ModelSerializer.serialize_idea(idea)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get idea: {str(e)}"
        )
    finally:
        session.close()


@router.put("/{idea_id}", response_model=IdeaResponse)
@rate_limit_moderate("50/minute")
async def update_idea(
    idea_id: UUID,
    update_data: IdeaUpdate,
    current_user: dict = Depends(require_write)
):
    """Update an idea."""
    session = get_database()
    try:
        idea = session.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
        
        if not idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )
        
        # Update fields if provided
        if update_data.content is not None:
            idea.content = update_data.content
        if update_data.category is not None:
            idea.category = update_data.category
        if update_data.priority_score is not None:
            idea.priority_score = update_data.priority_score
        if update_data.processed is not None:
            idea.processed = update_data.processed
        if update_data.extra_metadata is not None:
            idea.extra_metadata = update_data.extra_metadata
        
        session.commit()
        session.refresh(idea)
        
        return ModelSerializer.serialize_idea(idea)
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update idea: {str(e)}"
        )
    finally:
        session.close()


@router.delete("/{idea_id}")
@rate_limit_moderate("30/minute")
async def delete_idea(
    idea_id: UUID,
    current_user: dict = Depends(require_write)
):
    """Delete an idea."""
    session = get_database()
    try:
        idea = session.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
        
        if not idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )
        
        session.delete(idea)
        session.commit()
        
        return {
            "message": "Idea deleted successfully",
            "idea_id": str(idea_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete idea: {str(e)}"
        )
    finally:
        session.close()