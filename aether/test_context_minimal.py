"""Minimal test for context module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing minimal context...")

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

print("Basic imports successful")

from core.database.memory_integration import search_memories_by_content
print("Database import successful")

from shared.schemas import MemoryEntryResponse
print("Schema import successful")

logger = logging.getLogger(__name__)

print("About to define ConversationContext class")

class ConversationContext:
    """Manages context for a single conversation session."""
    
    def __init__(self, session_id: str, max_context_length: int = 4000):
        """Initialize conversation context."""
        self.session_id = session_id
        self.max_context_length = max_context_length
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.relevant_memories: List[Tuple[MemoryEntryResponse, float]] = []

print("ConversationContext class defined successfully")

# Test instantiation
context = ConversationContext("test-session")
print(f"ConversationContext instantiated: {context.session_id}")

print("All tests passed!")