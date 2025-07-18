"""
Database helper methods for idea processor.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from core.database.models import Idea
from .types import IdeaEntry, IdeaCategory, IdeaPriority, IdeaStatus, IdeaQuery


def db_idea_to_entry(db_idea: Idea) -> IdeaEntry:
    """Convert database Idea model to IdeaEntry."""
    metadata = db_idea.extra_metadata or {}
    
    # Parse category
    category = IdeaCategory.OTHER
    try:
        if db_idea.category:
            category = IdeaCategory(db_idea.category)
    except ValueError:
        pass
    
    # Parse priority from metadata
    priority = IdeaPriority.MEDIUM
    try:
        if metadata.get("priority"):
            priority = IdeaPriority(metadata["priority"])
    except ValueError:
        pass
    
    # Parse status from metadata
    status = IdeaStatus.CAPTURED
    try:
        if metadata.get("status"):
            status = IdeaStatus(metadata["status"])
    except ValueError:
        pass
    
    # Parse suggested categories
    suggested_categories = []
    try:
        if metadata.get("suggested_categories"):
            suggested_categories = [
                IdeaCategory(cat) for cat in metadata["suggested_categories"]
                if cat in [c.value for c in IdeaCategory]
            ]
    except (ValueError, TypeError):
        pass
    
    return IdeaEntry(
        id=str(db_idea.id),
        content=db_idea.content,
        title=metadata.get("title"),
        category=category,
        priority=priority,
        status=status,
        keywords=metadata.get("keywords", []),
        tags=metadata.get("tags", []),
        source=db_idea.source,
        context=metadata.get("context"),
        created_at=db_idea.created_at,
        updated_at=db_idea.updated_at,
        processed_at=metadata.get("processed_at"),
        extracted_keywords=metadata.get("extracted_keywords", []),
        suggested_categories=suggested_categories,
        confidence_score=metadata.get("confidence_score", 0.0),
        related_ideas=metadata.get("related_ideas", []),
        parent_idea=metadata.get("parent_idea"),
        sub_ideas=metadata.get("sub_ideas", []),
        converted_to_tasks=metadata.get("converted_to_tasks", []),
        converted_to_events=metadata.get("converted_to_events", [])
    )


def priority_to_score(priority: IdeaPriority) -> float:
    """Convert priority enum to numeric score."""
    priority_scores = {
        IdeaPriority.LOW: 0.25,
        IdeaPriority.MEDIUM: 0.5,
        IdeaPriority.HIGH: 0.75,
        IdeaPriority.URGENT: 1.0
    }
    return priority_scores.get(priority, 0.5)


def score_to_priority(score: float) -> IdeaPriority:
    """Convert numeric score to priority enum."""
    if score >= 0.9:
        return IdeaPriority.URGENT
    elif score >= 0.7:
        return IdeaPriority.HIGH
    elif score >= 0.4:
        return IdeaPriority.MEDIUM
    else:
        return IdeaPriority.LOW


def build_idea_filters(query: IdeaQuery) -> Dict:
    """Build database filters from IdeaQuery."""
    filters = {}
    
    if query.categories:
        filters["category"] = [cat.value for cat in query.categories]
    
    if query.statuses:
        # Status is stored in metadata, so we'll handle this in the query logic
        pass
    
    if query.source:
        filters["source"] = query.source
    
    if query.date_range:
        filters["date_range"] = query.date_range
    
    return filters