"""
Idea processing types and data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


class IdeaCategory(Enum):
    """Categories for idea classification."""
    BUSINESS = "business"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    PRODUCTIVITY = "productivity"
    PERSONAL = "personal"
    RESEARCH = "research"
    PRODUCT = "product"
    MARKETING = "marketing"
    PROCESS = "process"
    STRATEGY = "strategy"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    PROBLEM_SOLVING = "problem_solving"
    INNOVATION = "innovation"
    OTHER = "other"


class IdeaPriority(Enum):
    """Priority levels for ideas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class IdeaStatus(Enum):
    """Status of idea processing."""
    CAPTURED = "captured"
    PROCESSING = "processing"
    CATEGORIZED = "categorized"
    EXPANDED = "expanded"
    CONVERTED = "converted"
    ARCHIVED = "archived"


@dataclass
class IdeaEntry:
    """A single idea entry in the system."""
    id: Optional[str] = None
    content: str = ""
    title: Optional[str] = None
    category: IdeaCategory = IdeaCategory.OTHER
    priority: IdeaPriority = IdeaPriority.MEDIUM
    status: IdeaStatus = IdeaStatus.CAPTURED
    
    # Metadata
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None  # conversation_id, voice_input, manual, etc.
    context: Optional[str] = None  # Additional context about the idea
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Processing results
    extracted_keywords: List[str] = field(default_factory=list)
    suggested_categories: List[IdeaCategory] = field(default_factory=list)
    confidence_score: float = 0.0  # Confidence in categorization
    
    # Relationships
    related_ideas: List[str] = field(default_factory=list)  # IDs of related ideas
    parent_idea: Optional[str] = None  # ID of parent idea if this is a sub-idea
    sub_ideas: List[str] = field(default_factory=list)  # IDs of sub-ideas
    
    # Conversion tracking
    converted_to_tasks: List[str] = field(default_factory=list)  # Task IDs
    converted_to_events: List[str] = field(default_factory=list)  # Calendar event IDs
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class IdeaQuery:
    """Query parameters for idea search."""
    query_text: Optional[str] = None
    categories: Optional[List[IdeaCategory]] = None
    priorities: Optional[List[IdeaPriority]] = None
    statuses: Optional[List[IdeaStatus]] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    source: Optional[str] = None
    max_results: int = 20
    similarity_threshold: float = 0.6
    include_related: bool = False


@dataclass
class IdeaSearchResult:
    """Result from idea search operation."""
    idea: IdeaEntry
    similarity_score: float = 0.0
    relevance_score: float = 0.0
    match_reasons: List[str] = field(default_factory=list)


@dataclass
class IdeaProcessingResult:
    """Result from idea processing operation."""
    idea: IdeaEntry
    processing_time_ms: float
    extracted_keywords: List[str]
    suggested_categories: List[tuple[IdeaCategory, float]]  # (category, confidence)
    generated_title: Optional[str] = None
    suggested_tags: List[str] = field(default_factory=list)
    context_analysis: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class IdeaExpansionResult:
    """Result from idea expansion operation."""
    original_idea: IdeaEntry
    expanded_content: str
    follow_up_questions: List[str]
    related_concepts: List[str]
    potential_challenges: List[str]
    implementation_suggestions: List[str]
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class IdeaConnectionResult:
    """Result from idea connection analysis."""
    idea: IdeaEntry
    connections: List[tuple[str, float, str]]  # (idea_id, similarity, connection_type)
    connection_summary: str
    suggested_merges: List[str] = field(default_factory=list)  # IDs of ideas to potentially merge
    suggested_hierarchies: List[tuple[str, str]] = field(default_factory=list)  # (parent_id, child_id)


@dataclass
class IdeaStats:
    """Statistics about the idea system."""
    total_ideas: int
    ideas_by_category: Dict[IdeaCategory, int]
    ideas_by_priority: Dict[IdeaPriority, int]
    ideas_by_status: Dict[IdeaStatus, int]
    ideas_by_source: Dict[str, int]
    average_processing_time_ms: float
    most_active_tags: List[tuple[str, int]]  # (tag, count)
    most_common_keywords: List[tuple[str, int]]  # (keyword, count)
    conversion_rates: Dict[str, float]  # conversion_type -> rate
    recent_activity: List[tuple[datetime, str, str]]  # (timestamp, action, idea_id)