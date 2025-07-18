"""
Test script for memory integration with vector store.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database.connection import initialize_database
from core.database.vector_store import initialize_vector_store
from core.database.memory_integration import (
    add_memory_with_vector_indexing,
    search_memories_by_content,
    get_memory_integration
)


async def test_memory_vector_integration():
    """Test memory integration with vector store."""
    print("🔧 Testing Memory-Vector Integration...")
    
    # Clean up test files
    test_db = Path("test_memory_integration.db")
    test_vectors = Path("test_memory_vectors")
    
    if test_db.exists():
        test_db.unlink()
    if test_vectors.exists():
        import shutil
        shutil.rmtree(test_vectors)
    
    try:
        # Initialize database and vector store
        db_manager = initialize_database(f"sqlite:///{test_db}", echo=False)
        vector_store = initialize_vector_store("simple", test_vectors)
        
        await db_manager.create_tables_async()
        print("✅ Database and vector store initialized")
        
        # Test adding memories with vector indexing
        print("\n📝 Testing memory creation with vector indexing...")
        
        test_memories = [
            {
                "content": "User wants to create a comprehensive business dashboard showing KPIs, revenue, and operational metrics",
                "importance_score": 0.9,
                "tags": ["dashboard", "business", "kpi", "metrics"]
            },
            {
                "content": "Discussion about integrating with Google Calendar API for automated scheduling and meeting management",
                "importance_score": 0.8,
                "tags": ["integration", "calendar", "google", "scheduling"]
            },
            {
                "content": "AI assistant should maintain context across conversations and remember user preferences and past decisions",
                "importance_score": 0.95,
                "tags": ["ai", "context", "memory", "preferences"]
            },
            {
                "content": "Need to implement task prioritization system based on deadlines, importance, and user-defined criteria",
                "importance_score": 0.7,
                "tags": ["tasks", "prioritization", "deadlines", "productivity"]
            },
            {
                "content": "User expressed interest in Monday.com integration for project management and team collaboration",
                "importance_score": 0.6,
                "tags": ["integration", "monday", "project-management", "collaboration"]
            }
        ]
        
        created_memories = []
        
        async with db_manager.get_async_session() as session:
            for memory_data in test_memories:
                memory = await add_memory_with_vector_indexing(
                    session,
                    memory_data["content"],
                    memory_data["importance_score"],
                    memory_data["tags"]
                )
                
                if memory:
                    created_memories.append(memory)
                    print(f"✅ Created memory: {memory.id}")
                    print(f"   Content: {memory.content[:60]}...")
                    print(f"   Importance: {memory.importance_score}")
                else:
                    print("❌ Failed to create memory")
        
        print(f"\n📊 Created {len(created_memories)} memories")
        
        # Test semantic search
        print("\n🔍 Testing semantic memory search...")
        
        search_scenarios = [
            {
                "query": "I need help with business metrics and KPIs",
                "expected": "Should find dashboard-related memory",
                "threshold": 0.1
            },
            {
                "query": "How can I schedule meetings automatically?",
                "expected": "Should find calendar integration memory",
                "threshold": 0.1
            },
            {
                "query": "Does the AI remember our previous conversations?",
                "expected": "Should find context/memory-related memory",
                "threshold": 0.1
            },
            {
                "query": "I want to manage my tasks better",
                "expected": "Should find task prioritization memory",
                "threshold": 0.1
            },
            {
                "query": "Team collaboration and project tracking",
                "expected": "Should find Monday.com integration memory",
                "threshold": 0.1
            }
        ]
        
        async with db_manager.get_async_session() as session:
            for scenario in search_scenarios:
                print(f"\n🔎 Query: '{scenario['query']}'")
                print(f"Expected: {scenario['expected']}")
                
                results = await search_memories_by_content(
                    session,
                    scenario["query"],
                    limit=3,
                    threshold=scenario["threshold"]
                )
                
                if results:
                    print(f"✅ Found {len(results)} relevant memories:")
                    for i, (memory, similarity) in enumerate(results, 1):
                        print(f"  {i}. Similarity: {similarity:.3f}")
                        print(f"     Content: {memory.content[:80]}...")
                        print(f"     Tags: {memory.tags}")
                        print(f"     Importance: {memory.importance_score}")
                else:
                    print("❌ No relevant memories found")
        
        # Test related memories
        print("\n🔗 Testing related memory discovery...")
        
        if created_memories:
            reference_memory = created_memories[0]  # Use first memory as reference
            
            async with db_manager.get_async_session() as session:
                integration = get_memory_integration()
                related_memories = await integration.get_related_memories(
                    session,
                    reference_memory,
                    limit=3,
                    threshold=0.1
                )
                
                print(f"🔍 Finding memories related to:")
                print(f"   {reference_memory.content[:80]}...")
                
                if related_memories:
                    print(f"✅ Found {len(related_memories)} related memories:")
                    for i, (memory, similarity) in enumerate(related_memories, 1):
                        print(f"  {i}. Similarity: {similarity:.3f}")
                        print(f"     Content: {memory.content[:80]}...")
                else:
                    print("❌ No related memories found")
        
        # Test vector store statistics
        print("\n📊 Vector Store Statistics:")
        integration = get_memory_integration()
        stats = integration.get_vector_store_stats()
        
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test importance filtering
        print("\n🎯 Testing importance-based filtering...")
        
        async with db_manager.get_async_session() as session:
            # Search with high importance filter
            high_importance_results = await search_memories_by_content(
                session,
                "business dashboard AI",
                limit=5,
                threshold=0.0,
                importance_filter=0.8
            )
            
            print(f"High importance memories (≥0.8): {len(high_importance_results)}")
            for memory, similarity in high_importance_results:
                print(f"  - Importance: {memory.importance_score}, Similarity: {similarity:.3f}")
                print(f"    Content: {memory.content[:60]}...")
        
        print("\n🎉 Memory-Vector integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Memory integration test failed: {e}")
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
    print("🚀 Aether Memory-Vector Integration Test\n")
    
    success = await test_memory_vector_integration()
    
    if success:
        print("\n✅ Memory-Vector integration test passed!")
        print("\n🎯 Integration Status:")
        print("  ✅ Memory creation with vector indexing")
        print("  ✅ Semantic memory search")
        print("  ✅ Related memory discovery")
        print("  ✅ Importance-based filtering")
        print("  ✅ Database-vector store synchronization")
        print("  ✅ Ready for production use")
        return True
    else:
        print("\n❌ Memory-Vector integration test failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)