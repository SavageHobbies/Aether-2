"""
Memory management system for Aether AI Companion.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from core.ai import get_ai_provider
from core.database import get_database_manager
from core.database.vector_store import get_vector_store
from shared.utils.logging import get_logger

from .types import (
    MemoryType, 
    MemoryEntry, 
    MemoryQuery, 
    MemorySearchResult,
    MemoryConsolidationResult,
    MemoryStats
)

logger = get_logger(__name__)


class MemoryManager:
    """
    Manages semantic memory storage, retrieval, and consolidation.
    
    This system provides:
    - Automatic indexing of memories with embeddings
    - Semantic search with relevance scoring
    - Memory consolidation to prevent storage bloat
    - User-controlled memory editing and deletion
    """
    
    def __init__(self):
        """Initialize memory manager."""
        self.db_manager = get_database_manager()
        self.vector_store = get_vector_store()
        self.ai_provider = get_ai_provider()
        
        # Memory consolidation settings
        self.consolidation_threshold = 1000  # Max memories before consolidation
        self.importance_decay_days = 30  # Days after which importance decays
        self.min_importance_threshold = 0.1  # Below this, memories are candidates for deletion
        
        logger.info("Memory manager initialized")
    
    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> MemoryEntry:
        """
        Store a new memory with automatic indexing.
        
        Args:
            content: The memory content
            memory_type: Type of memory
            metadata: Optional metadata
            importance_score: Importance score (0.0 to 1.0)
            tags: Optional tags
            source: Optional source identifier
        
        Returns:
            MemoryEntry: The stored memory entry
        """
        try:
            # Create memory entry
            memory = MemoryEntry(
                id=str(uuid.uuid4()),
                content=content,
                memory_type=memory_type,
                metadata=metadata or {},
                importance_score=max(0.0, min(1.0, importance_score)),
                tags=tags or [],
                source=source
            )
            
            # Generate embedding
            memory.embedding = await self.ai_provider.get_embedding(content)
            
            # Store in database
            await self._store_memory_in_db(memory)
            
            # Store in vector store
            self.vector_store.add_memory(
                memory_id=memory.id,
                content=content,
                metadata={
                    "memory_type": memory_type.value,
                    "importance_score": importance_score,
                    "created_at": memory.created_at.isoformat(),
                    "tags": tags or [],
                    "source": source
                }
            )
            
            logger.info(f"Stored memory {memory.id} of type {memory_type.value}")
            
            # Check if consolidation is needed
            await self._check_consolidation_needed()
            
            return memory
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    async def search_memories(
        self,
        query: MemoryQuery
    ) -> List[MemorySearchResult]:
        """
        Search memories using semantic similarity and filters.
        
        Args:
            query: Memory query parameters
        
        Returns:
            List of memory search results ordered by relevance
        """
        try:
            # Generate query embedding
            query_embedding = await self.ai_provider.get_embedding(query.query_text)
            
            # Search vector store
            vector_results = self.vector_store.search_memories(
                query=query.query_text,
                limit=query.max_results * 2,  # Get more results for filtering
                threshold=query.similarity_threshold
            )
            
            # Get full memory entries from database
            # vector_results is a list of tuples: (memory_id, similarity, metadata)
            memory_ids = [result[0] for result in vector_results]
            memories = await self._get_memories_by_ids(memory_ids)
            
            # Create search results with relevance scoring
            search_results = []
            for memory_id, similarity_score, metadata in vector_results:
                memory = memories.get(memory_id)
                
                if memory and self._passes_filters(memory, query):
                    relevance_score = self._calculate_relevance_score(
                        memory, similarity_score
                    )
                    
                    search_results.append(MemorySearchResult(
                        memory=memory,
                        similarity_score=similarity_score,
                        relevance_score=relevance_score,
                        explanation=self._generate_retrieval_explanation(
                            memory, similarity_score, query.query_text
                        )
                    ))
            
            # Sort by relevance score and limit results
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            search_results = search_results[:query.max_results]
            
            # Update access statistics
            for result in search_results:
                await self._update_memory_access(result.memory.id)
            
            logger.info(f"Found {len(search_results)} memories for query: {query.query_text[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            MemoryEntry if found, None otherwise
        """
        try:
            memories = await self._get_memories_by_ids([memory_id])
            memory = memories.get(memory_id)
            
            if memory:
                await self._update_memory_access(memory_id)
            
            return memory
            
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[MemoryEntry]:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory identifier
            content: New content (if provided)
            metadata: New metadata (if provided)
            importance_score: New importance score (if provided)
            tags: New tags (if provided)
        
        Returns:
            Updated MemoryEntry if successful, None otherwise
        """
        try:
            # Get existing memory
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory {memory_id} not found for update")
                return None
            
            # Update fields
            updated = False
            if content is not None and content != memory.content:
                memory.content = content
                # Regenerate embedding for new content
                memory.embedding = await self.ai_provider.get_embedding(content)
                updated = True
            
            if metadata is not None:
                memory.metadata.update(metadata)
                updated = True
            
            if importance_score is not None:
                memory.importance_score = max(0.0, min(1.0, importance_score))
                updated = True
            
            if tags is not None:
                memory.tags = tags
                updated = True
            
            if updated:
                memory.updated_at = datetime.utcnow()
                
                # Update in database
                await self._update_memory_in_db(memory)
                
                # Update in vector store (delete and re-add)
                self.vector_store.delete_memory(memory_id)
                self.vector_store.add_memory(
                    memory_id=memory_id,
                    content=memory.content,
                    metadata={
                        "memory_type": memory.memory_type.value,
                        "importance_score": memory.importance_score,
                        "updated_at": memory.updated_at.isoformat(),
                        "tags": memory.tags,
                        "source": memory.source
                    }
                )
                
                logger.info(f"Updated memory {memory_id}")
            
            return memory
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return None
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Delete from database
            deleted_from_db = await self._delete_memory_from_db(memory_id)
            
            # Delete from vector store
            deleted_from_vector = self.vector_store.delete_memory(memory_id)
            
            success = deleted_from_db and deleted_from_vector
            if success:
                logger.info(f"Deleted memory {memory_id}")
            else:
                logger.warning(f"Partial deletion of memory {memory_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    async def consolidate_memories(
        self,
        force: bool = False
    ) -> MemoryConsolidationResult:
        """
        Consolidate memories to prevent storage bloat.
        
        This process:
        1. Identifies low-importance, rarely accessed memories
        2. Merges similar memories
        3. Deletes obsolete memories
        4. Updates importance scores based on access patterns
        
        Args:
            force: Force consolidation even if threshold not reached
        
        Returns:
            MemoryConsolidationResult with consolidation statistics
        """
        try:
            logger.info("Starting memory consolidation")
            
            # Get memory statistics
            stats = await self.get_memory_stats()
            
            if not force and stats.total_memories < self.consolidation_threshold:
                logger.info(f"Consolidation not needed ({stats.total_memories} < {self.consolidation_threshold})")
                return MemoryConsolidationResult(
                    consolidated_count=0,
                    deleted_count=0,
                    updated_count=0,
                    summary="Consolidation not needed"
                )
            
            consolidated_count = 0
            deleted_count = 0
            updated_count = 0
            details = []
            
            # Step 1: Update importance scores based on access patterns
            updated_count += await self._update_importance_scores()
            details.append(f"Updated importance scores for {updated_count} memories")
            
            # Step 2: Delete low-importance memories
            deleted_memories = await self._delete_low_importance_memories()
            deleted_count += len(deleted_memories)
            if deleted_memories:
                details.append(f"Deleted {len(deleted_memories)} low-importance memories")
            
            # Step 3: Merge similar memories
            merged_groups = await self._merge_similar_memories()
            consolidated_count += len(merged_groups)
            if merged_groups:
                details.append(f"Consolidated {len(merged_groups)} groups of similar memories")
            
            # Step 4: Clean up orphaned vector embeddings (placeholder for now)
            # In a real implementation, this would clean up orphaned vectors
            cleaned_vectors = 0
            if cleaned_vectors > 0:
                details.append(f"Cleaned up {cleaned_vectors} orphaned vector embeddings")
            
            summary = f"Consolidated {consolidated_count} memories, deleted {deleted_count}, updated {updated_count}"
            logger.info(f"Memory consolidation completed: {summary}")
            
            return MemoryConsolidationResult(
                consolidated_count=consolidated_count,
                deleted_count=deleted_count,
                updated_count=updated_count,
                summary=summary,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error during memory consolidation: {e}")
            raise
    
    async def get_memory_stats(self) -> MemoryStats:
        """
        Get statistics about the memory system.
        
        Returns:
            MemoryStats with system statistics
        """
        try:
            # Get basic counts from database
            total_memories = await self._count_memories()
            memories_by_type = await self._count_memories_by_type()
            
            # Get memory details for statistics
            all_memories = await self._get_all_memories_summary()
            
            # Calculate statistics
            average_importance = 0.0
            most_accessed_memory = None
            oldest_memory = None
            newest_memory = None
            
            if all_memories:
                average_importance = sum(m.importance_score for m in all_memories) / len(all_memories)
                most_accessed_memory = max(all_memories, key=lambda m: m.access_count)
                oldest_memory = min(all_memories, key=lambda m: m.created_at)
                newest_memory = max(all_memories, key=lambda m: m.created_at)
            
            # Get storage size from vector store
            vector_stats = self.vector_store.get_stats()
            storage_size_mb = vector_stats.get("storage_size_mb", 0.0)
            embedding_dimension = vector_stats.get("embedding_dimension", 384)
            
            return MemoryStats(
                total_memories=total_memories,
                memories_by_type=memories_by_type,
                average_importance=average_importance,
                most_accessed_memory=most_accessed_memory,
                oldest_memory=oldest_memory,
                newest_memory=newest_memory,
                storage_size_mb=storage_size_mb,
                embedding_dimension=embedding_dimension
            )
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            raise
    
    async def _store_memory_in_db(self, memory: MemoryEntry) -> None:
        """Store memory in database."""
        # This would interact with the database models
        # For now, we'll use a placeholder implementation
        pass
    
    async def _get_memories_by_ids(self, memory_ids: List[str]) -> Dict[str, MemoryEntry]:
        """Get memories by IDs from database."""
        # Placeholder implementation
        return {}
    
    async def _update_memory_in_db(self, memory: MemoryEntry) -> None:
        """Update memory in database."""
        # Placeholder implementation
        pass
    
    async def _delete_memory_from_db(self, memory_id: str) -> bool:
        """Delete memory from database."""
        # Placeholder implementation
        return True
    
    async def _update_memory_access(self, memory_id: str) -> None:
        """Update memory access statistics."""
        # Placeholder implementation
        pass
    
    async def _count_memories(self) -> int:
        """Count total memories."""
        # Placeholder implementation
        return 0
    
    async def _count_memories_by_type(self) -> Dict[MemoryType, int]:
        """Count memories by type."""
        # Placeholder implementation
        return {}
    
    async def _get_all_memories_summary(self) -> List[MemoryEntry]:
        """Get summary of all memories."""
        # Placeholder implementation
        return []
    
    def _build_metadata_filter(self, query: MemoryQuery) -> Dict[str, Any]:
        """Build metadata filter for vector search."""
        filter_dict = {}
        
        if query.memory_types:
            filter_dict["memory_type"] = [mt.value for mt in query.memory_types]
        
        if query.tags:
            filter_dict["tags"] = query.tags
        
        if query.min_importance > 0:
            filter_dict["importance_score"] = {"$gte": query.min_importance}
        
        return filter_dict
    
    def _passes_filters(self, memory: MemoryEntry, query: MemoryQuery) -> bool:
        """Check if memory passes additional filters."""
        # Date range filter
        if query.date_range:
            start_date, end_date = query.date_range
            if not (start_date <= memory.created_at <= end_date):
                return False
        
        # Importance filter
        if memory.importance_score < query.min_importance:
            return False
        
        return True
    
    def _calculate_relevance_score(
        self,
        memory: MemoryEntry,
        similarity_score: float
    ) -> float:
        """
        Calculate relevance score combining similarity, importance, and recency.
        
        Args:
            memory: Memory entry
            similarity_score: Semantic similarity score
        
        Returns:
            Combined relevance score
        """
        # Base similarity score (0.0 to 1.0)
        relevance = similarity_score * 0.6
        
        # Add importance score (0.0 to 1.0) * 0.3
        relevance += memory.importance_score * 0.3
        
        # Add recency bonus (0.0 to 0.1)
        days_old = (datetime.utcnow() - memory.created_at).days
        recency_bonus = max(0, 0.1 - (days_old / 365) * 0.1)  # Decay over a year
        relevance += recency_bonus
        
        # Add access frequency bonus (0.0 to 0.1)
        access_bonus = min(0.1, memory.access_count / 100 * 0.1)
        relevance += access_bonus
        
        return min(1.0, relevance)
    
    def _generate_retrieval_explanation(
        self,
        memory: MemoryEntry,
        similarity_score: float,
        query_text: str
    ) -> str:
        """Generate explanation for why this memory was retrieved."""
        explanations = []
        
        if similarity_score > 0.9:
            explanations.append("highly similar content")
        elif similarity_score > 0.8:
            explanations.append("similar content")
        elif similarity_score > 0.7:
            explanations.append("related content")
        
        if memory.importance_score > 0.8:
            explanations.append("high importance")
        
        if memory.access_count > 10:
            explanations.append("frequently accessed")
        
        days_old = (datetime.utcnow() - memory.created_at).days
        if days_old < 7:
            explanations.append("recent")
        
        if not explanations:
            explanations.append("semantic match")
        
        return f"Retrieved due to: {', '.join(explanations)}"
    
    async def _check_consolidation_needed(self) -> None:
        """Check if memory consolidation is needed."""
        stats = await self.get_memory_stats()
        if stats.total_memories >= self.consolidation_threshold:
            logger.info("Memory consolidation threshold reached, scheduling consolidation")
            # In a real implementation, this might schedule a background task
            # For now, we'll just log the need for consolidation
    
    async def _update_importance_scores(self) -> int:
        """Update importance scores based on access patterns and age."""
        # Placeholder implementation
        return 0
    
    async def _delete_low_importance_memories(self) -> List[str]:
        """Delete memories with very low importance scores."""
        # Placeholder implementation
        return []
    
    async def _merge_similar_memories(self) -> List[str]:
        """Merge very similar memories to reduce redundancy."""
        # Placeholder implementation
        return []


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """
    Get global memory manager instance.
    
    Returns:
        MemoryManager instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager