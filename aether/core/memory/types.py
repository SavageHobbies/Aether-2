"""
Memory system types and data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class MemoryType(Enum):
    """Types of memories that can be stored."""
    CONVERSATION = "conversation"
    IDEA = "idea"
    TASK = "task"
    FACT = "fact"
    PREFERENCE = "preference"
    CONTEXT = "context"
    RELATIONSHIP = "relationship"


@dataclass
class MemoryEntry:
    """A single memory entry in the system."""
    id: Optional[str] = None
    content: str = ""
    memory_type: MemoryType = MemoryType.CONVERSATION
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    importance_score: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None  # Source of the memory (conversation_id, etc.)
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class MemoryQuery:
    """Query parameters for memory search."""
    query_text: str
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    min_importance: float = 0.0
    max_results: int = 10
    similarity_threshold: float = 0.7
    include_metadata: bool = True


@dataclass
class MemorySearchResult:
    """Result from memory search operation."""
    memory: MemoryEntry
    similarity_score: float
    relevance_score: float  # Combined similarity + importance + recency
    explanation: Optional[str] = None  # Why this memory was retrieved
    
    @property
    def combined_score(self) -> float:
        """Get combined relevance score."""
        return self.relevance_score


@dataclass
class MemoryConsolidationResult:
    """Result from memory consolidation operation."""
    consolidated_count: int
    deleted_count: int
    updated_count: int
    summary: str
    details: List[str] = field(default_factory=list)


@dataclass
class MemoryStats:
    """Statistics about the memory system."""
    total_memories: int
    memories_by_type: Dict[MemoryType, int]
    average_importance: float
    most_accessed_memory: Optional[MemoryEntry]
    oldest_memory: Optional[MemoryEntry]
    newest_memory: Optional[MemoryEntry]
    storage_size_mb: float
    embedding_dimension: int