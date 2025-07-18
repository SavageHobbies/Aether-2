"""
Database models for Aether AI Companion.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, VARCHAR

Base = declarative_base()


class UUID(TypeDecorator):
    """Platform-independent UUID type."""
    
    impl = VARCHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(VARCHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return str(value)


class JSONType(TypeDecorator):
    """JSON type that works across different databases."""
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Conversation(Base, TimestampMixin):
    """Conversation model for storing chat interactions."""
    
    __tablename__ = "conversations"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(UUID, nullable=False, index=True)
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    context_metadata = Column(JSONType, default=dict)
    
    # Relationships
    memory_references = relationship("ConversationMemoryRef", back_populates="conversation")
    extracted_tasks = relationship("Task", back_populates="source_conversation")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id})>"


class MemoryEntry(Base, TimestampMixin):
    """Memory entry model for long-term storage."""
    
    __tablename__ = "memory_entries"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    content = Column(Text, nullable=False)
    importance_score = Column(Float, default=1.0, nullable=False)
    tags = Column(JSONType, default=list)
    user_editable = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    conversation_refs = relationship("ConversationMemoryRef", back_populates="memory_entry")
    connections = relationship(
        "MemoryConnection",
        foreign_keys="MemoryConnection.from_memory_id",
        back_populates="from_memory"
    )
    
    def __repr__(self):
        return f"<MemoryEntry(id={self.id}, importance={self.importance_score})>"


class ConversationMemoryRef(Base):
    """Reference table linking conversations to memory entries."""
    
    __tablename__ = "conversation_memory_refs"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
    memory_entry_id = Column(UUID, ForeignKey("memory_entries.id"), nullable=False)
    relevance_score = Column(Float, default=1.0)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="memory_references")
    memory_entry = relationship("MemoryEntry", back_populates="conversation_refs")
    
    __table_args__ = (
        UniqueConstraint("conversation_id", "memory_entry_id"),
    )


class MemoryConnection(Base):
    """Connections between memory entries."""
    
    __tablename__ = "memory_connections"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    from_memory_id = Column(UUID, ForeignKey("memory_entries.id"), nullable=False)
    to_memory_id = Column(UUID, ForeignKey("memory_entries.id"), nullable=False)
    connection_strength = Column(Float, default=1.0)
    connection_type = Column(String(50), default="related")  # related, similar, opposite, etc.
    
    # Relationships
    from_memory = relationship("MemoryEntry", foreign_keys=[from_memory_id])
    to_memory = relationship("MemoryEntry", foreign_keys=[to_memory_id])
    
    __table_args__ = (
        UniqueConstraint("from_memory_id", "to_memory_id"),
    )


class Idea(Base, TimestampMixin):
    """Idea model for capturing thoughts and insights."""
    
    __tablename__ = "ideas"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    content = Column(Text, nullable=False)
    source = Column(String(20), nullable=False)  # desktop, mobile, voice, web
    processed = Column(Boolean, default=False, nullable=False)
    category = Column(String(100), nullable=True)
    priority_score = Column(Float, default=0.0, nullable=False)
    extra_metadata = Column(JSONType, default=dict)
    
    # Relationships
    converted_task = relationship("Task", back_populates="source_idea", uselist=False)
    connections = relationship(
        "IdeaConnection",
        foreign_keys="IdeaConnection.from_idea_id",
        back_populates="from_idea"
    )
    
    def __repr__(self):
        return f"<Idea(id={self.id}, source={self.source}, processed={self.processed})>"


class IdeaConnection(Base):
    """Connections between ideas."""
    
    __tablename__ = "idea_connections"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    from_idea_id = Column(UUID, ForeignKey("ideas.id"), nullable=False)
    to_idea_id = Column(UUID, ForeignKey("ideas.id"), nullable=False)
    connection_strength = Column(Float, default=1.0)
    connection_type = Column(String(50), default="related")
    
    # Relationships
    from_idea = relationship("Idea", foreign_keys=[from_idea_id])
    to_idea = relationship("Idea", foreign_keys=[to_idea_id])
    
    __table_args__ = (
        UniqueConstraint("from_idea_id", "to_idea_id"),
    )


class Task(Base, TimestampMixin):
    """Task model for managing actionable items."""
    
    __tablename__ = "tasks"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    priority = Column(Integer, nullable=False)  # 1=low, 2=medium, 3=high, 4=urgent
    status = Column(String(20), default="pending", nullable=False)  # pending, in_progress, completed, cancelled
    due_date = Column(DateTime, nullable=True)
    
    # Source tracking
    source_conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=True)
    source_idea_id = Column(UUID, ForeignKey("ideas.id"), nullable=True)
    
    # External integrations
    external_integrations = Column(JSONType, default=dict)  # Google Calendar, Monday.com IDs
    
    # Relationships
    source_conversation = relationship("Conversation", back_populates="extracted_tasks")
    source_idea = relationship("Idea", back_populates="converted_task")
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.dependent_task_id",
        back_populates="dependent_task"
    )
    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.prerequisite_task_id",
        back_populates="prerequisite_task"
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"


class TaskDependency(Base):
    """Task dependencies."""
    
    __tablename__ = "task_dependencies"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))
    dependent_task_id = Column(UUID, ForeignKey("tasks.id"), nullable=False)
    prerequisite_task_id = Column(UUID, ForeignKey("tasks.id"), nullable=False)
    dependency_type = Column(String(50), default="blocks")  # blocks, related, etc.
    
    # Relationships
    dependent_task = relationship("Task", foreign_keys=[dependent_task_id])
    prerequisite_task = relationship("Task", foreign_keys=[prerequisite_task_id])
    
    __table_args__ = (
        UniqueConstraint("dependent_task_id", "prerequisite_task_id"),
    )