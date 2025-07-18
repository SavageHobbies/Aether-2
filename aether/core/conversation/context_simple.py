"""
Simple conversation context management for Aether AI Companion.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationContext:
    """Manages context for a single conversation session."""
    
    def __init__(self, session_id: str, max_context_length: int = 4000):
        """Initialize conversation context."""
        self.session_id = session_id
        self.max_context_length = max_context_length
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.relevant_memories: List = []
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation context."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        logger.debug(f"Added {role} message to session {self.session_id}")
    
    def get_context_string(self, include_memories: bool = True) -> str:
        """Get formatted context string for AI model."""
        context_parts = []
        
        # Add conversation history
        if self.messages:
            context_parts.append("## Conversation History:")
            for message in self.messages[-10:]:  # Last 10 messages
                role = message["role"].title()
                content = message["content"]
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "relevant_memories_count": len(self.relevant_memories),
            "metadata": self.metadata
        }


class ContextManager:
    """Manages conversation contexts across multiple sessions."""
    
    def __init__(self, cleanup_interval_minutes: int = 30):
        """Initialize context manager."""
        self.contexts: Dict[str, ConversationContext] = {}
        self.cleanup_interval = cleanup_interval_minutes
        self.last_cleanup = datetime.now()
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one."""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id)
            logger.info(f"Created new conversation context for session {session_id}")
        
        return self.contexts[session_id]
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get existing context."""
        return self.contexts.get(session_id)
    
    async def update_context_memories(
        self, 
        session_id: str, 
        query: str, 
        db_session,
        limit: int = 5,
        threshold: float = 0.3
    ):
        """
        Update context with relevant memories based on query.
        
        Args:
            session_id: Session identifier
            query: Query to search memories
            db_session: Database session
            limit: Maximum memories to retrieve
            threshold: Minimum similarity threshold
        """
        try:
            context = self.get_or_create_context(session_id)
            
            # Search for relevant memories
            from core.database.memory_integration import search_memories_by_content
            memory_results = await search_memories_by_content(
                db_session, query, limit, threshold
            )
            
            if memory_results:
                # Convert to simple format for now
                context.relevant_memories = memory_results[:limit]
                logger.info(f"Updated context with {len(memory_results)} relevant memories")
            
        except Exception as e:
            logger.error(f"Failed to update context memories: {e}")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get context manager statistics.
        
        Returns:
            Statistics dictionary
        """
        total_messages = sum(len(ctx.messages) for ctx in self.contexts.values())
        
        return {
            "active_sessions": len(self.contexts),
            "total_messages": total_messages,
            "last_cleanup": self.last_cleanup.isoformat(),
            "sessions": len(self.contexts)
        }
    
    def _cleanup_expired_contexts(self):
        """Clean up expired conversation contexts."""
        # For simplicity, we'll skip the actual cleanup logic for now
        # In a production system, this would remove old contexts
        logger.info("Context cleanup called (simplified version)")
        pass
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.contexts.keys())


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager