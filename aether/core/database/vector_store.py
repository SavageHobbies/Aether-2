"""
Vector store implementation for semantic memory search in Aether AI Companion.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text using various methods."""
    
    def __init__(self, method: str = "simple"):
        """
        Initialize embedding generator.
        
        Args:
            method: Embedding method ('simple', 'sentence-transformers', 'openai')
        """
        self.method = method
        self._model = None
        
        if method == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence-transformers model")
            except ImportError:
                logger.warning("sentence-transformers not available, falling back to simple method")
                self.method = "simple"
        
        elif method == "openai":
            try:
                import openai
                self._openai_client = openai.OpenAI()
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI not available, falling back to simple method")
                self.method = "simple"
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding
        """
        if self.method == "sentence-transformers" and self._model:
            embedding = self._model.encode(text)
            return embedding.tolist()
        
        elif self.method == "openai" and hasattr(self, '_openai_client'):
            try:
                response = self._openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                return self._simple_embedding(text)
        
        else:
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str, dimension: int = 384) -> List[float]:
        """
        Generate a simple hash-based embedding for testing.
        
        Args:
            text: Text to embed
            dimension: Embedding dimension
        
        Returns:
            Simple embedding vector
        """
        # Simple hash-based embedding for testing
        # In production, this should be replaced with a proper embedding model
        words = text.lower().split()
        
        # Create a simple vector based on word hashes
        vector = np.zeros(dimension)
        
        for i, word in enumerate(words[:50]):  # Limit to first 50 words
            # Use hash to create pseudo-random but deterministic values
            word_hash = hash(word) % (2**31)
            
            # Distribute hash across vector dimensions
            for j in range(min(8, dimension)):  # Use up to 8 dimensions per word
                idx = (word_hash + j * i) % dimension
                vector[idx] += np.sin(word_hash + j) * 0.1
        
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()


class SimpleVectorStore:
    """Simple in-memory vector store for development and testing."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize simple vector store.
        
        Args:
            data_dir: Directory to store vector data
        """
        self.data_dir = data_dir or Path.home() / ".aether" / "vectors"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.embedding_generator = EmbeddingGenerator("simple")
        
        # Load existing data
        self._load_data()
    
    def add_document(
        self, 
        doc_id: str, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a document to the vector store.
        
        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Optional metadata
        
        Returns:
            True if successful
        """
        try:
            embedding = self.embedding_generator.generate_embedding(text)
            
            self.vectors[doc_id] = embedding
            self.metadata[doc_id] = {
                "text": text,
                "metadata": metadata or {},
                "created_at": str(uuid.uuid4())  # Simple timestamp placeholder
            }
            
            self._save_data()
            logger.debug(f"Added document {doc_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            return False
    
    def search(
        self, 
        query: str, 
        limit: int = 10, 
        threshold: float = 0.0
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            threshold: Minimum similarity threshold
        
        Returns:
            List of (doc_id, similarity_score, metadata) tuples
        """
        try:
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            results = []
            
            for doc_id, doc_embedding in self.vectors.items():
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                
                if similarity >= threshold:
                    results.append((doc_id, similarity, self.metadata[doc_id]))
            
            # Sort by similarity (descending) and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        
        Args:
            doc_id: Document identifier
        
        Returns:
            Document metadata or None
        """
        return self.metadata.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from vector store.
        
        Args:
            doc_id: Document identifier
        
        Returns:
            True if successful
        """
        try:
            if doc_id in self.vectors:
                del self.vectors[doc_id]
                del self.metadata[doc_id]
                self._save_data()
                logger.debug(f"Deleted document {doc_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def list_documents(self) -> List[str]:
        """
        List all document IDs.
        
        Returns:
            List of document IDs
        """
        return list(self.vectors.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_documents": len(self.vectors),
            "embedding_dimension": len(next(iter(self.vectors.values()))) if self.vectors else 0,
            "data_directory": str(self.data_dir)
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity score
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _save_data(self):
        """Save vector data to disk."""
        try:
            import json
            
            data = {
                "vectors": self.vectors,
                "metadata": self.metadata
            }
            
            data_file = self.data_dir / "vectors.json"
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save vector data: {e}")
    
    def _load_data(self):
        """Load vector data from disk."""
        try:
            import json
            
            data_file = self.data_dir / "vectors.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                self.vectors = data.get("vectors", {})
                self.metadata = data.get("metadata", {})
                
                logger.info(f"Loaded {len(self.vectors)} documents from vector store")
                
        except Exception as e:
            logger.error(f"Failed to load vector data: {e}")


class VectorStoreManager:
    """Manages vector store operations for Aether."""
    
    def __init__(self, store_type: str = "simple", data_dir: Optional[Path] = None):
        """
        Initialize vector store manager.
        
        Args:
            store_type: Type of vector store ('simple', 'chromadb', 'qdrant')
            data_dir: Data directory for vector storage
        """
        self.store_type = store_type
        self.data_dir = data_dir or Path.home() / ".aether"
        
        if store_type == "simple":
            self.store = SimpleVectorStore(self.data_dir)
        elif store_type == "chromadb":
            self.store = self._init_chromadb()
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")
        
        logger.info(f"Initialized {store_type} vector store")
    
    def _init_chromadb(self):
        """Initialize ChromaDB vector store."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create ChromaDB client
            client = chromadb.PersistentClient(
                path=str(self.data_dir / "chromadb"),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            collection = client.get_or_create_collection(
                name="aether_memories",
                metadata={"description": "Aether AI Companion memory storage"}
            )
            
            return ChromaDBWrapper(collection)
            
        except ImportError:
            logger.warning("ChromaDB not available, falling back to simple store")
            return SimpleVectorStore(self.data_dir)
    
    def add_memory(self, memory_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add memory to vector store.
        
        Args:
            memory_id: Memory identifier
            content: Memory content
            metadata: Optional metadata
        
        Returns:
            True if successful
        """
        return self.store.add_document(memory_id, content, metadata)
    
    def search_memories(
        self, 
        query: str, 
        limit: int = 10, 
        threshold: float = 0.7
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for relevant memories.
        
        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity threshold
        
        Returns:
            List of (memory_id, similarity, metadata) tuples
        """
        return self.store.search(query, limit, threshold)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete memory from vector store.
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            True if successful
        """
        return self.store.delete_document(memory_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return self.store.get_stats()


class ChromaDBWrapper:
    """Wrapper for ChromaDB to match SimpleVectorStore interface."""
    
    def __init__(self, collection):
        """Initialize ChromaDB wrapper."""
        self.collection = collection
        self.embedding_generator = EmbeddingGenerator("simple")
    
    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None) -> bool:
        """Add document to ChromaDB."""
        try:
            embedding = self.embedding_generator.generate_embedding(text)
            
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id]
            )
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB add failed: {e}")
            return False
    
    def search(self, query: str, limit: int = 10, threshold: float = 0.0) -> List[Tuple[str, float, Dict]]:
        """Search ChromaDB."""
        try:
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            # Convert ChromaDB results to our format
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    if similarity >= threshold:
                        metadata = {
                            "text": results['documents'][0][i] if results['documents'] else "",
                            "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                        }
                        formatted_results.append((doc_id, similarity, metadata))
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document from ChromaDB."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"ChromaDB delete failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "store_type": "chromadb"
            }
        except Exception:
            return {"total_documents": 0, "store_type": "chromadb"}


# Global vector store manager
_vector_store_manager: Optional[VectorStoreManager] = None


def initialize_vector_store(
    store_type: str = "simple", 
    data_dir: Optional[Path] = None
) -> VectorStoreManager:
    """
    Initialize global vector store manager.
    
    Args:
        store_type: Vector store type
        data_dir: Data directory
    
    Returns:
        VectorStoreManager instance
    """
    global _vector_store_manager
    _vector_store_manager = VectorStoreManager(store_type, data_dir)
    return _vector_store_manager


def get_vector_store() -> VectorStoreManager:
    """
    Get global vector store manager.
    
    Returns:
        VectorStoreManager instance
    
    Raises:
        RuntimeError: If not initialized
    """
    if _vector_store_manager is None:
        raise RuntimeError("Vector store not initialized. Call initialize_vector_store() first.")
    return _vector_store_manager