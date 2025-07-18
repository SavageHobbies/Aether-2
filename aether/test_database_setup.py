"""
Test script for database setup and models.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database.connection import DatabaseManager, initialize_database
from core.database.models import Conversation, Idea, MemoryEntry, Task


async def test_database_setup():
    """Test database setup and basic operations."""
    print("🔧 Testing Aether database setup...")
    
    # Initialize database
    db_path = Path("test_aether.db")
    if db_path.exists():
        db_path.unlink()  # Remove existing test database
    
    database_url = f"sqlite:///{db_path}"
    db_manager = initialize_database(database_url, echo=True)
    
    try:
        # Create tables
        print("📋 Creating database tables...")
        await db_manager.create_tables_async()
        print("✅ Tables created successfully")
        
        # Test basic operations
        print("🧪 Testing basic database operations...")
        
        async with db_manager.get_async_session() as session:
            # Create a memory entry
            memory = MemoryEntry(
                content="This is a test memory entry",
                importance_score=0.8,
                tags=["test", "memory"]
            )
            session.add(memory)
            await session.flush()  # Get the ID
            
            # Create a conversation
            conversation = Conversation(
                session_id="test-session-123",
                user_input="Hello, Aether!",
                ai_response="Hello! How can I help you today?",
                context_metadata={"test": True}
            )
            session.add(conversation)
            await session.flush()
            
            # Create an idea
            idea = Idea(
                content="Build an AI companion for business management",
                source="desktop",
                category="project",
                priority_score=0.9,
                extra_metadata={"inspiration": "personal need"}
            )
            session.add(idea)
            await session.flush()
            
            # Create a task
            task = Task(
                title="Set up database schema",
                description="Create SQLAlchemy models and migrations",
                priority=3,  # high priority
                status="completed",
                source_idea_id=idea.id
            )
            session.add(task)
            
            await session.commit()
            
            print(f"✅ Created memory entry: {memory.id}")
            print(f"✅ Created conversation: {conversation.id}")
            print(f"✅ Created idea: {idea.id}")
            print(f"✅ Created task: {task.id}")
        
        # Test querying
        print("🔍 Testing database queries...")
        
        async with db_manager.get_async_session() as session:
            from sqlalchemy import select
            
            # Query conversations
            result = await session.execute(select(Conversation))
            conversations = result.scalars().all()
            print(f"📊 Found {len(conversations)} conversations")
            
            # Query ideas
            result = await session.execute(select(Idea))
            ideas = result.scalars().all()
            print(f"💡 Found {len(ideas)} ideas")
            
            # Query tasks
            result = await session.execute(select(Task))
            tasks = result.scalars().all()
            print(f"📝 Found {len(tasks)} tasks")
            
            # Query memory entries
            result = await session.execute(select(MemoryEntry))
            memories = result.scalars().all()
            print(f"🧠 Found {len(memories)} memory entries")
        
        print("🎉 Database setup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_manager.close()
        # Clean up test database (Windows may have file locks)
        try:
            if db_path.exists():
                db_path.unlink()
        except PermissionError:
            print(f"⚠️  Could not delete test file {db_path} (file in use)")


def test_database_sync():
    """Test synchronous database operations."""
    print("🔧 Testing synchronous database operations...")
    
    # Initialize database
    db_path = Path("test_aether_sync.db")
    if db_path.exists():
        db_path.unlink()
    
    database_url = f"sqlite:///{db_path}"
    db_manager = initialize_database(database_url, echo=False)
    
    try:
        # Create tables
        print("📋 Creating database tables (sync)...")
        db_manager.create_tables()
        print("✅ Tables created successfully")
        
        # Test basic operations
        print("🧪 Testing basic database operations (sync)...")
        
        session = db_manager.get_session()
        try:
            # Create test data
            memory = MemoryEntry(
                content="Synchronous test memory",
                importance_score=0.7,
                tags=["sync", "test"]
            )
            session.add(memory)
            session.commit()
            
            print(f"✅ Created memory entry (sync): {memory.id}")
            
            # Query data
            memories = session.query(MemoryEntry).all()
            print(f"🧠 Found {len(memories)} memory entries (sync)")
            
        finally:
            session.close()
        
        print("🎉 Synchronous database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Synchronous database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up (Windows may have file locks)
        try:
            if db_path.exists():
                db_path.unlink()
        except PermissionError:
            print(f"⚠️  Could not delete test file {db_path} (file in use)")


async def main():
    """Main test function."""
    print("🚀 Starting Aether database tests...\n")
    
    # Test synchronous operations
    sync_success = test_database_sync()
    print()
    
    # Test asynchronous operations
    async_success = await test_database_setup()
    print()
    
    if sync_success and async_success:
        print("🎉 All database tests passed!")
        return True
    else:
        print("❌ Some database tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)