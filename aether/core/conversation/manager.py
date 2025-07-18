"""
Main conversation manager for Aether AI Companion.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import (
    get_database_manager,
    add_memory_with_vector_indexing,
    Conversation,
    Task,
    Idea
)
from shared.schemas import ConversationCreate, ConversationResponse
from shared.serialization import ModelSerializer
from .context_simple import ContextManager, get_context_manager
from core.ai import get_ai_provider, get_prompt_manager
from core.memory import get_memory_manager, MemoryType, MemoryQuery

logger = logging.getLogger(__name__)



class ConversationManager:
    """Manages AI conversations with context and memory integration."""
    
    def __init__(self, ai_provider: Optional[Any] = None):
        """
        Initialize conversation manager.
        
        Args:
            ai_provider: AI provider instance (optional)
        """
        self.ai_provider = ai_provider or get_ai_provider()
        self.context_manager = get_context_manager()
        self.prompt_manager = get_prompt_manager()
        self.memory_manager = get_memory_manager()
        
        logger.info(f"Initialized conversation manager with {self.ai_provider.model_name}")
    
    async def process_message(
        self,
        user_input: str,
        session_id: str,
        db_session: AsyncSession,
        save_to_database: bool = True,
        create_memory: bool = True
    ) -> ConversationResponse:
        """
        Process user message and generate AI response.
        
        Args:
            user_input: User's input message
            session_id: Session identifier
            db_session: Database session
            save_to_database: Whether to save conversation to database
            create_memory: Whether to create memory entries
        
        Returns:
            ConversationResponse with AI response
        """
        try:
            # Get or create conversation context
            context = self.context_manager.get_or_create_context(session_id)
            
            # Search for relevant memories using the new memory system
            memory_query = MemoryQuery(
                query_text=user_input,
                max_results=5,
                similarity_threshold=0.7,
                include_metadata=True
            )
            relevant_memories = await self.memory_manager.search_memories(memory_query)
            
            # Add user message to context
            context.add_message("user", user_input)
            
            # Get context string for AI
            context_string = context.get_context_string()
            
            # Determine conversation type and build enhanced prompt
            conversation_type = self.prompt_manager.extract_conversation_type(user_input)
            
            # Build memory context from relevant memories
            memory_context = ""
            if relevant_memories:
                memory_parts = []
                for result in relevant_memories[:3]:
                    memory_parts.append(f"- {result.memory.content} (relevance: {result.relevance_score:.2f})")
                memory_context = "\n".join(memory_parts)
            
            # Generate AI response with enhanced prompting
            if hasattr(self.ai_provider, 'generate_response'):
                # Use the AI provider's generate_response method
                ai_response = await self.ai_provider.generate_response(
                    user_input, context_string, context.metadata
                )
            else:
                # Fallback for providers without the method
                ai_response = "I apologize, but I'm having trouble processing your request right now."
            
            # Add AI response to context
            context.add_message("assistant", ai_response)
            
            # Create conversation metadata
            conversation_metadata = {
                "model": getattr(self.ai_provider, 'model_name', 'unknown'),
                "context_length": len(context_string),
                "relevant_memories": len(relevant_memories),
                "session_message_count": len(context.messages)
            }
            
            # Save conversation to database if requested
            conversation_id = None
            if save_to_database:
                conversation = Conversation(
                    session_id=session_id,
                    user_input=user_input,
                    ai_response=ai_response,
                    context_metadata=conversation_metadata
                )
                
                db_session.add(conversation)
                await db_session.flush()
                conversation_id = conversation.id
                
                logger.debug(f"Saved conversation {conversation_id} to database")
            
            # Create memory entries if requested
            if create_memory and conversation_id:
                await self._create_conversation_memory(
                    db_session, user_input, ai_response, conversation_id
                )
            
            # Commit database changes
            if save_to_database or create_memory:
                await db_session.commit()
            
            # Create response
            response = ConversationResponse(
                id=str(conversation_id) if conversation_id else str(uuid4()),
                session_id=session_id,
                user_input=user_input,
                ai_response=ai_response,
                context_metadata=conversation_metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"Processed message for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await db_session.rollback()
            
            # Return error response
            return ConversationResponse(
                id=str(uuid4()),
                session_id=session_id,
                user_input=user_input,
                ai_response="I apologize, but I encountered an error processing your message. Please try again.",
                context_metadata={"error": str(e)},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    async def get_conversation_history(
        self,
        session_id: str,
        db_session: AsyncSession,
        limit: int = 50
    ) -> List[ConversationResponse]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            db_session: Database session
            limit: Maximum conversations to return
        
        Returns:
            List of ConversationResponse objects
        """
        try:
            from sqlalchemy import select, desc
            
            stmt = (
                select(Conversation)
                .where(Conversation.session_id == session_id)
                .order_by(desc(Conversation.created_at))
                .limit(limit)
            )
            
            result = await db_session.execute(stmt)
            conversations = result.scalars().all()
            
            # Serialize conversations
            return [
                ModelSerializer.serialize_conversation(conv)
                for conv in reversed(conversations)  # Reverse to get chronological order
            ]
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def extract_tasks_from_conversation(
        self,
        conversation_id: str,
        db_session: AsyncSession
    ) -> List[str]:
        """
        Extract potential tasks from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            db_session: Database session
        
        Returns:
            List of extracted task descriptions
        """
        try:
            from sqlalchemy import select
            
            # Get conversation
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await db_session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                return []
            
            # Simple task extraction patterns
            task_patterns = [
                r"i need to (.+)",
                r"i should (.+)",
                r"i have to (.+)",
                r"i want to (.+)",
                r"let me (.+)",
                r"i'll (.+)",
                r"create (.+)",
                r"build (.+)",
                r"design (.+)",
                r"implement (.+)"
            ]
            
            extracted_tasks = []
            text = f"{conversation.user_input} {conversation.ai_response}".lower()
            
            for pattern in task_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match.strip()) > 5:  # Minimum task length
                        extracted_tasks.append(match.strip().capitalize())
            
            return list(set(extracted_tasks))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting tasks: {e}")
            return []
    
    async def _create_conversation_memory(
        self,
        db_session: AsyncSession,
        user_input: str,
        ai_response: str,
        conversation_id: str
    ):
        """
        Create memory entries from conversation using the new memory system.
        
        Args:
            db_session: Database session
            user_input: User input
            ai_response: AI response
            conversation_id: Conversation ID
        """
        try:
            # Create memory content
            memory_content = f"User: {user_input}\nAssistant: {ai_response}"
            
            # Calculate importance based on content
            importance_score = self._calculate_memory_importance(user_input, ai_response)
            
            # Extract tags
            tags = self._extract_memory_tags(user_input, ai_response)
            
            # Create memory using the new memory manager
            await self.memory_manager.store_memory(
                content=memory_content,
                memory_type=MemoryType.CONVERSATION,
                metadata={
                    "conversation_id": conversation_id,
                    "user_input_length": len(user_input),
                    "ai_response_length": len(ai_response),
                    "created_from": "conversation"
                },
                importance_score=importance_score,
                tags=tags,
                source=f"conversation_{conversation_id}"
            )
            
            logger.debug(f"Created memory for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error creating conversation memory: {e}")
    
    def _calculate_memory_importance(self, user_input: str, ai_response: str) -> float:
        """
        Calculate importance score for memory.
        
        Args:
            user_input: User input
            ai_response: AI response
        
        Returns:
            Importance score (0.0 to 1.0)
        """
        # Base importance
        importance = 0.5
        
        # Increase for business/planning keywords
        business_keywords = [
            "dashboard", "business", "project", "plan", "strategy",
            "goal", "deadline", "priority", "important", "urgent"
        ]
        
        text = f"{user_input} {ai_response}".lower()
        keyword_count = sum(1 for keyword in business_keywords if keyword in text)
        importance += min(keyword_count * 0.1, 0.3)
        
        # Increase for questions and detailed responses
        if "?" in user_input:
            importance += 0.1
        
        if len(ai_response) > 200:
            importance += 0.1
        
        return min(importance, 1.0)
    
    def _extract_memory_tags(self, user_input: str, ai_response: str) -> List[str]:
        """
        Extract tags from conversation content.
        
        Args:
            user_input: User input
            ai_response: AI response
        
        Returns:
            List of tags
        """
        tags = ["conversation"]
        
        text = f"{user_input} {ai_response}".lower()
        
        # Common tag patterns
        tag_patterns = {
            "dashboard": ["dashboard", "visualization"],
            "business": ["business", "analytics"],
            "task": ["task", "productivity"],
            "idea": ["idea", "planning"],
            "project": ["project", "development"],
            "calendar": ["calendar", "scheduling"],
            "integration": ["integration", "tools"],
            "help": ["help", "support"]
        }
        
        for keyword, related_tags in tag_patterns.items():
            if keyword in text:
                tags.extend(related_tags)
        
        return list(set(tags))  # Remove duplicates
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get conversation manager statistics.
        
        Returns:
            Statistics dictionary
        """
        context_stats = self.context_manager.get_context_stats()
        
        return {
            "ai_provider": getattr(self.ai_provider, 'model_name', 'unknown'),
            "context_manager": context_stats
        }


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def initialize_conversation_manager(ai_provider: Optional[Any] = None) -> ConversationManager:
    """
    Initialize global conversation manager.
    
    Args:
        ai_provider: AI provider instance
    
    Returns:
        ConversationManager instance
    """
    global _conversation_manager
    _conversation_manager = ConversationManager(ai_provider)
    return _conversation_manager


def get_conversation_manager() -> ConversationManager:
    """
    Get global conversation manager instance.
    
    Returns:
        ConversationManager instance
    
    Raises:
        RuntimeError: If not initialized
    """
    if _conversation_manager is None:
        # Auto-initialize with default provider
        return initialize_conversation_manager()
    return _conversation_manager