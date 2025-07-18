"""
Conversation routes for Aether AI Companion API.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from core.database.connection import get_database
from core.database.models import ConversationModel
from shared.schemas.conversation import ConversationResponse
from shared.serialization import ModelSerializer
from ..auth import get_current_user, require_read, require_write
from ..middleware import rate_limit_moderate

router = APIRouter()


class ConversationCreate(BaseModel):
    """Request model for creating conversations."""
    session_id: Optional[str] = None
    user_input: str = Field(..., min_length=1, max_length=10000)
    ai_response: str = Field(..., min_length=1, max_length=10000)
    context_metadata: Optional[dict] = None


class ConversationUpdate(BaseModel):
    """Request model for updating conversations."""
    ai_response: Optional[str] = Field(None, max_length=10000)
    context_metadata: Optional[dict] = None


@router.post("/", response_model=ConversationResponse)
@rate_limit_moderate("50/minute")
async def create_conversation(
    conversation: ConversationCreate,
    current_user: dict = Depends(require_write)
):
    """
    Create a new conversation entry.
    
    Args:
        conversation: Conversation data
        current_user: Current authenticated user
    
    Returns:
        Created conversation
    
    Raises:
        HTTPException: If creation fails
    """
    session = get_database()
    try:
        # Generate session ID if not provided
        session_id = conversation.session_id or str(uuid4())
        
        # Create conversation model
        db_conversation = ConversationModel(
            session_id=session_id,
            user_input=conversation.user_input,
            ai_response=conversation.ai_response,
            context_metadata=conversation.context_metadata or {}
        )
        
        session.add(db_conversation)
        session.commit()
        session.refresh(db_conversation)
        
        # Serialize and return
        return ModelSerializer.serialize_conversation(db_conversation)
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )
    finally:
        session.close()


@router.get("/", response_model=List[ConversationResponse])
@rate_limit_moderate()
async def get_conversations(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    current_user: dict = Depends(require_read)
):
    """
    Get conversations with optional filtering.
    
    Args:
        session_id: Optional session ID filter
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user
    
    Returns:
        List of conversations
    
    Raises:
        HTTPException: If query fails
    """
    session = get_database()
    try:
        query = session.query(ConversationModel)
        
        # Apply session filter if provided
        if session_id:
            query = query.filter(ConversationModel.session_id == session_id)
        
        # Apply pagination and ordering
        conversations = (
            query.order_by(ConversationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Serialize results
        return [
            ModelSerializer.serialize_conversation(conv)
            for conv in conversations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )
    finally:
        session.close()


@router.get("/{conversation_id}", response_model=ConversationResponse)
@rate_limit_moderate()
async def get_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(require_read)
):
    """
    Get a specific conversation by ID.
    
    Args:
        conversation_id: Conversation identifier
        current_user: Current authenticated user
    
    Returns:
        Conversation data
    
    Raises:
        HTTPException: If conversation not found
    """
    session = get_database()
    try:
        conversation = session.query(ConversationModel).filter(
            ConversationModel.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return ModelSerializer.serialize_conversation(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )
    finally:
        session.close()


@router.put("/{conversation_id}", response_model=ConversationResponse)
@rate_limit_moderate("30/minute")
async def update_conversation(
    conversation_id: UUID,
    update_data: ConversationUpdate,
    current_user: dict = Depends(require_write)
):
    """
    Update a conversation.
    
    Args:
        conversation_id: Conversation identifier
        update_data: Updated conversation data
        current_user: Current authenticated user
    
    Returns:
        Updated conversation
    
    Raises:
        HTTPException: If conversation not found or update fails
    """
    session = get_database()
    try:
        conversation = session.query(ConversationModel).filter(
            ConversationModel.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Update fields if provided
        if update_data.ai_response is not None:
            conversation.ai_response = update_data.ai_response
        
        if update_data.context_metadata is not None:
            conversation.context_metadata = update_data.context_metadata
        
        session.commit()
        session.refresh(conversation)
        
        return ModelSerializer.serialize_conversation(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )
    finally:
        session.close()


@router.delete("/{conversation_id}")
@rate_limit_moderate("20/minute")
async def delete_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(require_write)
):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation identifier
        current_user: Current authenticated user
    
    Returns:
        Deletion confirmation
    
    Raises:
        HTTPException: If conversation not found or deletion fails
    """
    session = get_database()
    try:
        conversation = session.query(ConversationModel).filter(
            ConversationModel.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        session.delete(conversation)
        session.commit()
        
        return {
            "message": "Conversation deleted successfully",
            "conversation_id": str(conversation_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )
    finally:
        session.close()


@router.get("/sessions/{session_id}/summary")
@rate_limit_moderate()
async def get_session_summary(
    session_id: str,
    current_user: dict = Depends(require_read)
):
    """
    Get summary statistics for a conversation session.
    
    Args:
        session_id: Session identifier
        current_user: Current authenticated user
    
    Returns:
        Session summary statistics
    """
    session = get_database()
    try:
        conversations = session.query(ConversationModel).filter(
            ConversationModel.session_id == session_id
        ).all()
        
        if not conversations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Calculate summary statistics
        total_conversations = len(conversations)
        total_user_chars = sum(len(conv.user_input) for conv in conversations)
        total_ai_chars = sum(len(conv.ai_response) for conv in conversations)
        
        first_conversation = min(conversations, key=lambda c: c.created_at)
        last_conversation = max(conversations, key=lambda c: c.created_at)
        
        return {
            "session_id": session_id,
            "total_conversations": total_conversations,
            "total_user_characters": total_user_chars,
            "total_ai_characters": total_ai_chars,
            "session_start": first_conversation.created_at,
            "session_end": last_conversation.created_at,
            "duration_minutes": (
                last_conversation.created_at - first_conversation.created_at
            ).total_seconds() / 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session summary: {str(e)}"
        )
    finally:
        session.close()