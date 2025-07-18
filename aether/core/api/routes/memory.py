"""
Memory routes for Aether AI Companion API.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from uuid import UUID

from core.database.connection import get_database
from core.database.models import MemoryModel
from shared.schemas.memory import MemoryEntryResponse
from shared.serialization import ModelSerializer
from ..auth import get_current_user, require_read, require_write
from ..middleware import rate_limit_moderate

router = APIRouter()


class MemoryCreate(BaseModel):
    """Request model for creating memory entries."""
    content: str = Field(..., min_length=1, max_length=5000)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    user_editable: bool = Field(default=True)


class MemoryUpdate(BaseModel):
    """Request model for updating memory entries."""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    user_editable: Optional[bool] = None


class MemorySearchRequest(BaseModel):
    """Request model for memory search."""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)


@router.post("/", response_model=MemoryEntryResponse)
@rate_limit_moderate("30/minute")
async def create_memory(
    memory: MemoryCreate,
    current_user: dict = Depends(require_write)
):
    """Create a new memory entry."""
    session = get_database()
    try:
        db_memory = MemoryModel(
            content=memory.content,
            importance_score=memory.importance_score,
            tags=memory.tags or [],
            user_editable=memory.user_editable
        )
        
        session.add(db_memory)
        session.commit()
        session.refresh(db_memory)
        
        return ModelSerializer.serialize_memory_entry(db_memory)
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create memory: {str(e)}"
        )
    finally:
        session.close()


@router.get("/", response_model=List[MemoryEntryResponse])
@rate_limit_moderate()
async def get_memories(
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    min_importance: Optional[float] = Query(None, ge=0.0, le=1.0),
    user_editable: Optional[bool] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_read)
):
    """Get memory entries with optional filtering."""
    session = get_database()
    try:
        query = session.query(MemoryModel)
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            # Filter memories that contain any of the specified tags
            for tag in tag_list:
                query = query.filter(MemoryModel.tags.contains([tag]))
        
        if min_importance is not None:
            query = query.filter(MemoryModel.importance_score >= min_importance)
        
        if user_editable is not None:
            query = query.filter(MemoryModel.user_editable == user_editable)
        
        memories = (
            query.order_by(MemoryModel.importance_score.desc(), MemoryModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return [ModelSerializer.serialize_memory_entry(memory) for memory in memories]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memories: {str(e)}"
        )
    finally:
        session.close()


@router.get("/{memory_id}", response_model=MemoryEntryResponse)
@rate_limit_moderate()
async def get_memory(
    memory_id: UUID,
    current_user: dict = Depends(require_read)
):
    """Get a specific memory entry by ID."""
    session = get_database()
    try:
        memory = session.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return ModelSerializer.serialize_memory_entry(memory)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory: {str(e)}"
        )
    finally:
        session.close()


@router.put("/{memory_id}", response_model=MemoryEntryResponse)
@rate_limit_moderate("20/minute")
async def update_memory(
    memory_id: UUID,
    update_data: MemoryUpdate,
    current_user: dict = Depends(require_write)
):
    """Update a memory entry."""
    session = get_database()
    try:
        memory = session.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        # Check if memory is user-editable
        if not memory.user_editable:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This memory entry is not user-editable"
            )
        
        # Update fields if provided
        if update_data.content is not None:
            memory.content = update_data.content
        if update_data.importance_score is not None:
            memory.importance_score = update_data.importance_score
        if update_data.tags is not None:
            memory.tags = update_data.tags
        if update_data.user_editable is not None:
            memory.user_editable = update_data.user_editable
        
        session.commit()
        session.refresh(memory)
        
        return ModelSerializer.serialize_memory_entry(memory)
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update memory: {str(e)}"
        )
    finally:
        session.close()


@router.delete("/{memory_id}")
@rate_limit_moderate("10/minute")
async def delete_memory(
    memory_id: UUID,
    current_user: dict = Depends(require_write)
):
    """Delete a memory entry."""
    session = get_database()
    try:
        memory = session.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        # Check if memory is user-editable
        if not memory.user_editable:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This memory entry cannot be deleted"
            )
        
        session.delete(memory)
        session.commit()
        
        return {
            "message": "Memory deleted successfully",
            "memory_id": str(memory_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete memory: {str(e)}"
        )
    finally:
        session.close()


@router.post("/search", response_model=List[MemoryEntryResponse])
@rate_limit_moderate("50/minute")
async def search_memories(
    search_request: MemorySearchRequest,
    current_user: dict = Depends(require_read)
):
    """
    Search memory entries using semantic similarity.
    
    Note: This is a simplified implementation. In production,
    this would use vector similarity search with embeddings.
    """
    session = get_database()
    try:
        # Simple text-based search for now
        # In production, this would use vector embeddings and similarity search
        query_terms = search_request.query.lower().split()
        
        memories = session.query(MemoryModel).all()
        
        # Score memories based on term matches
        scored_memories = []
        for memory in memories:
            content_lower = memory.content.lower()
            score = sum(1 for term in query_terms if term in content_lower)
            
            # Include tag matches
            if memory.tags:
                tag_matches = sum(1 for tag in memory.tags if any(term in tag.lower() for term in query_terms))
                score += tag_matches * 2  # Weight tag matches higher
            
            # Normalize score and combine with importance
            normalized_score = score / len(query_terms) if query_terms else 0
            final_score = (normalized_score * 0.7) + (memory.importance_score * 0.3)
            
            if final_score >= search_request.threshold:
                scored_memories.append((memory, final_score))
        
        # Sort by score and limit results
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        top_memories = [memory for memory, score in scored_memories[:search_request.limit]]
        
        return [ModelSerializer.serialize_memory_entry(memory) for memory in top_memories]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memories: {str(e)}"
        )
    finally:
        session.close()