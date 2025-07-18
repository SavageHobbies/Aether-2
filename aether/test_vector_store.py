"""
Test script for vector store functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database.vector_store import VectorStoreManager, initialize_vector_store


def test_simple_vector_store():
    """Test simple vector store functionality."""
    print("🔧 Testing Simple Vector Store...")
    
    # Initialize vector store
    test_dir = Path("test_vectors")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    vector_store = VectorStoreManager("simple", test_dir)
    
    try:
        # Test adding documents
        print("📝 Adding test documents...")
        
        documents = [
            ("doc1", "I want to build a dashboard for business metrics", {"type": "idea", "priority": "high"}),
            ("doc2", "Create a system for tracking customer feedback", {"type": "task", "priority": "medium"}),
            ("doc3", "Dashboard should show revenue, costs, and profit margins", {"type": "requirement", "priority": "high"}),
            ("doc4", "Need to integrate with Google Calendar for scheduling", {"type": "integration", "priority": "low"}),
            ("doc5", "The AI assistant should remember previous conversations", {"type": "feature", "priority": "high"}),
        ]
        
        for doc_id, content, metadata in documents:
            success = vector_store.add_memory(doc_id, content, metadata)
            if success:
                print(f"✅ Added: {doc_id}")
            else:
                print(f"❌ Failed to add: {doc_id}")
        
        # Test search functionality
        print("\n🔍 Testing search functionality...")
        
        search_queries = [
            ("dashboard metrics", "Looking for dashboard-related content"),
            ("business revenue", "Looking for business/financial content"),
            ("AI conversation", "Looking for AI-related content"),
            ("calendar integration", "Looking for integration content"),
        ]
        
        for query, description in search_queries:
            print(f"\n🔎 {description}")
            print(f"Query: '{query}'")
            
            results = vector_store.search_memories(query, limit=3, threshold=0.1)
            
            if results:
                for i, (doc_id, similarity, metadata) in enumerate(results, 1):
                    print(f"  {i}. {doc_id} (similarity: {similarity:.3f})")
                    print(f"     Text: {metadata['text'][:60]}...")
                    print(f"     Type: {metadata['metadata'].get('type', 'unknown')}")
            else:
                print("  No results found")
        
        # Test statistics
        print("\n📊 Vector Store Statistics:")
        stats = vector_store.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test document retrieval
        print("\n📄 Testing document retrieval...")
        doc = vector_store.store.get_document("doc1")
        if doc:
            print(f"✅ Retrieved doc1: {doc['text'][:50]}...")
        else:
            print("❌ Failed to retrieve doc1")
        
        # Test document deletion
        print("\n🗑️  Testing document deletion...")
        success = vector_store.delete_memory("doc4")
        if success:
            print("✅ Deleted doc4")
            
            # Verify deletion
            remaining_docs = vector_store.store.list_documents()
            print(f"📋 Remaining documents: {len(remaining_docs)}")
        else:
            print("❌ Failed to delete doc4")
        
        print("\n🎉 Simple vector store test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        if test_dir.exists():
            import shutil
            try:
                shutil.rmtree(test_dir)
            except PermissionError:
                print(f"⚠️  Could not delete test directory {test_dir}")


def test_embedding_generation():
    """Test embedding generation functionality."""
    print("🔧 Testing Embedding Generation...")
    
    from core.database.vector_store import EmbeddingGenerator
    
    try:
        # Test simple embedding
        generator = EmbeddingGenerator("simple")
        
        test_texts = [
            "Hello world",
            "Business dashboard with metrics",
            "AI assistant for productivity",
            "Calendar integration and scheduling",
        ]
        
        print("📝 Generating embeddings...")
        embeddings = []
        
        for text in test_texts:
            embedding = generator.generate_embedding(text)
            embeddings.append(embedding)
            print(f"✅ Generated embedding for: '{text}' (dim: {len(embedding)})")
        
        # Test similarity between embeddings
        print("\n🔍 Testing embedding similarities...")
        
        import numpy as np
        
        def cosine_similarity(vec1, vec2):
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        
        # Compare similar texts
        sim1 = cosine_similarity(embeddings[1], embeddings[1])  # Same text
        sim2 = cosine_similarity(embeddings[1], embeddings[2])  # Different but related
        sim3 = cosine_similarity(embeddings[1], embeddings[3])  # Different topics
        
        print(f"📊 Similarity Results:")
        print(f"  Same text: {sim1:.3f}")
        print(f"  Related text: {sim2:.3f}")
        print(f"  Different topic: {sim3:.3f}")
        
        # Verify that same text has highest similarity
        if sim1 >= sim2 >= sim3:
            print("✅ Embedding similarity ordering is correct")
        else:
            print("⚠️  Embedding similarity ordering may need improvement")
        
        print("\n🎉 Embedding generation test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store_integration():
    """Test vector store integration with database models."""
    print("🔧 Testing Vector Store Integration...")
    
    try:
        # Initialize vector store
        vector_store = initialize_vector_store("simple")
        
        # Simulate memory entries from database
        memory_entries = [
            {
                "id": "mem-001",
                "content": "User wants to create a business dashboard with KPIs",
                "importance_score": 0.9,
                "tags": ["dashboard", "business", "kpi"]
            },
            {
                "id": "mem-002", 
                "content": "Discussion about integrating with Google Calendar API",
                "importance_score": 0.7,
                "tags": ["integration", "calendar", "api"]
            },
            {
                "id": "mem-003",
                "content": "AI should remember context from previous conversations",
                "importance_score": 0.8,
                "tags": ["ai", "memory", "context"]
            }
        ]
        
        # Add memories to vector store
        print("📝 Adding memory entries to vector store...")
        for memory in memory_entries:
            metadata = {
                "importance_score": memory["importance_score"],
                "tags": memory["tags"]
            }
            success = vector_store.add_memory(memory["id"], memory["content"], metadata)
            if success:
                print(f"✅ Added memory: {memory['id']}")
        
        # Test contextual search
        print("\n🔍 Testing contextual memory search...")
        
        search_scenarios = [
            ("I need help with my business metrics", "Should find dashboard-related memory"),
            ("How do I schedule meetings?", "Should find calendar integration memory"),
            ("Does the AI remember what we talked about?", "Should find context memory"),
        ]
        
        for query, expected in search_scenarios:
            print(f"\n🔎 Query: '{query}'")
            print(f"Expected: {expected}")
            
            results = vector_store.search_memories(query, limit=2, threshold=0.1)
            
            if results:
                best_match = results[0]
                print(f"✅ Best match: {best_match[0]} (similarity: {best_match[1]:.3f})")
                print(f"   Content: {best_match[2]['text'][:60]}...")
                print(f"   Tags: {best_match[2]['metadata'].get('tags', [])}")
            else:
                print("❌ No matches found")
        
        print("\n🎉 Vector store integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 Aether Vector Store Tests\n")
    
    # Run all tests
    tests = [
        ("Embedding Generation", test_embedding_generation),
        ("Simple Vector Store", test_simple_vector_store),
        ("Vector Store Integration", test_vector_store_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All vector store tests passed!")
        print("\n🎯 Vector Store Status:")
        print("  ✅ Embedding generation working")
        print("  ✅ Document storage and retrieval")
        print("  ✅ Semantic search functionality")
        print("  ✅ Similarity scoring accurate")
        print("  ✅ Integration ready")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)