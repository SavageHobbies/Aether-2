"""
Simple test server to verify Aether components work together.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from shared.config.settings import AppSettings
from core.database.connection import init_database, get_database
from core.database.migrations import init_database_schema
from core.database.models import ConversationModel, MemoryModel, IdeaModel, TaskModel

# Initialize settings and database
settings = AppSettings()
init_database(settings)
init_database_schema()

# Create FastAPI app
app = FastAPI(title="Aether AI Companion", version="0.1.0")

# Pydantic models for API
class ConversationCreate(BaseModel):
    session_id: str
    user_input: str
    ai_response: str

class ConversationResponse(BaseModel):
    id: str
    session_id: str
    user_input: str
    ai_response: str
    created_at: str

class IdeaCreate(BaseModel):
    content: str
    source: str = "web"

class IdeaResponse(BaseModel):
    id: str
    content: str
    source: str
    processed: bool
    created_at: str

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Aether AI Companion API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    session = get_database()
    try:
        # Test database connection
        conversation_count = session.query(ConversationModel).count()
        memory_count = session.query(MemoryModel).count()
        idea_count = session.query(IdeaModel).count()
        task_count = session.query(TaskModel).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "stats": {
                "conversations": conversation_count,
                "memories": memory_count,
                "ideas": idea_count,
                "tasks": task_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        session.close()

@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation."""
    session = get_database()
    try:
        db_conversation = ConversationModel(
            session_id=conversation.session_id,
            user_input=conversation.user_input,
            ai_response=conversation.ai_response
        )
        
        session.add(db_conversation)
        session.commit()
        session.refresh(db_conversation)
        
        return ConversationResponse(
            id=str(db_conversation.id),
            session_id=db_conversation.session_id,
            user_input=db_conversation.user_input,
            ai_response=db_conversation.ai_response,
            created_at=db_conversation.created_at.isoformat()
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")
    finally:
        session.close()

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(session_id: Optional[str] = None, limit: int = 10):
    """Get conversations."""
    session = get_database()
    try:
        query = session.query(ConversationModel)
        
        if session_id:
            query = query.filter(ConversationModel.session_id == session_id)
        
        conversations = query.order_by(ConversationModel.created_at.desc()).limit(limit).all()
        
        return [
            ConversationResponse(
                id=str(conv.id),
                session_id=conv.session_id,
                user_input=conv.user_input,
                ai_response=conv.ai_response,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")
    finally:
        session.close()

@app.post("/ideas", response_model=IdeaResponse)
async def create_idea(idea: IdeaCreate):
    """Create a new idea."""
    session = get_database()
    try:
        db_idea = IdeaModel(
            content=idea.content,
            source=idea.source
        )
        
        session.add(db_idea)
        session.commit()
        session.refresh(db_idea)
        
        return IdeaResponse(
            id=str(db_idea.id),
            content=db_idea.content,
            source=db_idea.source,
            processed=db_idea.processed,
            created_at=db_idea.created_at.isoformat()
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create idea: {str(e)}")
    finally:
        session.close()

@app.get("/ideas", response_model=List[IdeaResponse])
async def get_ideas(processed: Optional[bool] = None, limit: int = 10):
    """Get ideas."""
    session = get_database()
    try:
        query = session.query(IdeaModel)
        
        if processed is not None:
            query = query.filter(IdeaModel.processed == processed)
        
        ideas = query.order_by(IdeaModel.created_at.desc()).limit(limit).all()
        
        return [
            IdeaResponse(
                id=str(idea.id),
                content=idea.content,
                source=idea.source,
                processed=idea.processed,
                created_at=idea.created_at.isoformat()
            )
            for idea in ideas
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ideas: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting Aether AI Companion test server...")
    print(f"Database: {settings.database_url}")
    print(f"Server: http://{settings.host}:{settings.port}")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )