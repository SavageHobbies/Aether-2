"""
Unit tests for vector store functionality.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.database.vector_store import (
    EmbeddingGenerator,
    SimpleVectorStore,
    VectorStoreManager,
    initialize_vector_store,
    get_vector_store
)


class TestEmbeddingGenerator(unittest.TestCase):
    """Test embedding generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = EmbeddingGenerator("simple")
    
    def test_simple_embedding_generation(self):
        """Test simple embedding generation."""
        text = "Hello world"
        embedding = self.generator.generate_embedding(text)
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)  # Default dimension
        self.assertTrue(all(isinstance(x, float) for x in embedding))
    
    def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        text = "Test consistency"
        embedding1 = self.generator.generate_embedding(text)
        embedding2 = self.generator.generate_embedding(text)
        
        self.assertEqual(embedding1, embedding2)
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        text1 = "First text"
        text2 = "Second text"
        
        embedding1 = self.generator.generate_embedding(text1)
        embedding2 = self.generator.generate_embedding(text2)
        
        self.assertNotEqual(embedding1, embedding2)
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        embedding = self.generator.generate_embedding("")
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)


class TestSimpleVectorStore(unittest.TestCase):
    """Test simple vector store functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.store = SimpleVectorStore(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_document(self):
        """Test adding documents to vector store."""
        success = self.store.add_document("doc1", "Test document", {"type": "test"})
        
        self.assertTrue(success)
        self.assertIn("doc1", self.store.vectors)
        self.assertIn("doc1", self.store.metadata)
    
    def test_get_document(self):
        """Test retrieving documents from vector store."""
        self.store.add_document("doc1", "Test document", {"type": "test"})
        
        doc = self.store.get_document("doc1")
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc["text"], "Test document")
        self.assertEqual(doc["metadata"]["type"], "test")
    
    def test_delete_document(self):
        """Test deleting documents from vector store."""
        self.store.add_document("doc1", "Test document")
        
        success = self.store.delete_document("doc1")
        
        self.assertTrue(success)
        self.assertNotIn("doc1", self.store.vectors)
        self.assertNotIn("doc1", self.store.metadata)
    
    def test_search_documents(self):
        """Test searching documents in vector store."""
        # Add test documents
        self.store.add_document("doc1", "Business dashboard metrics")
        self.store.add_document("doc2", "Calendar integration system")
        self.store.add_document("doc3", "AI conversation memory")
        
        # Search for business-related content
        results = self.store.search("business metrics", limit=2, threshold=0.0)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)
        
        # Check result format
        if results:
            doc_id, similarity, metadata = results[0]
            self.assertIsInstance(doc_id, str)
            self.assertIsInstance(similarity, float)
            self.assertIsInstance(metadata, dict)
    
    def test_list_documents(self):
        """Test listing all documents."""
        self.store.add_document("doc1", "First document")
        self.store.add_document("doc2", "Second document")
        
        doc_ids = self.store.list_documents()
        
        self.assertEqual(len(doc_ids), 2)
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)
    
    def test_get_stats(self):
        """Test getting vector store statistics."""
        self.store.add_document("doc1", "Test document")
        
        stats = self.store.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["total_documents"], 1)
        self.assertEqual(stats["embedding_dimension"], 384)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]
        
        # Same vectors should have similarity 1.0
        sim1 = self.store._cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim1, 1.0, places=5)
        
        # Orthogonal vectors should have similarity 0.0
        sim2 = self.store._cosine_similarity(vec1, vec3)
        self.assertAlmostEqual(sim2, 0.0, places=5)


class TestVectorStoreManager(unittest.TestCase):
    """Test vector store manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = VectorStoreManager("simple", self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_memory(self):
        """Test adding memory to vector store."""
        success = self.manager.add_memory(
            "mem1", 
            "Test memory content", 
            {"importance": 0.8}
        )
        
        self.assertTrue(success)
    
    def test_search_memories(self):
        """Test searching memories."""
        # Add test memories
        self.manager.add_memory("mem1", "Business dashboard project")
        self.manager.add_memory("mem2", "Calendar integration task")
        
        # Search for memories
        results = self.manager.search_memories("business project", limit=1)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 1)
    
    def test_delete_memory(self):
        """Test deleting memory."""
        self.manager.add_memory("mem1", "Test memory")
        
        success = self.manager.delete_memory("mem1")
        
        self.assertTrue(success)
    
    def test_get_stats(self):
        """Test getting statistics."""
        self.manager.add_memory("mem1", "Test memory")
        
        stats = self.manager.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("total_documents", stats)


class TestVectorStoreGlobals(unittest.TestCase):
    """Test global vector store functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Reset global state
        import core.database.vector_store
        core.database.vector_store._vector_store_manager = None
    
    def test_initialize_and_get_vector_store(self):
        """Test initializing and getting global vector store."""
        # Initialize
        manager = initialize_vector_store("simple", self.temp_dir)
        self.assertIsInstance(manager, VectorStoreManager)
        
        # Get initialized store
        retrieved_manager = get_vector_store()
        self.assertIs(manager, retrieved_manager)
    
    def test_get_vector_store_not_initialized(self):
        """Test getting vector store when not initialized."""
        with self.assertRaises(RuntimeError):
            get_vector_store()


if __name__ == "__main__":
    # Create test directory
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)