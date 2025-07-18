"""
Task identification and extraction from conversations.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid

from .task_types import (
    TaskEntry, TaskPriority, TaskStatus, TaskType, 
    ExtractionResult, DependencyType, TaskDependency
)

logger = logging.getLogger(__name__)


class TaskExtractor:
    """Extracts tasks from conversation text using NLP."""
    
    def __init__(self):
        """Initialize the task extractor."""
        # Priority keywords and their weights
        self.priority_keywords = {
            TaskPriority.URGENT: ["urgent", "asap", "immediately", "critical", "emergency", "now"],
            TaskPriority.HIGH: ["important", "priority", "soon", "quickly", "deadline"],
            TaskPriority.MEDIUM: ["should", "need", "want", "plan"],
            TaskPriority.LOW: ["maybe", "consider", "eventually", "someday"]
        }
        
        # Time extraction patterns
        self.time_patterns = [
            (r"by (\w+day)", "weekday"),
            (r"in (\d+) days?", "days"),
            (r"in (\d+) weeks?", "weeks"),
            (r"next week", "next_week"),
            (r"tomorrow", "tomorrow"),
            (r"today", "today")
        ]
        
        # Task identification patterns
        self.task_patterns = [
            (r"(?:I )?(?:need to|have to|must|should) (.+)", TaskType.ACTION),
            (r"(?:Don't forget to|Remember to) (.+)", TaskType.REMINDER),
            (r"(?:Schedule|Set up|Arrange) (?:a )?(?:meeting|call) (.+)", TaskType.MEETING),
            (r"(.+) (?:is )?due (.+)", TaskType.DEADLINE),
            (r"(?:Research|Look into|Find out about) (.+)", TaskType.RESEARCH),
            (r"(?:Review|Analyze|Examine) (.+)", TaskType.REVIEW),
            (r"(?:Decide|Choose|Determine) (.+)", TaskType.DECISION),
        ]
    
    def extract_tasks_from_text(
        self, 
        text: str, 
        conversation_id: Optional[str] = None,
        source_context: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """Extract tasks from text using regex patterns."""
        start_time = datetime.utcnow()
        
        try:
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Extract tasks using regex patterns
            tasks = self._extract_with_regex(cleaned_text)
            
            # Enhance tasks with additional information
            enhanced_tasks = []
            for task in tasks:
                enhanced_task = self._enhance_task(task, text, source_context)
                enhanced_tasks.append(enhanced_task)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(enhanced_tasks, text)
            
            # Processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ExtractionResult(
                success=True,
                source_text=text,
                extracted_tasks=enhanced_tasks,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                extraction_method="regex",
                suggestions=self._generate_suggestions(enhanced_tasks, text)
            )
            
        except Exception as e:
            logger.error(f"Error extracting tasks: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ExtractionResult(
                success=False,
                source_text=text,
                confidence_score=0.0,
                processing_time_ms=processing_time,
                extraction_method="error",
                error_message=str(e)
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for task extraction."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize common contractions
        contractions = {
            "I'll": "I will", "I'd": "I would", "I've": "I have",
            "we'll": "we will", "don't": "do not", "won't": "will not",
            "can't": "cannot", "shouldn't": "should not"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _extract_with_regex(self, text: str) -> List[TaskEntry]:
        """Extract tasks using regex patterns."""
        tasks = []
        
        for pattern, task_type in self.task_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                task_content = match.group(1).strip()
                if len(task_content) < 3:  # Skip very short matches
                    continue
                
                # Extract due date if present
                due_date = self._extract_due_date(task_content)
                
                # Calculate priority
                priority = self._calculate_priority(task_content)
                
                task = TaskEntry(
                    id=str(uuid.uuid4()),
                    title=self._clean_task_title(task_content),
                    description=task_content,
                    task_type=task_type,
                    priority=priority,
                    due_date=due_date,
                    extracted_from=match.group(0),
                    priority_score=self._get_priority_score(priority)
                )
                
                tasks.append(task)
        
        return tasks
    
    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date from text."""
        text_lower = text.lower()
        now = datetime.now()
        
        # Check for specific time patterns
        for pattern, time_type in self.time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if time_type == "days":
                    days = int(match.group(1))
                    return now + timedelta(days=days)
                elif time_type == "weeks":
                    weeks = int(match.group(1))
                    return now + timedelta(weeks=weeks)
                elif time_type == "tomorrow":
                    return now + timedelta(days=1)
                elif time_type == "today":
                    return now
                elif time_type == "next_week":
                    return now + timedelta(days=7)
                elif time_type == "weekday":
                    weekday = match.group(1).lower()
                    if weekday in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                        target_day = weekdays.index(weekday)
                        current_day = now.weekday()
                        days_ahead = target_day - current_day
                        if days_ahead <= 0:
                            days_ahead += 7
                        return now + timedelta(days=days_ahead)
        
        return None
    
    def _calculate_priority(self, text: str) -> TaskPriority:
        """Calculate task priority based on keywords."""
        text_lower = text.lower()
        
        # Check for priority keywords
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return priority
        
        return TaskPriority.MEDIUM
    
    def _clean_task_title(self, text: str) -> str:
        """Clean and format task title."""
        text = text.strip()
        text = re.sub(r'[,;!?]+$', '', text)
        
        if text:
            text = text[0].upper() + text[1:]
        
        return text[:100]
    
    def _get_priority_score(self, priority: TaskPriority) -> float:
        """Convert priority enum to numeric score."""
        priority_scores = {
            TaskPriority.LOW: 0.2,
            TaskPriority.MEDIUM: 0.5,
            TaskPriority.HIGH: 0.8,
            TaskPriority.URGENT: 1.0
        }
        return priority_scores.get(priority, 0.5)
    
    def _enhance_task(
        self, 
        task: TaskEntry, 
        original_text: str, 
        context: Optional[Dict[str, Any]]
    ) -> TaskEntry:
        """Enhance task with additional information."""
        if context:
            task.source_conversation_id = context.get('conversation_id')
            task.source_idea_id = context.get('idea_id')
        
        if not task.due_date:
            task.due_date = self._extract_due_date(original_text)
        
        task.urgency_score = self._calculate_urgency_score(task, original_text)
        task.importance_score = self._calculate_importance_score(task, original_text)
        task.tags = self._extract_tags(original_text)
        
        return task
    
    def _calculate_urgency_score(self, task: TaskEntry, text: str) -> float:
        """Calculate urgency score based on due date and keywords."""
        urgency = 0.5
        
        if task.due_date:
            days_until_due = (task.due_date - datetime.now()).days
            if days_until_due <= 0:
                urgency = 1.0
            elif days_until_due <= 1:
                urgency = 0.9
            elif days_until_due <= 3:
                urgency = 0.8
            elif days_until_due <= 7:
                urgency = 0.6
            else:
                urgency = 0.4
        
        text_lower = text.lower()
        if any(word in text_lower for word in ["urgent", "asap", "immediately", "critical"]):
            urgency = min(urgency + 0.3, 1.0)
        
        return urgency
    
    def _calculate_importance_score(self, task: TaskEntry, text: str) -> float:
        """Calculate importance score based on context and keywords."""
        type_importance = {
            TaskType.DEADLINE: 0.8,
            TaskType.MEETING: 0.7,
            TaskType.DECISION: 0.7,
            TaskType.ACTION: 0.5,
            TaskType.REVIEW: 0.4,
            TaskType.RESEARCH: 0.4,
            TaskType.REMINDER: 0.3
        }
        importance = type_importance.get(task.task_type, 0.5)
        
        text_lower = text.lower()
        if any(word in text_lower for word in ["important", "critical", "key", "essential"]):
            importance = min(importance + 0.2, 1.0)
        
        return importance
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        text_lower = text.lower()
        
        business_tags = {
            "meeting": ["meeting", "call", "appointment"],
            "email": ["email", "send", "reply"],
            "project": ["project", "deliverable", "milestone"],
            "client": ["client", "customer", "stakeholder"],
            "deadline": ["deadline", "due", "submit"],
            "research": ["research", "investigate", "analyze"],
            "planning": ["plan", "strategy", "roadmap"],
            "finance": ["budget", "cost", "payment", "invoice"]
        }
        
        for tag, keywords in business_tags.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _calculate_confidence(self, tasks: List[TaskEntry], text: str) -> float:
        """Calculate overall confidence score for extraction."""
        if not tasks:
            return 0.0
        
        text_length = len(text.split())
        task_density = len(tasks) / max(text_length / 10, 1)
        
        quality_score = 0.0
        for task in tasks:
            if task.due_date:
                quality_score += 0.2
            if task.task_type in [TaskType.DEADLINE, TaskType.MEETING]:
                quality_score += 0.1
            if any(verb in task.title.lower() for verb in ['create', 'schedule', 'call', 'review']):
                quality_score += 0.1
        
        quality_score = quality_score / len(tasks) if tasks else 0.0
        confidence = min(0.5 + (task_density * 0.3) + (quality_score * 0.2), 1.0)
        
        return confidence
    
    def _generate_suggestions(self, tasks: List[TaskEntry], text: str) -> List[str]:
        """Generate suggestions for improving task extraction."""
        suggestions = []
        
        if not tasks:
            suggestions.append("No tasks were detected. Try using more specific action words like 'need to', 'should', or 'must'.")
        
        tasks_without_dates = [t for t in tasks if not t.due_date]
        if tasks_without_dates:
            suggestions.append(f"{len(tasks_without_dates)} task(s) don't have due dates. Consider adding time references like 'by Friday' or 'in 3 days'.")
        
        vague_tasks = [t for t in tasks if len(t.title.split()) < 3]
        if vague_tasks:
            suggestions.append(f"{len(vague_tasks)} task(s) seem vague. Try to be more specific about what needs to be done.")
        
        return suggestions


