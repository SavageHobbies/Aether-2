#!/usr/bin/env python3
"""
Test script for the memory management system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from core.memory import MemoryManager, MemoryType, MemoryEntry, MemoryQuery
from core.ai import initialize_ai_provider
from core.database import initialize_database
from core.database.vector_store import initialize_vector_store
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_memory_storage():
    """Test basic memory storage functionality."""
    print("\n=== Testing Memory Storage ===")
    
    memory_manager = MemoryManager()
    
    # Test storing different types of memories
    test_memories = [
        {
            "content": "User prefers morning meetings and dislikes late afternoon calls",
            "memory_type": MemoryType.PREFERENCE,
            "importance_score": 0.8,
            "tags": ["meetings", "schedule", "preferences"]
        },
        {
            "content": "Discussed creating a business dashboard with revenue and KPI tracking",
            "memory_type": MemoryType.CONVERSATION,
            "importance_score": 0.9,
            "tags": ["dashboard", "business", "kpi"],
            "source": "conversation_001"
        },
        {
            "content": "Task: Implement user authentication system with OAuth2",
            "memory_type": MemoryType.TASK,
            "importance_score": 0.7,
            "tags": ["authentication", "oauth2", "security"]
        },
        {
            "content": "User's company is called TechCorp and they work in the fintech industry",
            "memory_type": MemoryType.FACT,
            "importance_score": 0.9,
            "tags": ["company", "industry", "fintech"]
        },
        {
            "content": "Idea: Create a mobile app for expense tracking with receipt scanning",
            "memory_type": MemoryType.IDEA,
            "importance_score": 0.6,
            "tags": ["mobile", "expenses", "receipts", "scanning"]
        }
    ]
    
    stored_memories = []
    for memory_data in test_memories:
        try:
            memory = await memory_manager.store_memory(**memory_data)
            stored_memories.append(memory)
            print(f"✓ Stored {memory.memory_type.value} memory: {memory.content[:50]}...")
        except Exception as e:
            print(f"✗ Failed to store memory: {e}")
    
    print(f"Successfully stored {len(stored_memories)} memories")
    return stored_memories


async def test_memory_search():
    """Test memory search functionality."""
    print("\n=== Testing Memory Search ===")
    
    memory_manager = MemoryManager()
    
    # Test different search queries
    test_queries = [
        {
            "query_text": "business dashboard metrics",
            "description": "Business-related search"
        },
        {
            "query_text": "user preferences and settings",
            "description": "Preference search"
        },
        {
            "query_text": "authentication security",
            "description": "Technical search"
        },
        {
            "query_text": "mobile app development",
            "description": "Development search"
        },
        {
            "query_text": "TechCorp fintech company",
            "description": "Company information search"
        }
    ]
    
    for query_data in test_queries:
        try:
            query = MemoryQuery(
                query_text=query_data["query_text"],
                max_results=5,
                similarity_threshold=0.6
            )
            
            results = await memory_manager.search_memories(query)
            
            print(f"\n{query_data['description']}:")
            print(f"Query: '{query_data['query_text']}'")
            print(f"Found {len(results)} results:")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result.memory.memory_type.value}] {result.memory.content[:60]}...")
                print(f"     Similarity: {result.similarity_score:.3f}, Relevance: {result.relevance_score:.3f}")
                if result.explanation:
                    print(f"     Reason: {result.explanation}")
            
        except Exception as e:
            print(f"✗ Search failed for '{query_data['query_text']}': {e}")


async def test_memory_updates():
    """Test memory update functionality."""
    print("\n=== Testing Memory Updates ===")
    
    memory_manager = MemoryManager()
    
    # First, store a memory to update
    memory = await memory_manager.store_memory(
        content="Original task: Set up development environment",
        memory_type=MemoryType.TASK,
        importance_score=0.5,
        tags=["development", "setup"]
    )
    
    print(f"Original memory: {memory.content}")
    print(f"Original importance: {memory.importance_score}")
    print(f"Original tags: {memory.tags}")
    
    # Update the memory
    updated_memory = await memory_manager.update_memory(
        memory_id=memory.id,
        content="Updated task: Set up development environment with Docker and CI/CD",
        importance_score=0.8,
        tags=["development", "setup", "docker", "cicd"]
    )
    
    if updated_memory:
        print(f"\n✓ Memory updated successfully")
        print(f"Updated content: {updated_memory.content}")
        print(f"Updated importance: {updated_memory.importance_score}")
        print(f"Updated tags: {updated_memory.tags}")
    else:
        print("✗ Failed to update memory")


async def test_memory_consolidation():
    """Test memory consolidation functionality."""
    print("\n=== Testing Memory Consolidation ===")
    
    memory_manager = MemoryManager()
    
    # Get initial stats
    initial_stats = await memory_manager.get_memory_stats()
    print(f"Initial memory count: {initial_stats.total_memories}")
    print(f"Average importance: {initial_stats.average_importance:.3f}")
    
    # Force consolidation
    consolidation_result = await memory_manager.consolidate_memories(force=True)
    
    print(f"\nConsolidation results:")
    print(f"Summary: {consolidation_result.summary}")
    print(f"Consolidated: {consolidation_result.consolidated_count}")
    print(f"Deleted: {consolidation_result.deleted_count}")
    print(f"Updated: {consolidation_result.updated_count}")
    
    if consolidation_result.details:
        print("Details:")
        for detail in consolidation_result.details:
            print(f"  - {detail}")
    
    # Get final stats
    final_stats = await memory_manager.get_memory_stats()
    print(f"\nFinal memory count: {final_stats.total_memories}")
    print(f"Final average importance: {final_stats.average_importance:.3f}")


async def test_memory_stats():
    """Test memory statistics functionality."""
    print("\n=== Testing Memory Statistics ===")
    
    memory_manager = MemoryManager()
    
    try:
        stats = await memory_manager.get_memory_stats()
        
        print(f"Total memories: {stats.total_memories}")
        print(f"Average importance: {stats.average_importance:.3f}")
        print(f"Storage size: {stats.storage_size_mb:.2f} MB")
        print(f"Embedding dimension: {stats.embedding_dimension}")
        
        print("\nMemories by type:")
        for memory_type, count in stats.memories_by_type.items():
            print(f"  {memory_type.value}: {count}")
        
        if stats.most_accessed_memory:
            print(f"\nMost accessed memory: {stats.most_accessed_memory.content[:50]}...")
            print(f"Access count: {stats.most_accessed_memory.access_count}")
        
        if stats.oldest_memory:
            print(f"\nOldest memory: {stats.oldest_memory.created_at}")
        
        if stats.newest_memory:
            print(f"Newest memory: {stats.newest_memory.created_at}")
            
    except Exception as e:
        print(f"✗ Failed to get memory stats: {e}")


async def test_memory_deletion():
    """Test memory deletion functionality."""
    print("\n=== Testing Memory Deletion ===")
    
    memory_manager = MemoryManager()
    
    # Store a memory to delete
    memory = await memory_manager.store_memory(
        content="Temporary memory for deletion test",
        memory_type=MemoryType.CONTEXT,
        importance_score=0.1
    )
    
    print(f"Created memory for deletion: {memory.id}")
    
    # Verify it exists
    retrieved = await memory_manager.get_memory(memory.id)
    if retrieved:
        print("✓ Memory exists before deletion")
    else:
        print("✗ Memory not found before deletion")
        return
    
    # Delete the memory
    deleted = await memory_manager.delete_memory(memory.id)
    if deleted:
        print("✓ Memory deleted successfully")
    else:
        print("✗ Failed to delete memory")
        return
    
    # Verify it's gone
    retrieved_after = await memory_manager.get_memory(memory.id)
    if retrieved_after is None:
        print("✓ Memory confirmed deleted")
    else:
        print("✗ Memory still exists after deletion")


async def test_complex_search_scenarios():
    """Test complex search scenarios with filters."""
    print("\n=== Testing Complex Search Scenarios ===")
    
    memory_manager = MemoryManager()
    
    # Test search with type filter
    print("\n1. Search for only TASK memories:")
    task_query = MemoryQuery(
        query_text="development setup authentication",
        memory_types=[MemoryType.TASK],
        max_results=3
    )
    
    task_results = await memory_manager.search_memories(task_query)
    print(f"Found {len(task_results)} task memories")
    for result in task_results:
        print(f"  - {result.memory.content[:50]}... (score: {result.relevance_score:.3f})")
    
    # Test search with tag filter
    print("\n2. Search with tag filter:")
    tag_query = MemoryQuery(
        query_text="business",
        tags=["dashboard", "business"],
        max_results=3
    )
    
    tag_results = await memory_manager.search_memories(tag_query)
    print(f"Found {len(tag_results)} memories with business/dashboard tags")
    for result in tag_results:
        print(f"  - {result.memory.content[:50]}... (tags: {result.memory.tags})")
    
    # Test search with importance filter
    print("\n3. Search for high-importance memories:")
    importance_query = MemoryQuery(
        query_text="important information",
        min_importance=0.8,
        max_results=5
    )
    
    importance_results = await memory_manager.search_memories(importance_query)
    print(f"Found {len(importance_results)} high-importance memories")
    for result in importance_results:
        print(f"  - {result.memory.content[:50]}... (importance: {result.memory.importance_score:.2f})")


async def main():
    """Run all memory system tests."""
    print("Starting Memory Management System Tests")
    print("=" * 50)
    
    try:
        # Initialize systems
        print("Initializing systems...")
        initialize_ai_provider("simple")  # Use simple provider for testing
        db_manager = initialize_database("sqlite:///test_memory.db")
        await db_manager.create_tables_async()
        initialize_vector_store("simple")
        print("✓ Systems initialized")
        
        # Run tests
        stored_memories = await test_memory_storage()
        await test_memory_search()
        await test_memory_updates()
        await test_memory_stats()
        await test_complex_search_scenarios()
        await test_memory_deletion()
        await test_memory_consolidation()
        
        print("\n" + "=" * 50)
        print("Memory Management System Tests Completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n✗ Tests failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())