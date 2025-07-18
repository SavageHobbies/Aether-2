"""
Data models and interfaces for Aether AI Companion.
"""

from .base import (
    BaseModel,
    Conversation,
    ConversationManagerInterface,
    Idea,
    IdeaProcessorInterface,
    IdeaSource,
    MemoryEntry,
    MemoryManagerInterface,
    Priority,
    Task,
    TaskManagerInterface,
    TaskStatus,
)

__all__ = [
    "BaseModel",
    "Conversation",
    "ConversationManagerInterface",
    "Idea",
    "IdeaProcessorInterface",
    "IdeaSource",
    "MemoryEntry",
    "MemoryManagerInterface",
    "Priority",
    "Task",
    "TaskManagerInterface",
    "TaskStatus",
]