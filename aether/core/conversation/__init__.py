"""
Conversation management for Aether AI Companion.
"""

from .context_simple import ConversationContext, ContextManager, get_context_manager
from .manager import ConversationManager, get_conversation_manager, initialize_conversation_manager

__all__ = [
    "ConversationContext",
    "ContextManager", 
    "ConversationManager",
    "get_conversation_manager",
    "initialize_conversation_manager",
]