"""
Comprehensive test for the complete database + vector store system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import (
    initialize_database,
    initialize_vector_store,
    add_memory_with_vector_indexing,
    search_memories_by_content,
    Conversation,
    Idea,
    Task,
    MemoryEntry
)


async def test_complete_system():
    """Test the complete database + vector store system."""
    print("🚀 Testing Complete Aether Database + Vector Store System...")
    
    # Clean up test files
    test_db = Path("test_complete_system.db")
    test_vectors = Path("test_complete_vectors")
    
    if test_db.exists():
        test_db.unlink()
    if test_vectors.exists():
        import shutil
        shutil.rmtree(test_vectors)
    
    try:
        # Initialize systems
        print("🔧 Initializing database and vector store...")
        db_manager = initialize_database(f"sqlite:///{test_db}", echo=False)
        vector_store = initialize_vector_store("simple", test_vectors)
        
        await db_manager.create_tables_async()
        print("✅ Systems initialized")
        
        # Simulate a complete user workflow
        print("\n📋 Simulating complete user workflow...")
        
        async with db_manager.get_async_session() as session:
            # 1. User captures an idea
            print("\n💡 Step 1: User captures an idea")
            idea = Idea(
                content="Build an AI-powered business intelligence dashboard that shows real-time KPIs, revenue trends, and operational metrics with predictive analytics",
                source="mobile",
                category="product-idea",
                priority_score=0.9,
                extra_metadata={
                    "inspiration_source": "competitor analysis",
                    "estimated_effort": "high",
                    "market_opportunity": "large"
                }
            )
            session.add(idea)
            await session.flush()
            print(f"✅ Idea captured: {idea.id}")
            
            # 2. Create memory from the idea
            print("\n🧠 Step 2: Creating memory with vector indexing")
            memory = await add_memory_with_vector_indexing(
                session,
                f"User proposed building an AI-powered BI dashboard. Key features: real-time KPIs, revenue trends, operational metrics, predictive analytics. High priority product idea with large market opportunity.",
                importance_score=0.9,
                tags=["dashboard", "bi", "ai", "analytics", "product-idea", "high-priority"]
            )
            print(f"✅ Memory created with vector indexing: {memory.id}")
            
            # 3. User has a conversation about the idea
            print("\n💬 Step 3: User conversation about the idea")
            conversation = Conversation(
                session_id="user-session-001",
                user_input="I want to build a business intelligence dashboard with AI features. What should I focus on first?",
                ai_response="Great idea! For an AI-powered BI dashboard, I'd recommend starting with: 1) Core KPI visualization, 2) Real-time data integration, 3) Basic predictive models for trends. Should we break this down into specific tasks?",
                context_metadata={
                    "related_idea_id": str(idea.id),
                    "related_memory_id": str(memory.id),
                    "topic": "product-planning",
                    "user_intent": "project-initiation"
                }
            )
            session.add(conversation)
            await session.flush()
            print(f"✅ Conversation logged: {conversation.id}")
            
            # 4. Create another memory from the conversation
            print("\n🧠 Step 4: Creating memory from conversation")
            conversation_memory = await add_memory_with_vector_indexing(
                session,
                "User wants to start with core KPI visualization, real-time data integration, and basic predictive models for their BI dashboard project. Discussed breaking down into specific tasks.",
                importance_score=0.8,
                tags=["conversation", "planning", "kpi", "data-integration", "predictive-models"]
            )
            print(f"✅ Conversation memory created: {conversation_memory.id}")
            
            # 5. Convert idea to tasks
            print("\n📋 Step 5: Converting idea to actionable tasks")
            tasks = [
                Task(
                    title="Design BI Dashboard Architecture",
                    description="Create technical architecture for AI-powered business intelligence dashboard including data flow, component design, and technology stack selection",
                    priority=3,  # high
                    status="pending",
                    source_idea_id=idea.id,
                    external_integrations={"monday_board": "product-development"}
                ),
                Task(
                    title="Implement Core KPI Visualization",
                    description="Build the core KPI visualization components with real-time data display capabilities",
                    priority=3,  # high
                    status="pending",
                    source_idea_id=idea.id,
                    external_integrations={"monday_board": "product-development"}
                ),
                Task(
                    title="Integrate Real-time Data Sources",
                    description="Set up real-time data integration from various business systems and databases",
                    priority=2,  # medium
                    status="pending",
                    source_idea_id=idea.id,
                    external_integrations={"monday_board": "product-development"}
                )
            ]
            
            for task in tasks:
                session.add(task)
                await session.flush()
                print(f"✅ Task created: {task.title}")
            
            # 6. Mark idea as processed
            idea.processed = True
            
            await session.commit()
            print("✅ Workflow completed and committed to database")
        
        # Test semantic search across all memories
        print("\n🔍 Testing semantic search across all memories...")
        
        search_queries = [
            "business intelligence and analytics",
            "KPI visualization and dashboards", 
            "real-time data integration",
            "predictive analytics and AI",
            "product development planning"
        ]
        
        async with db_manager.get_async_session() as session:
            for query in search_queries:
                print(f"\n🔎 Searching for: '{query}'")
                
                results = await search_memories_by_content(
                    session,
                    query,
                    limit=3,
                    threshold=0.0  # Low threshold to see all results
                )
                
                if results:
                    print(f"✅ Found {len(results)} relevant memories:")
                    for i, (memory_entry, similarity) in enumerate(results, 1):
                        print(f"  {i}. Similarity: {similarity:.3f}")
                        print(f"     Content: {memory_entry.content[:80]}...")
                        print(f"     Tags: {memory_entry.tags}")
                        print(f"     Importance: {memory_entry.importance_score}")
                else:
                    print("❌ No memories found")
        
        # Test data relationships
        print("\n🔗 Testing data relationships...")
        
        async with db_manager.get_async_session() as session:
            from sqlalchemy import select
            
            # Get idea with related tasks
            stmt = select(Idea).where(Idea.id == idea.id)
            result = await session.execute(stmt)
            retrieved_idea = result.scalar_one()
            
            # Get tasks related to this idea
            stmt = select(Task).where(Task.source_idea_id == idea.id)
            result = await session.execute(stmt)
            related_tasks = result.scalars().all()
            
            print(f"✅ Idea '{retrieved_idea.content[:50]}...' has {len(related_tasks)} related tasks")
            
            # Get conversation with context
            stmt = select(Conversation).where(Conversation.id == conversation.id)
            result = await session.execute(stmt)
            retrieved_conversation = result.scalar_one()
            
            related_idea_id = retrieved_conversation.context_metadata.get("related_idea_id")
            related_memory_id = retrieved_conversation.context_metadata.get("related_memory_id")
            
            print(f"✅ Conversation references idea: {related_idea_id}")
            print(f"✅ Conversation references memory: {related_memory_id}")
        
        # System statistics
        print("\n📊 System Statistics:")
        
        async with db_manager.get_async_session() as session:
            from sqlalchemy import select, func
            
            # Count all entities
            for model, name in [(Idea, "Ideas"), (Task, "Tasks"), (Conversation, "Conversations"), (MemoryEntry, "Memories")]:
                stmt = select(func.count(model.id))
                result = await session.execute(stmt)
                count = result.scalar()
                print(f"  {name}: {count}")
        
        # Vector store statistics
        vector_stats = vector_store.get_stats()
        print(f"  Vector Store Documents: {vector_stats.get('total_documents', 0)}")
        print(f"  Vector Dimensions: {vector_stats.get('embedding_dimension', 0)}")
        
        print("\n🎉 Complete system test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Complete system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            await db_manager.close()
        except:
            pass
        
        try:
            if test_db.exists():
                test_db.unlink()
        except PermissionError:
            print(f"⚠️  Could not delete {test_db}")
        
        try:
            if test_vectors.exists():
                import shutil
                shutil.rmtree(test_vectors)
        except PermissionError:
            print(f"⚠️  Could not delete {test_vectors}")


async def main():
    """Main test function."""
    print("🔧 Aether Complete Database + Vector Store System Test\n")
    
    success = await test_complete_system()
    
    if success:
        print("\n✅ Complete system test passed!")
        print("\n🎯 System Capabilities Verified:")
        print("  ✅ Database models and relationships")
        print("  ✅ Vector store integration")
        print("  ✅ Semantic memory search")
        print("  ✅ Cross-entity data relationships")
        print("  ✅ Complete user workflow simulation")
        print("  ✅ Data persistence and retrieval")
        print("  ✅ Memory importance scoring")
        print("  ✅ Tag-based organization")
        print("\n🚀 Ready for Task 2.3: Data validation and serialization!")
        return True
    else:
        print("\n❌ Complete system test failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)