# Global extractor instance
_task_extractor = None


def get_task_extractor() -> TaskExtractor:
    """Get a singleton instance of the task extractor."""
    global _task_extractor
    if _task_extractor is None:
        _task_extractor = TaskExtractor()
    return _task_extractor


def analyze_task_dependencies(tasks: List[TaskEntry]) -> List[TaskDependency]:
    """Analyze potential dependencies between tasks."""
    dependencies = []
    
    for i, task1 in enumerate(tasks):
        for j, task2 in enumerate(tasks):
            if i != j:
                # Simple dependency detection based on keywords
                if _has_dependency_relationship(task1, task2):
                    dependency = TaskDependency(
                        task_id=task1.id,
                        dependent_task_id=task2.id,
                        dependency_type=DependencyType.BLOCKS,
                        description=f"'{task1.title}' may need to be completed before '{task2.title}'"
                    )
                    dependencies.append(dependency)
    
    return dependencies


def _has_dependency_relationship(task1: TaskEntry, task2: TaskEntry) -> bool:
    """Check if two tasks have a dependency relationship."""
    # Simple heuristic: if task1 involves creating/preparing something
    # and task2 involves using/reviewing it
    creation_words = ["create", "build", "develop", "prepare", "write", "design"]
    usage_words = ["review", "analyze", "present", "submit", "send", "deliver"]
    
    task1_lower = task1.title.lower()
    task2_lower = task2.title.lower()
    
    task1_creates = any(word in task1_lower for word in creation_words)
    task2_uses = any(word in task2_lower for word in usage_words)
    
    return task1_creates and task2_uses


def calculate_priority_score(task: TaskEntry) -> float:
    """Calculate comprehensive priority score for task scheduling."""
    # Combine urgency, importance, and other factors
    urgency_weight = 0.4
    importance_weight = 0.4
    type_weight = 0.2
    
    # Task type scoring
    type_scores = {
        TaskType.DEADLINE: 0.9,
        TaskType.MEETING: 0.7,
        TaskType.ACTION: 0.5,
        TaskType.REVIEW: 0.4,
        TaskType.RESEARCH: 0.3,
        TaskType.REMINDER: 0.2
    }
    
    type_score = type_scores.get(task.task_type, 0.5)
    
    priority_score = (
        task.urgency_score * urgency_weight +
        task.importance_score * importance_weight +
        type_score * type_weight
    )
    
    return min(priority_score, 1.0)