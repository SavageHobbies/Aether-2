"""
Database module for Aether AI Companion.
"""

from .connection import DatabaseManager, get_database_manager, initialize_database
from .models import Base, Conversation, Idea, MemoryEntry, Task
from .vector_store import VectorStoreManager, initialize_vector_store, get_vector_store
from .memory_integration import (
    get_memory_integration,
    add_memory_with_vector_indexing,
    search_memories_by_content
)

__all__ = [
    "Base",
    "Conversation", 
    "Idea",
    "MemoryEntry",
    "Task",
    "DatabaseManager",
    "get_database_manager",
    "initialize_database",
    "VectorStoreManager",
    "initialize_vector_store",
    "get_vector_store",
    "get_memory_integration",
    "add_memory_with_vector_indexing",
    "search_memories_by_content",
]