"""
Data schemas and validation for Aether AI Companion.
"""

from .base import BaseSchema, ValidationError
from .conversation import ConversationCreate, ConversationResponse, ConversationUpdate
from .idea import IdeaCreate, IdeaResponse, IdeaUpdate
from .memory import MemoryEntryCreate, MemoryEntryResponse, MemoryEntryUpdate, MemorySearchRequest
from .task import TaskCreate, TaskResponse, TaskUpdate

__all__ = [
    "BaseSchema",
    "ValidationError",
    "ConversationCreate",
    "ConversationResponse", 
    "ConversationUpdate",
    "IdeaCreate",
    "IdeaResponse",
    "IdeaUpdate",
    "MemoryEntryCreate",
    "MemoryEntryResponse",
    "MemoryEntryUpdate",
    "MemorySearchRequest",
    "TaskCreate",
    "TaskResponse",
    "TaskUpdate",
]