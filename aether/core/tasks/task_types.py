"""
Task management types and data structures.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    """Task status levels."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class TaskType(Enum):
    """Types of tasks."""
    ACTION = "action"
    MEETING = "meeting"
    DEADLINE = "deadline"
    REMINDER = "reminder"
    RESEARCH = "research"
    DECISION = "decision"
    REVIEW = "review"


class DependencyType(Enum):
    """Types of task dependencies."""
    BLOCKS = "blocks"  # This task blocks another
    BLOCKED_BY = "blocked_by"  # This task is blocked by another
    RELATED = "related"  # Tasks are related but not blocking
    SUBTASK = "subtask"  # This is a subtask of another
    PARENT = "parent"  # This task has subtasks


@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""
    task_id: str
    dependent_task_id: str
    dependency_type: DependencyType
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class TaskEntry:
    """A task entry in the system."""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    
    # Classification
    task_type: TaskType = TaskType.ACTION
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    
    # Scheduling
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    
    # Organization
    project_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    
    # Context
    source_conversation_id: Optional[str] = None
    source_idea_id: Optional[str] = None
    extracted_from: Optional[str] = None  # Text from which task was extracted
    
    # Dependencies
    dependencies: List[TaskDependency] = field(default_factory=list)
    
    # Scoring
    priority_score: float = 0.5  # 0.0 to 1.0
    urgency_score: float = 0.5   # 0.0 to 1.0
    importance_score: float = 0.5  # 0.0 to 1.0
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class ExtractionResult:
    """Result from task extraction operation."""
    success: bool
    source_text: str
    extracted_tasks: List[TaskEntry] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time_ms: float = 0.0
    extraction_method: str = "unknown"
    suggestions: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class TaskAnalysis:
    """Analysis of task characteristics and relationships."""
    task: TaskEntry
    complexity_score: float = 0.0  # 0.0 to 1.0
    estimated_effort: str = "medium"  # low, medium, high
    suggested_breakdown: List[str] = field(default_factory=list)
    potential_blockers: List[str] = field(default_factory=list)
    recommended_timeline: Optional[timedelta] = None
    skill_requirements: List[str] = field(default_factory=list)


@dataclass
class TaskStats:
    """Statistics about the task system."""
    total_tasks: int
    tasks_by_status: Dict[TaskStatus, int]
    tasks_by_priority: Dict[TaskPriority, int]
    tasks_by_type: Dict[TaskType, int]
    overdue_tasks: int
    completed_today: int
    average_completion_time_hours: float
    most_common_tags: List[tuple[str, int]]  # (tag, count)
    productivity_score: float  # 0.0 to 1.0