"""
Base data models and interfaces for Aether AI Companion.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, UUID
from uuid import uuid4


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IdeaSource(Enum):
    """Source of idea capture."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    VOICE = "voice"
    WEB = "web"


class Priority(Enum):
    """Priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BaseModel:
    """Base model with common fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not self.id:
            self.id = uuid4()
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()


@dataclass
class Conversation(BaseModel):
    """Conversation data model."""
    user_input: str
    ai_response: str
    context_metadata: Dict[str, Any]
    session_id: UUID
    memory_references: List[UUID]
    extracted_tasks: List[UUID]
    
    def __post_init__(self):
        super().__post_init__()
        if not self.context_metadata:
            self.context_metadata = {}
        if not self.memory_references:
            self.memory_references = []
        if not self.extracted_tasks:
            self.extracted_tasks = []


@dataclass
class MemoryEntry(BaseModel):
    """Memory entry data model."""
    content: str
    embedding: Optional[List[float]]
    importance_score: float
    tags: List[str]
    connections: List[UUID]
    user_editable: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.tags:
            self.tags = []
        if not self.connections:
            self.connections = []


@dataclass
class Idea(BaseModel):
    """Idea data model."""
    content: str
    source: IdeaSource
    processed: bool = False
    category: Optional[str] = None
    priority_score: float = 0.0
    connections: List[UUID] = None
    converted_to_task: Optional[UUID] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.connections is None:
            self.connections = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Task(BaseModel):
    """Task data model."""
    title: str
    description: str
    priority: Priority
    due_date: Optional[datetime]
    status: TaskStatus
    source_idea_id: Optional[UUID]
    external_integrations: Dict[str, str]
    dependencies: List[UUID]
    
    def __post_init__(self):
        super().__post_init__()
        if not self.external_integrations:
            self.external_integrations = {}
        if not self.dependencies:
            self.dependencies = []


# Abstract interfaces for core components

class ConversationManagerInterface(ABC):
    """Interface for conversation management."""
    
    @abstractmethod
    async def process_input(self, user_input: str, session_id: UUID) -> str:
        """Process user input and return AI response."""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, session_id: UUID, limit: int = 50) -> List[Conversation]:
        """Get conversation history for a session."""
        pass


class MemoryManagerInterface(ABC):
    """Interface for memory management."""
    
    @abstractmethod
    async def store_memory(self, content: str, importance_score: float = 1.0) -> MemoryEntry:
        """Store a new memory entry."""
        pass
    
    @abstractmethod
    async def retrieve_memories(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve relevant memories based on query."""
        pass
    
    @abstractmethod
    async def update_memory(self, memory_id: UUID, updates: Dict[str, Any]) -> MemoryEntry:
        """Update an existing memory entry."""
        pass


class TaskManagerInterface(ABC):
    """Interface for task management."""
    
    @abstractmethod
    async def create_task(self, title: str, description: str, priority: Priority) -> Task:
        """Create a new task."""
        pass
    
    @abstractmethod
    async def get_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get tasks, optionally filtered by status."""
        pass
    
    @abstractmethod
    async def update_task_status(self, task_id: UUID, status: TaskStatus) -> Task:
        """Update task status."""
        pass


class IdeaProcessorInterface(ABC):
    """Interface for idea processing."""
    
    @abstractmethod
    async def capture_idea(self, content: str, source: IdeaSource) -> Idea:
        """Capture and process a new idea."""
        pass
    
    @abstractmethod
    async def get_ideas(self, processed: Optional[bool] = None) -> List[Idea]:
        """Get ideas, optionally filtered by processed status."""
        pass
    
    @abstractmethod
    async def convert_to_task(self, idea_id: UUID) -> Task:
        """Convert an idea to a task."""
        pass