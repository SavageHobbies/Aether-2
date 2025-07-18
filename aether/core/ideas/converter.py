"""
Idea-to-action conversion system for Aether AI Companion.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from core.ai import get_ai_provider
from shared.utils.logging import get_logger
from .types import IdeaEntry, IdeaCategory, IdeaPriority

logger = get_logger(__name__)


class ConversionType(Enum):
    """Types of conversions available."""
    TASK = "task"
    CALENDAR_EVENT = "calendar_event"
    PROJECT = "project"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class TaskEntry:
    """A task converted from an idea."""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    source_idea_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class CalendarEvent:
    """A calendar event converted from an idea."""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source_idea_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ProjectEntry:
    """A project that can contain multiple tasks and ideas."""
    id: Optional[str] = None
    name: str = ""
    description: str = ""
    source_idea_ids: List[str] = field(default_factory=list)
    task_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ConversionResult:
    """Result from idea-to-action conversion."""
    success: bool
    conversion_type: ConversionType
    source_idea: IdeaEntry
    tasks: List[TaskEntry] = field(default_factory=list)
    calendar_events: List[CalendarEvent] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    conversion_confidence: float = 0.0
    processing_time_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class IdeaToActionConverter:
    """Converts ideas into actionable tasks, calendar events, and projects."""
    
    def __init__(self):
        """Initialize idea-to-action converter."""
        self.ai_provider = get_ai_provider()
        self.default_task_duration = 60  # minutes
        self.default_meeting_duration = 30  # minutes
        logger.info("Idea-to-action converter initialized")
    
    async def convert_idea_to_task(self, idea: IdeaEntry) -> ConversionResult:
        """Convert an idea into actionable tasks."""
        start_time = datetime.utcnow()
        
        try:
            # Generate task using AI
            prompt = f"""Convert this idea into actionable tasks:

Idea: {idea.content}
Category: {idea.category.value}

Break this down into specific, actionable tasks with:
1. Clear task titles
2. Brief descriptions
3. Estimated time in minutes

Format as numbered list."""
            
            ai_response = await self.ai_provider.generate_response(
                user_input=prompt,
                context=f"Converting {idea.category.value} idea to tasks"
            )
            
            # Parse response into tasks
            tasks = self._parse_task_response(ai_response, idea)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ConversionResult(
                success=True,
                conversion_type=ConversionType.TASK,
                source_idea=idea,
                tasks=tasks,
                conversion_confidence=0.8,
                processing_time_ms=processing_time,
                suggestions=["Consider setting specific due dates", "Add priority levels"]
            )
            
        except Exception as e:
            logger.error(f"Error converting idea to task: {e}")
            return ConversionResult(
                success=False,
                conversion_type=ConversionType.TASK,
                source_idea=idea,
                error_message=str(e)
            )
    
    async def convert_idea_to_calendar_event(
        self, 
        idea: IdeaEntry, 
        preferred_time: Optional[datetime] = None
    ) -> ConversionResult:
        """Convert an idea into a calendar event."""
        start_time = datetime.utcnow()
        
        try:
            # Create calendar event
            event_start = preferred_time or (datetime.utcnow() + timedelta(days=1))
            event_end = event_start + timedelta(minutes=self.default_meeting_duration)
            
            event = CalendarEvent(
                id=str(uuid.uuid4()),
                title=idea.content[:50] + "..." if len(idea.content) > 50 else idea.content,
                description=idea.content,
                start_time=event_start,
                end_time=event_end,
                source_idea_id=idea.id,
                tags=idea.tags.copy()
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ConversionResult(
                success=True,
                conversion_type=ConversionType.CALENDAR_EVENT,
                source_idea=idea,
                calendar_events=[event],
                conversion_confidence=0.7,
                processing_time_ms=processing_time,
                suggestions=["Set specific location", "Add attendees if needed"]
            )
            
        except Exception as e:
            logger.error(f"Error converting idea to calendar event: {e}")
            return ConversionResult(
                success=False,
                conversion_type=ConversionType.CALENDAR_EVENT,
                source_idea=idea,
                error_message=str(e)
            )
    
    def _parse_task_response(self, response: str, idea: IdeaEntry) -> List[TaskEntry]:
        """Parse AI response into task entries."""
        tasks = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•'))):
                # Extract task title
                title = line.lstrip('123456789.-•').strip()
                
                task = TaskEntry(
                    id=str(uuid.uuid4()),
                    title=title[:100],
                    description=title,
                    source_idea_id=idea.id,
                    tags=idea.tags.copy(),
                    estimated_duration_minutes=self.default_task_duration,
                    due_date=datetime.utcnow() + timedelta(days=7)
                )
                
                # Set priority based on idea priority
                if idea.priority == IdeaPriority.HIGH:
                    task.priority = TaskPriority.HIGH
                elif idea.priority == IdeaPriority.URGENT:
                    task.priority = TaskPriority.URGENT
                else:
                    task.priority = TaskPriority.MEDIUM
                
                tasks.append(task)
        
        # If no tasks were parsed, create a default task
        if not tasks:
            tasks.append(TaskEntry(
                id=str(uuid.uuid4()),
                title=idea.content[:50] + "..." if len(idea.content) > 50 else idea.content,
                description=idea.content,
                source_idea_id=idea.id,
                tags=idea.tags.copy(),
                estimated_duration_minutes=self.default_task_duration,
                due_date=datetime.utcnow() + timedelta(days=7)
            ))
        
        return tasks


# Global converter instance
_idea_converter: Optional[IdeaToActionConverter] = None


def get_idea_converter() -> IdeaToActionConverter:
    """Get global idea-to-action converter instance."""
    global _idea_converter
    if _idea_converter is None:
        _idea_converter = IdeaToActionConverter()
    return _idea_converter