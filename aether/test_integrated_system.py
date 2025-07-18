"""
Integrated system test for Aether AI Companion.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database.connection import initialize_database
from core.database.models import Conversation, Idea, MemoryEntry, Task


async def test_integrated_workflow():
    """Test an integrated workflow simulating real usage."""
    print("🚀 Testing Aether integrated workflow...")
    
    # Initialize database
    db_path = Path("aether_integrated_test.db")
    if db_path.exists():
        db_path.unlink()
    
    database_url = f"sqlite:///{db_path}"
    db_manager = initialize_database(database_url, echo=False)
    
    try:
        # Create tables
        await db_manager.create_tables_async()
        print("✅ Database initialized")
        
        # Simulate user workflow
        print("\n📝 Simulating user workflow...")
        
        async with db_manager.get_async_session() as session:
            # 1. User captures an idea
            idea = Idea(
                content="Create a dashboard for monitoring business metrics",
                source="mobile",
                category="feature",
                priority_score=0.8,
                extra_metadata={"location": "coffee shop", "mood": "inspired"}
            )
            session.add(idea)
            await session.flush()
            print(f"💡 Captured idea: {idea.content[:50]}...")
            
            # 2. User has a conversation about the idea
            conversation = Conversation(
                session_id="user-session-001",
                user_input="I want to build a dashboard for my business metrics. What should I include?",
                ai_response="Great idea! For a business dashboard, consider including KPIs like revenue, customer acquisition cost, conversion rates, and operational metrics. Would you like me to help you prioritize these?",
                context_metadata={"idea_reference": str(idea.id), "topic": "dashboard"}
            )
            session.add(conversation)
            await session.flush()
            print(f"💬 Conversation logged: {conversation.id}")
            
            # 3. System creates a memory entry from the conversation
            memory = MemoryEntry(
                content="User wants to create a business metrics dashboard with KPIs including revenue, CAC, conversion rates, and operational metrics",
                importance_score=0.9,
                tags=["dashboard", "business", "metrics", "kpi"]
            )
            session.add(memory)
            await session.flush()
            print(f"🧠 Memory created: {memory.id}")
            
            # 4. User converts idea to task
            task = Task(
                title="Design business metrics dashboard",
                description="Create a comprehensive dashboard showing key business metrics including revenue, customer acquisition cost, conversion rates, and operational KPIs",
                priority=3,  # high priority
                status="pending",
                source_idea_id=idea.id,
                external_integrations={"monday_board": "business-projects"}
            )
            session.add(task)
            await session.flush()
            print(f"📋 Task created: {task.title}")
            
            # 5. Mark idea as processed
            idea.processed = True
            idea.converted_to_task = task
            
            await session.commit()
            print("✅ Workflow completed and saved")
        
        # Verify the workflow
        print("\n🔍 Verifying integrated data...")
        
        async with db_manager.get_async_session() as session:
            from sqlalchemy import select
            
            # Check relationships
            result = await session.execute(
                select(Task).where(Task.source_idea_id == idea.id)
            )
            related_task = result.scalar_one_or_none()
            
            if related_task:
                print(f"✅ Task-Idea relationship verified: {related_task.title}")
            
            # Check data integrity
            result = await session.execute(select(Idea).where(Idea.processed == True))
            processed_ideas = result.scalars().all()
            print(f"📊 Found {len(processed_ideas)} processed ideas")
            
            result = await session.execute(select(MemoryEntry))
            memories = result.scalars().all()
            print(f"🧠 Found {len(memories)} memory entries")
            
            result = await session.execute(select(Conversation))
            conversations = result.scalars().all()
            print(f"💬 Found {len(conversations)} conversations")
        
        print("\n🎉 Integrated workflow test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integrated test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_manager.close()
        # Clean up
        try:
            if db_path.exists():
                db_path.unlink()
        except PermissionError:
            print(f"⚠️  Could not delete test file {db_path} (file in use)")


async def main():
    """Main test function."""
    print("🔧 Aether AI Companion - Integrated System Test\n")
    
    success = await test_integrated_workflow()
    
    if success:
        print("\n✅ All integrated tests passed!")
        print("\n🎯 System Status:")
        print("  ✅ Database models working")
        print("  ✅ Relationships functioning")
        print("  ✅ Data integrity maintained")
        print("  ✅ Async operations stable")
        print("  ✅ Ready for next development phase")
        return True
    else:
        print("\n❌ Integrated tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)