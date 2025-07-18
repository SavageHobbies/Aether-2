"""
Unit tests for database models.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.models import (
    Base, ConversationModel, MemoryModel, IdeaModel, 
    TaskModel, SessionModel, IntegrationLogModel
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


class TestConversationModel:
    """Test ConversationModel functionality."""
    
    def test_create_conversation(self, db_session):
        """Test creating a conversation record."""
        session_id = str(uuid4())
        conversation = ConversationModel(
            session_id=session_id,
            user_input="Hello, how are you?",
            ai_response="I'm doing well, thank you for asking!",
            context_metadata={"source": "desktop"},
            input_tokens=5,
            output_tokens=8,
            relevance_score=0.8,
            importance_score=0.6
        )
        
        db_session.add(conversation)
        db_session.commit()
        
        # Verify the conversation was saved
        saved = db_session.query(ConversationModel).filter_by(session_id=session_id).first()
        assert saved is not None
        assert saved.user_input == "Hello, how are you?"
        assert saved.ai_response == "I'm doing well, thank you for asking!"
        assert saved.context_metadata["source"] == "desktop"
        assert saved.input_tokens == 5
        assert saved.output_tokens == 8
        assert saved.relevance_score == 0.8
        assert saved.importance_score == 0.6
        assert saved.created_at is not None
        assert saved.updated_at is not None
    
    def test_conversation_defaults(self, db_session):
        """Test conversation model defaults."""
        conversation = ConversationModel(
            session_id=str(uuid4()),
            user_input="Test input",
            ai_response="Test response"
        )
        
        db_session.add(conversation)
        db_session.commit()
        
        assert conversation.context_metadata == {}
        assert conversation.memory_references == []
        assert conversation.extracted_entities == []
        assert conversation.input_tokens == 0
        assert conversation.output_tokens == 0
        assert conversation.relevance_score == 0.0
        assert conversation.importance_score == 0.0


class TestMemoryModel:
    """Test MemoryModel functionality."""
    
    def test_create_memory(self, db_session):
        """Test creating a memory record."""
        memory = MemoryModel(
            content="User prefers morning meetings",
            memory_type="preference",
            category="scheduling",
            importance_score=8.5,
            recency_score=1.0,
            access_frequency=3,
            tags=["meetings", "schedule", "preference"],
            user_pinned=True,
            extra_metadata={"confidence": 0.9}
        )
        
        db_session.add(memory)
        db_session.commit()
        
        # Verify the memory was saved
        saved = db_session.query(MemoryModel).filter_by(content="User prefers morning meetings").first()
        assert saved is not None
        assert saved.memory_type == "preference"
        assert saved.category == "scheduling"
        assert saved.importance_score == 8.5
        assert saved.recency_score == 1.0
        assert saved.access_frequency == 3
        assert "meetings" in saved.tags
        assert saved.user_pinned is True
        assert saved.extra_metadata["confidence"] == 0.9
        assert saved.created_at is not None
        assert saved.last_accessed is not None
    
    def test_memory_defaults(self, db_session):
        """Test memory model defaults."""
        memory = MemoryModel(content="Test memory content")
        
        db_session.add(memory)
        db_session.commit()
        
        assert memory.memory_type == "general"
        assert memory.importance_score == 1.0
        assert memory.recency_score == 1.0
        assert memory.access_frequency == 0
        assert memory.tags == []
        assert memory.connections == []
        assert memory.source_conversations == []
        assert memory.user_editable is True
        assert memory.user_pinned is False
        assert memory.auto_generated is False
        assert memory.extra_metadata == {}
    
    def test_memory_scoring(self, db_session):
        """Test memory importance and recency scoring."""
        # High importance memory
        important_memory = MemoryModel(
            content="Critical business decision",
            importance_score=9.5,
            recency_score=1.0
        )
        
        # Old but accessed memory
        old_memory = MemoryModel(
            content="Old but useful info",
            importance_score=5.0,
            recency_score=0.3,
            access_frequency=10
        )
        
        db_session.add_all([important_memory, old_memory])
        db_session.commit()
        
        # Query by importance
        high_importance = db_session.query(MemoryModel).filter(
            MemoryModel.importance_score > 8.0
        ).all()
        assert len(high_importance) == 1
        assert high_importance[0].content == "Critical business decision"
        
        # Query by access frequency
        frequently_accessed = db_session.query(MemoryModel).filter(
            MemoryModel.access_frequency > 5
        ).all()
        assert len(frequently_accessed) == 1
        assert frequently_accessed[0].content == "Old but useful info"


class TestIdeaModel:
    """Test IdeaModel functionality."""
    
    def test_create_idea(self, db_session):
        """Test creating an idea record."""
        idea = IdeaModel(
            content="Build a mobile app for task management",
            source="mobile",
            category="product",
            priority_score=7.5,
            urgency_score=6.0,
            extra_metadata={"location": "office", "mood": "excited"}
        )
        
        db_session.add(idea)
        db_session.commit()
        
        # Verify the idea was saved
        saved = db_session.query(IdeaModel).filter_by(source="mobile").first()
        assert saved is not None
        assert saved.content == "Build a mobile app for task management"
        assert saved.source == "mobile"
        assert saved.category == "product"
        assert saved.priority_score == 7.5
        assert saved.urgency_score == 6.0
        assert saved.extra_metadata["location"] == "office"
        assert saved.processed is False
        assert saved.created_at is not None
    
    def test_idea_processing_workflow(self, db_session):
        """Test idea processing workflow."""
        idea = IdeaModel(
            content="Implement user authentication",
            source="desktop",
            processed=False
        )
        
        db_session.add(idea)
        db_session.commit()
        
        # Mark as processed
        idea.processed = True
        idea.processed_at = datetime.utcnow()
        idea.category = "development"
        idea.extracted_entities = ["authentication", "users", "security"]
        
        db_session.commit()
        
        # Verify processing
        saved = db_session.query(IdeaModel).filter_by(id=idea.id).first()
        assert saved.processed is True
        assert saved.processed_at is not None
        assert saved.category == "development"
        assert "authentication" in saved.extracted_entities


class TestTaskModel:
    """Test TaskModel functionality."""
    
    def test_create_task(self, db_session):
        """Test creating a task record."""
        task = TaskModel(
            title="Review quarterly reports",
            description="Analyze Q4 performance metrics",
            priority=3,
            status="pending",
            due_date=datetime.utcnow() + timedelta(days=7),
            external_integrations={"google_calendar": "event_123"},
            tags=["quarterly", "reports", "analysis"]
        )
        
        db_session.add(task)
        db_session.commit()
        
        # Verify the task was saved
        saved = db_session.query(TaskModel).filter_by(title="Review quarterly reports").first()
        assert saved is not None
        assert saved.description == "Analyze Q4 performance metrics"
        assert saved.priority == 3
        assert saved.status == "pending"
        assert saved.due_date is not None
        assert saved.external_integrations["google_calendar"] == "event_123"
        assert "quarterly" in saved.tags
        assert saved.sync_status == "pending"
    
    def test_task_status_workflow(self, db_session):
        """Test task status transitions."""
        task = TaskModel(
            title="Test task",
            description="Test description",
            priority=2,
            status="pending"
        )
        
        db_session.add(task)
        db_session.commit()
        
        # Start task
        task.status = "in_progress"
        db_session.commit()
        
        # Complete task
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        db_session.commit()
        
        # Verify status changes
        saved = db_session.query(TaskModel).filter_by(id=task.id).first()
        assert saved.status == "completed"
        assert saved.completed_at is not None
    
    def test_task_dependencies(self, db_session):
        """Test task dependency relationships."""
        task1 = TaskModel(title="Setup database", priority=4)
        task2 = TaskModel(title="Create API", priority=3)
        task3 = TaskModel(title="Build frontend", priority=2)
        
        db_session.add_all([task1, task2, task3])
        db_session.commit()
        
        # Set up dependencies: task2 depends on task1, task3 depends on task2
        task2.dependencies = [str(task1.id)]
        task3.dependencies = [str(task2.id)]
        
        # Set up blocking relationships
        task1.blocks = [str(task2.id)]
        task2.blocks = [str(task3.id)]
        
        db_session.commit()
        
        # Verify dependencies
        saved_task2 = db_session.query(TaskModel).filter_by(id=task2.id).first()
        saved_task3 = db_session.query(TaskModel).filter_by(id=task3.id).first()
        
        assert str(task1.id) in saved_task2.dependencies
        assert str(task2.id) in saved_task3.dependencies
        assert str(task2.id) in task1.blocks
        assert str(task3.id) in task2.blocks


class TestSessionModel:
    """Test SessionModel functionality."""
    
    def test_create_session(self, db_session):
        """Test creating a session record."""
        session = SessionModel(
            name="Morning Planning Session",
            conversation_count=5,
            context_summary="Discussed project priorities and deadlines",
            key_topics=["project management", "deadlines", "priorities"]
        )
        
        db_session.add(session)
        db_session.commit()
        
        # Verify the session was saved
        saved = db_session.query(SessionModel).filter_by(name="Morning Planning Session").first()
        assert saved is not None
        assert saved.conversation_count == 5
        assert saved.context_summary == "Discussed project priorities and deadlines"
        assert "project management" in saved.key_topics
        assert saved.is_active is True
        assert saved.created_at is not None
        assert saved.last_activity is not None


class TestIntegrationLogModel:
    """Test IntegrationLogModel functionality."""
    
    def test_create_integration_log(self, db_session):
        """Test creating an integration log record."""
        log = IntegrationLogModel(
            service="google_calendar",
            operation="create",
            entity_type="task",
            entity_id=str(uuid4()),
            external_id="cal_event_456",
            status="success",
            request_data={"title": "Meeting", "date": "2024-01-15"},
            response_data={"id": "cal_event_456", "status": "confirmed"}
        )
        
        db_session.add(log)
        db_session.commit()
        
        # Verify the log was saved
        saved = db_session.query(IntegrationLogModel).filter_by(service="google_calendar").first()
        assert saved is not None
        assert saved.operation == "create"
        assert saved.entity_type == "task"
        assert saved.external_id == "cal_event_456"
        assert saved.status == "success"
        assert saved.request_data["title"] == "Meeting"
        assert saved.response_data["status"] == "confirmed"
        assert saved.created_at is not None
    
    def test_integration_error_logging(self, db_session):
        """Test logging integration errors."""
        error_log = IntegrationLogModel(
            service="monday_com",
            operation="update",
            entity_type="task",
            entity_id=str(uuid4()),
            status="failed",
            error_message="API rate limit exceeded",
            request_data={"item_id": "123", "status": "done"}
        )
        
        db_session.add(error_log)
        db_session.commit()
        
        # Verify error logging
        saved = db_session.query(IntegrationLogModel).filter_by(status="failed").first()
        assert saved is not None
        assert saved.error_message == "API rate limit exceeded"
        assert saved.service == "monday_com"
        assert saved.operation == "update"


class TestModelRelationships:
    """Test relationships between models."""
    
    def test_conversation_to_task_relationship(self, db_session):
        """Test conversation to task extraction relationship."""
        # Create conversation
        conversation = ConversationModel(
            session_id=str(uuid4()),
            user_input="I need to review the budget by Friday",
            ai_response="I'll help you create a task for that."
        )
        
        db_session.add(conversation)
        db_session.commit()
        
        # Create task from conversation
        task = TaskModel(
            title="Review budget",
            description="Review budget by Friday",
            priority=3,
            source_conversation_id=conversation.id
        )
        
        db_session.add(task)
        db_session.commit()
        
        # Verify relationship
        saved_conversation = db_session.query(ConversationModel).filter_by(id=conversation.id).first()
        saved_task = db_session.query(TaskModel).filter_by(id=task.id).first()
        
        assert saved_task.source_conversation_id == conversation.id
        assert len(saved_conversation.extracted_tasks) == 1
        assert saved_conversation.extracted_tasks[0].id == task.id
    
    def test_idea_to_task_conversion(self, db_session):
        """Test idea to task conversion relationship."""
        # Create idea
        idea = IdeaModel(
            content="Create a customer feedback system",
            source="desktop",
            priority_score=8.0
        )
        
        db_session.add(idea)
        db_session.commit()
        
        # Convert to task
        task = TaskModel(
            title="Build customer feedback system",
            description="Implement system for collecting customer feedback",
            priority=4,
            source_idea_id=idea.id
        )
        
        db_session.add(task)
        db_session.commit()
        
        # Update idea
        idea.converted_to_task_id = task.id
        idea.processed = True
        db_session.commit()
        
        # Verify relationship
        saved_idea = db_session.query(IdeaModel).filter_by(id=idea.id).first()
        saved_task = db_session.query(TaskModel).filter_by(id=task.id).first()
        
        assert saved_idea.converted_to_task_id == task.id
        assert saved_task.source_idea_id == idea.id
        assert saved_task.source_idea.id == idea.id