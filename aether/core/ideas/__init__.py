"""
Idea processing system for Aether AI Companion.
"""

from .processor import IdeaProcessor, get_idea_processor
from .connections import IdeaConnectionEngine, get_idea_connection_engine
from .types import IdeaEntry, IdeaQuery, IdeaSearchResult, IdeaCategory, IdeaPriority
from .converter import ConversionType, TaskEntry, CalendarEvent, ProjectEntry, IdeaToActionConverter, get_idea_converter

__all__ = [
    "IdeaProcessor",
    "get_idea_processor",
    "IdeaConnectionEngine",
    "get_idea_connection_engine",
    "IdeaToActionConverter",
    "get_idea_converter",
    "ConversionType",
    "TaskEntry",
    "CalendarEvent",
    "ProjectEntry",
    "IdeaEntry",
    "IdeaQuery", 
    "IdeaSearchResult",
    "IdeaCategory",
    "IdeaPriority"
]