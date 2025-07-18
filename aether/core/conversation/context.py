"""
Conversation context management for Aether AI Companion.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from core.database.memory_integration import search_memories_by_content
from shared.schemas import MemoryEntryResponse

logger = logging.getLogger(__name__)


class ConversationContext:
    """Manages context for a single conversation session."""
    
    def __init__(self, session_id: str, max_context_length: int = 4000):
        """
        Initialize conversation context.
        
        Args:
            session_id: Unique session identifier
            max_context_length: Maximum context length in characters
        """
        self.session_id = session_id
        self.max_context_length = max_context_length
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.relevant_memories: List[Tuple[MemoryEntryResponse, float]] = []
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to the conversation context.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
        
        # Trim context if too long
        self._trim_context()
        
        logger.debug(f"Added {role} message to session {self.session_id}")
    
    def get_context_string(self, include_memories: bool = True) -> str:
        """
        Get formatted context string for AI model.
        
        Args:
            include_memories: Whether to include relevant memories
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add relevant memories if available
        if include_memories and self.relevant_memories:
            context_parts.append("## Relevant Context from Memory:")
            for memory, similarity in self.relevant_memories[:3]:  # Top 3 memories
                context_parts.append(f"- {memory.content} (relevance: {similarity:.2f})")
            context_parts.append("")
        
        # Add conversation history
        if self.messages:
            context_parts.append("## Conversation History:")
            for message in self.messages[-10:]:  # Last 10 messages
                role = message["role"].title()
                content = message["content"]
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent messages from the conversation.
        
        Args:
            count: Number of recent messages to return
        
        Returns:
            List of recent messages
        """
        return self.messages[-count:] if self.messages else []
    
    def update_metadata(self, key: str, value: Any):
        """
        Update conversation metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.last_activity = datetime.utcnow()
    
    def set_relevant_memories(self, memories: List[Tuple[MemoryEntryResponse, float]]):
        """
        Set relevant memories for this conversation.
        
        Args:
            memories: List of (memory, similarity_score) tuples
        """
        self.relevant_memories = memories
        logger.debug(f"Set {len(memories)} relevant memories for session {self.session_id}")
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """
        Check if conversation context has expired.
        
        Args:
            timeout_minutes: Timeout in minutes
        
        Returns:
            True if expired
        """
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.last_activity > timeout
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get conversation summary.
        
        Returns:
            Summary dictionary
        """
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "relevant_memories_count": len(self.relevant_memories),
            "metadata": self.metadata
        }
    
    def _trim_context(self):
        """Trim context to stay within length limits."""
        if not self.messages:
            return
        
        # Calculate total context length
        total_length = sum(len(msg["content"]) for msg in self.messages)
        
        # Remove oldest messages if over limit
        while total_length > self.max_context_length and len(self.messages) > 2:
            removed_message = self.messages.pop(0)
            total_length -= len(removed_message["content"])
            logger.debug(f"Trimmed old message from context (session: {self.session_id})")


class ContextManager:
    """Manages conversation contexts across multiple sessions."""
    
    def __init__(self, cleanup_interval_minutes: int = 30):
        """
        Initialize context manager.
        
        Args:
            cleanup_interval_minutes: How often to clean up expired contexts
        """
        self.contexts: Dict[str, ConversationContext] = {}
        self.cleanup_interval = cleanup_interval_minutes
        self.last_cleanup = datetime.utcnow()
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """
        Get existing context or create new one.
        
        Args:
            session_id: Session identifier
        
        Returns:
            ConversationContext instance
        """
        # Clean up expired contexts periodically
        self._cleanup_expired_contexts()
        
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id)
            logger.info(f"Created new conversation context for session {session_id}")
        
        return self.contexts[session_id]
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get existing context.
        
        Args:
            session_id: Session identifier
        
        Returns:
            ConversationContext or None if not found
        """
        return self.contexts.get(session_id)
    
    def remove_context(self, session_id: str) -> bool:
        """
        Remove context for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if context was removed
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"Removed conversation context for session {session_id}")
            return True
        return False
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List of active session IDs
        """
        return list(self.contexts.keys())
    
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
            "sessions": [ctx.get_summary() for ctx in self.contexts.values()]
        }
    
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
            memory_results = await search_memories_by_content(
                db_session, query, limit, threshold
            )
            
            if memory_results:
                # Convert to response format
                memory_responses = []
                for memory_entry, similarity in memory_results:
                    from shared.serialization import ModelSerializer
                    memory_response = ModelSerializer.serialize_memory_entry(memory_entry)
                    memory_responses.append((memory_response, similarity))
                
                context.set_relevant_memories(memory_responses)
                logger.info(f"Updated context with {len(memory_responses)} relevant memories")
            
        except Exception as e:
            logger.error(f"Failed to update context memories: {e}")
    
    def _cleanup_expired_contexts(self):
        """Clean up expired conversation contexts."""
        now = datetime.utcnow()
        cleanup_interval = timedelta(minutes=self.cleanup_interval)
        
        if now - self.last_cleanup < cleanup_interval:
            return
        
        expired_sessions = []
        for session_id, context in self.contexts.items():
            if context.is_expired():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.contexts[session_id]
            logger.info(f"Cleaned up expired context for session {session_id}")
        
        self.last_cleanup = now
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired contexts")


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """
    Get global context manager instance.
    
    Returns:
        ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def initialize_context_manager(cleanup_interval_minutes: int = 30) -> ContextManager:
    """
    Initialize global context manager.
    
    Args:
        cleanup_interval_minutes: Cleanup interval
    
    Returns:
        ContextManager instance
    """
    global _context_manager
    _context_manager = ContextManager(cleanup_interval_minutes)
    return _context_manager