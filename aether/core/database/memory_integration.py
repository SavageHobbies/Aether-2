"""
Integration between database models and vector store for semantic memory.
"""

import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import MemoryEntry
from .vector_store import get_vector_store

logger = logging.getLogger(__name__)


class MemoryVectorIntegration:
    """Integrates database memory entries with vector store for semantic search."""
    
    def __init__(self):
        """Initialize memory vector integration."""
        self.vector_store = None
    
    def _get_vector_store(self):
        """Get vector store instance."""
        if self.vector_store is None:
            try:
                self.vector_store = get_vector_store()
            except RuntimeError:
                logger.error("Vector store not initialized")
                raise
        return self.vector_store
    
    async def add_memory_to_vector_store(
        self, 
        session: AsyncSession, 
        memory_entry: MemoryEntry
    ) -> bool:
        """
        Add memory entry to vector store.
        
        Args:
            session: Database session
            memory_entry: Memory entry to add
        
        Returns:
            True if successful
        """
        try:
            vector_store = self._get_vector_store()
            
            # Prepare metadata
            metadata = {
                "importance_score": memory_entry.importance_score,
                "tags": memory_entry.tags,
                "user_editable": memory_entry.user_editable,
                "created_at": memory_entry.created_at.isoformat(),
                "updated_at": memory_entry.updated_at.isoformat()
            }
            
            # Add to vector store
            success = vector_store.add_memory(
                str(memory_entry.id),
                memory_entry.content,
                metadata
            )
            
            if success:
                logger.debug(f"Added memory {memory_entry.id} to vector store")
            else:
                logger.error(f"Failed to add memory {memory_entry.id} to vector store")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding memory to vector store: {e}")
            return False
    
    async def update_memory_in_vector_store(
        self, 
        session: AsyncSession, 
        memory_entry: MemoryEntry
    ) -> bool:
        """
        Update memory entry in vector store.
        
        Args:
            session: Database session
            memory_entry: Updated memory entry
        
        Returns:
            True if successful
        """
        try:
            vector_store = self._get_vector_store()
            
            # Delete old entry
            vector_store.delete_memory(str(memory_entry.id))
            
            # Add updated entry
            return await self.add_memory_to_vector_store(session, memory_entry)
            
        except Exception as e:
            logger.error(f"Error updating memory in vector store: {e}")
            return False
    
    async def delete_memory_from_vector_store(self, memory_id: str) -> bool:
        """
        Delete memory from vector store.
        
        Args:
            memory_id: Memory ID to delete
        
        Returns:
            True if successful
        """
        try:
            vector_store = self._get_vector_store()
            success = vector_store.delete_memory(memory_id)
            
            if success:
                logger.debug(f"Deleted memory {memory_id} from vector store")
            else:
                logger.warning(f"Memory {memory_id} not found in vector store")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting memory from vector store: {e}")
            return False
    
    async def search_memories_semantic(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        importance_filter: Optional[float] = None
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        Search memories using semantic similarity.
        
        Args:
            session: Database session
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity threshold
            importance_filter: Minimum importance score filter
        
        Returns:
            List of (MemoryEntry, similarity_score) tuples
        """
        try:
            vector_store = self._get_vector_store()
            
            # Search vector store
            vector_results = vector_store.search_memories(query, limit * 2, threshold)
            
            if not vector_results:
                return []
            
            # Get memory IDs from vector results
            memory_ids = [result[0] for result in vector_results]
            
            # Fetch corresponding database entries
            stmt = select(MemoryEntry).where(MemoryEntry.id.in_(memory_ids))
            result = await session.execute(stmt)
            memory_entries = {str(entry.id): entry for entry in result.scalars().all()}
            
            # Combine results with similarity scores
            combined_results = []
            for memory_id, similarity, metadata in vector_results:
                if memory_id in memory_entries:
                    memory_entry = memory_entries[memory_id]
                    
                    # Apply importance filter if specified
                    if importance_filter is None or memory_entry.importance_score >= importance_filter:
                        combined_results.append((memory_entry, similarity))
            
            # Sort by similarity and limit results
            combined_results.sort(key=lambda x: x[1], reverse=True)
            return combined_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in semantic memory search: {e}")
            return []
    
    async def get_related_memories(
        self,
        session: AsyncSession,
        memory_entry: MemoryEntry,
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        Find memories related to a given memory entry.
        
        Args:
            session: Database session
            memory_entry: Reference memory entry
            limit: Maximum results
            threshold: Minimum similarity threshold
        
        Returns:
            List of (MemoryEntry, similarity_score) tuples
        """
        try:
            # Use the memory content as query
            results = await self.search_memories_semantic(
                session, 
                memory_entry.content, 
                limit + 1,  # +1 to account for self-match
                threshold
            )
            
            # Filter out the original memory entry
            filtered_results = [
                (mem, score) for mem, score in results 
                if mem.id != memory_entry.id
            ]
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding related memories: {e}")
            return []
    
    async def sync_all_memories_to_vector_store(self, session: AsyncSession) -> int:
        """
        Sync all database memories to vector store.
        
        Args:
            session: Database session
        
        Returns:
            Number of memories synced
        """
        try:
            # Get all memory entries
            stmt = select(MemoryEntry)
            result = await session.execute(stmt)
            memory_entries = result.scalars().all()
            
            synced_count = 0
            
            for memory_entry in memory_entries:
                success = await self.add_memory_to_vector_store(session, memory_entry)
                if success:
                    synced_count += 1
            
            logger.info(f"Synced {synced_count}/{len(memory_entries)} memories to vector store")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing memories to vector store: {e}")
            return 0
    
    def get_vector_store_stats(self) -> Dict:
        """
        Get vector store statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            vector_store = self._get_vector_store()
            return vector_store.get_stats()
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {}


# Global memory integration instance
_memory_integration: Optional[MemoryVectorIntegration] = None


def get_memory_integration() -> MemoryVectorIntegration:
    """
    Get global memory integration instance.
    
    Returns:
        MemoryVectorIntegration instance
    """
    global _memory_integration
    if _memory_integration is None:
        _memory_integration = MemoryVectorIntegration()
    return _memory_integration


async def add_memory_with_vector_indexing(
    session: AsyncSession,
    content: str,
    importance_score: float = 1.0,
    tags: Optional[List[str]] = None,
    user_editable: bool = True
) -> Optional[MemoryEntry]:
    """
    Create a new memory entry and add it to vector store.
    
    Args:
        session: Database session
        content: Memory content
        importance_score: Importance score (0.0 to 1.0)
        tags: Optional tags
        user_editable: Whether user can edit this memory
    
    Returns:
        Created MemoryEntry or None if failed
    """
    try:
        # Create memory entry
        memory_entry = MemoryEntry(
            content=content,
            importance_score=importance_score,
            tags=tags or [],
            user_editable=user_editable
        )
        
        session.add(memory_entry)
        await session.flush()  # Get the ID
        
        # Add to vector store
        integration = get_memory_integration()
        vector_success = await integration.add_memory_to_vector_store(session, memory_entry)
        
        if not vector_success:
            logger.warning(f"Failed to add memory {memory_entry.id} to vector store")
        
        await session.commit()
        
        logger.info(f"Created memory {memory_entry.id} with vector indexing")
        return memory_entry
        
    except Exception as e:
        logger.error(f"Error creating memory with vector indexing: {e}")
        await session.rollback()
        return None


async def search_memories_by_content(
    session: AsyncSession,
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    importance_filter: Optional[float] = None
) -> List[Tuple[MemoryEntry, float]]:
    """
    Search memories by content using semantic similarity.
    
    Args:
        session: Database session
        query: Search query
        limit: Maximum results
        threshold: Minimum similarity threshold
        importance_filter: Minimum importance score filter
    
    Returns:
        List of (MemoryEntry, similarity_score) tuples
    """
    integration = get_memory_integration()
    return await integration.search_memories_semantic(
        session, query, limit, threshold, importance_filter
    )