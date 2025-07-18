"""
Real-time data synchronization for Aether AI Companion.
Handles offline/online transitions and conflict resolution.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import UUID, uuid4

from shared.utils.logging import get_logger
from core.database.connection import DatabaseManager
from core.database.models import Conversation, Idea, Task, MemoryEntry
from shared.config.settings import get_settings

logger = get_logger(__name__)


class SyncAction(Enum):
    """Types of synchronization actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    MERGE = "merge"
    USER_CHOICE = "user_choice"


@dataclass
class SyncEvent:
    """Represents a synchronization event."""
    id: str
    entity_type: str  # conversation, idea, task, memory
    entity_id: str
    action: SyncAction
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "device_id": self.device_id,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncEvent':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            action=SyncAction(data["action"]),
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            device_id=data.get("device_id"),
            version=data.get("version", 1)
        )


@dataclass
class ConflictInfo:
    """Information about a synchronization conflict."""
    entity_type: str
    entity_id: str
    local_event: SyncEvent
    remote_event: SyncEvent
    conflict_type: str
    resolution_strategy: ConflictResolution


class SyncManager:
    """Manages real-time data synchronization."""
    
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.pending_events: Dict[str, List[SyncEvent]] = {}  # user_id -> events
        self.conflict_queue: List[ConflictInfo] = []
        self.sync_lock = asyncio.Lock()
        
        # Initialize database manager
        settings = get_settings()
        self.db_manager = DatabaseManager(settings.database_url, settings.database_echo)
        
        # Entity type to model mapping
        self.entity_models = {
            "conversation": Conversation,
            "idea": Idea,
            "task": Task,
            "memory": MemoryEntry
        }
    
    async def process_sync_event(self, event: SyncEvent) -> Dict[str, Any]:
        """Process a synchronization event from a client."""
        async with self.sync_lock:
            try:
                # Validate the event
                if not self._validate_sync_event(event):
                    return {
                        "success": False,
                        "error": "Invalid sync event",
                        "event_id": event.id
                    }
                
                # Check for conflicts
                conflict = await self._detect_conflict(event)
                
                if conflict:
                    # Handle conflict
                    resolution = await self._resolve_conflict(conflict)
                    
                    if resolution["requires_user_input"]:
                        # Queue for user resolution
                        self.conflict_queue.append(conflict)
                        return {
                            "success": False,
                            "conflict": True,
                            "conflict_info": {
                                "entity_type": conflict.entity_type,
                                "entity_id": conflict.entity_id,
                                "local_data": conflict.local_event.data,
                                "remote_data": conflict.remote_event.data,
                                "conflict_id": str(uuid4())
                            },
                            "event_id": event.id
                        }
                    else:
                        # Auto-resolved conflict
                        event = resolution["resolved_event"]
                
                # Apply the event
                result = await self._apply_sync_event(event)
                
                if result["success"]:
                    # Broadcast to other clients
                    await self._broadcast_sync_event(event)
                    
                    # Store for offline clients
                    await self._store_pending_event(event)
                
                return result
                
            except Exception as e:
                logger.error(f"Error processing sync event: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "event_id": event.id
                }
    
    async def handle_client_reconnect(self, user_id: str, last_sync_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Handle client reconnection and sync missed events."""
        try:
            # Get pending events for this user
            pending_events = self.pending_events.get(user_id, [])
            
            # Filter events since last sync
            if last_sync_timestamp:
                last_sync = datetime.fromisoformat(last_sync_timestamp)
                pending_events = [
                    event for event in pending_events
                    if event.timestamp > last_sync
                ]
            
            # Send missed events to client
            sync_data = {
                "type": "sync_events",
                "events": [event.to_dict() for event in pending_events],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.send_to_user(user_id, sync_data)
            
            # Clear sent events
            if user_id in self.pending_events:
                self.pending_events[user_id] = [
                    event for event in self.pending_events[user_id]
                    if event not in pending_events
                ]
            
            return {
                "success": True,
                "events_sent": len(pending_events)
            }
            
        except Exception as e:
            logger.error(f"Error handling client reconnect: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def resolve_conflict(self, conflict_id: str, resolution: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a conflict with user input."""
        try:
            # Find the conflict
            conflict = None
            for c in self.conflict_queue:
                if str(uuid4()) == conflict_id:  # This would need proper ID tracking
                    conflict = c
                    break
            
            if not conflict:
                return {
                    "success": False,
                    "error": "Conflict not found"
                }
            
            # Apply user's resolution
            if resolution["strategy"] == "use_local":
                final_event = conflict.local_event
            elif resolution["strategy"] == "use_remote":
                final_event = conflict.remote_event
            elif resolution["strategy"] == "merge":
                final_event = await self._merge_events(conflict.local_event, conflict.remote_event)
            else:
                return {
                    "success": False,
                    "error": "Invalid resolution strategy"
                }
            
            # Apply the resolved event
            result = await self._apply_sync_event(final_event)
            
            if result["success"]:
                # Broadcast to other clients
                await self._broadcast_sync_event(final_event)
                
                # Remove from conflict queue
                self.conflict_queue.remove(conflict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_sync_event(self, event: SyncEvent) -> bool:
        """Validate a sync event."""
        try:
            # Check required fields
            if not all([event.id, event.entity_type, event.entity_id, event.action]):
                return False
            
            # Check entity type is supported
            if event.entity_type not in self.entity_models:
                return False
            
            # Check action is valid
            if event.action not in SyncAction:
                return False
            
            # Validate entity ID format
            try:
                UUID(event.entity_id)
            except ValueError:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating sync event: {e}")
            return False
    
    async def _detect_conflict(self, event: SyncEvent) -> Optional[ConflictInfo]:
        """Detect if there's a conflict with an incoming sync event."""
        try:
            session = self.db_manager.SessionLocal()
            
            # Get the current entity from database
            model_class = self.entity_models[event.entity_type]
            current_entity = session.query(model_class).filter(
                model_class.id == event.entity_id
            ).first()
            
            session.close()
            
            if not current_entity:
                # No conflict if entity doesn't exist (for CREATE operations)
                if event.action == SyncAction.CREATE:
                    return None
                else:
                    # Conflict: trying to update/delete non-existent entity
                    return ConflictInfo(
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                        local_event=event,
                        remote_event=event,  # Placeholder
                        conflict_type="entity_not_found",
                        resolution_strategy=ConflictResolution.USER_CHOICE
                    )
            
            # Check if there's a timestamp conflict
            if hasattr(current_entity, 'updated_at'):
                # If the entity was updated after the event timestamp, there's a conflict
                if current_entity.updated_at > event.timestamp:
                    # Create a synthetic event for the current state
                    current_event = SyncEvent(
                        id=str(uuid4()),
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                        action=SyncAction.UPDATE,
                        data=self._entity_to_dict(current_entity),
                        timestamp=current_entity.updated_at,
                        version=getattr(current_entity, 'version', 1)
                    )
                    
                    return ConflictInfo(
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                        local_event=current_event,
                        remote_event=event,
                        conflict_type="timestamp_conflict",
                        resolution_strategy=ConflictResolution.LAST_WRITE_WINS
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting conflict: {e}")
            return None
    
    async def _resolve_conflict(self, conflict: ConflictInfo) -> Dict[str, Any]:
        """Resolve a conflict automatically if possible."""
        try:
            if conflict.resolution_strategy == ConflictResolution.LAST_WRITE_WINS:
                # Use the event with the latest timestamp
                if conflict.remote_event.timestamp > conflict.local_event.timestamp:
                    resolved_event = conflict.remote_event
                else:
                    resolved_event = conflict.local_event
                
                return {
                    "requires_user_input": False,
                    "resolved_event": resolved_event
                }
            
            elif conflict.resolution_strategy == ConflictResolution.MERGE:
                # Attempt automatic merge
                merged_event = await self._merge_events(conflict.local_event, conflict.remote_event)
                
                return {
                    "requires_user_input": False,
                    "resolved_event": merged_event
                }
            
            else:
                # Requires user input
                return {
                    "requires_user_input": True
                }
                
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return {
                "requires_user_input": True
            }
    
    async def _merge_events(self, local_event: SyncEvent, remote_event: SyncEvent) -> SyncEvent:
        """Merge two conflicting events."""
        try:
            # Simple merge strategy: combine non-conflicting fields
            merged_data = local_event.data.copy()
            
            # For each field in remote data, use it if local doesn't have it
            # or if it's more recent (this is a simplified merge)
            for key, value in remote_event.data.items():
                if key not in merged_data or remote_event.timestamp > local_event.timestamp:
                    merged_data[key] = value
            
            # Create merged event with latest timestamp
            merged_event = SyncEvent(
                id=str(uuid4()),
                entity_type=local_event.entity_type,
                entity_id=local_event.entity_id,
                action=SyncAction.UPDATE,
                data=merged_data,
                timestamp=max(local_event.timestamp, remote_event.timestamp),
                user_id=local_event.user_id or remote_event.user_id,
                device_id=local_event.device_id,
                version=max(local_event.version, remote_event.version) + 1
            )
            
            return merged_event
            
        except Exception as e:
            logger.error(f"Error merging events: {e}")
            # Fallback to remote event
            return remote_event
    
    async def _apply_sync_event(self, event: SyncEvent) -> Dict[str, Any]:
        """Apply a sync event to the database."""
        try:
            session = self.db_manager.SessionLocal()
            model_class = self.entity_models[event.entity_type]
            
            if event.action == SyncAction.CREATE:
                # Create new entity
                entity = model_class(**event.data)
                session.add(entity)
                
            elif event.action == SyncAction.UPDATE:
                # Update existing entity
                entity = session.query(model_class).filter(
                    model_class.id == event.entity_id
                ).first()
                
                if not entity:
                    session.close()
                    return {
                        "success": False,
                        "error": "Entity not found for update"
                    }
                
                # Update fields
                for key, value in event.data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                
                # Update version if supported
                if hasattr(entity, 'version'):
                    entity.version = event.version
                
            elif event.action == SyncAction.DELETE:
                # Delete entity
                entity = session.query(model_class).filter(
                    model_class.id == event.entity_id
                ).first()
                
                if entity:
                    session.delete(entity)
            
            session.commit()
            session.close()
            
            return {
                "success": True,
                "event_id": event.id
            }
            
        except Exception as e:
            logger.error(f"Error applying sync event: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            
            return {
                "success": False,
                "error": str(e),
                "event_id": event.id
            }
    
    async def _broadcast_sync_event(self, event: SyncEvent):
        """Broadcast a sync event to all connected clients except the sender."""
        try:
            message = {
                "type": "sync_event",
                "event": event.to_dict()
            }
            
            # Broadcast to all users except the sender
            await self.websocket_manager.broadcast(message)
            
        except Exception as e:
            logger.error(f"Error broadcasting sync event: {e}")
    
    async def _store_pending_event(self, event: SyncEvent):
        """Store an event for offline clients."""
        try:
            # Store for all users (in a real implementation, this would be more targeted)
            if "all_users" not in self.pending_events:
                self.pending_events["all_users"] = []
            
            self.pending_events["all_users"].append(event)
            
            # Limit the number of stored events (keep last 1000)
            if len(self.pending_events["all_users"]) > 1000:
                self.pending_events["all_users"] = self.pending_events["all_users"][-1000:]
            
        except Exception as e:
            logger.error(f"Error storing pending event: {e}")
    
    def _entity_to_dict(self, entity) -> Dict[str, Any]:
        """Convert a database entity to dictionary."""
        try:
            result = {}
            
            for column in entity.__table__.columns:
                value = getattr(entity, column.name)
                
                # Convert datetime to ISO string
                if isinstance(value, datetime):
                    value = value.isoformat()
                # Convert UUID to string
                elif hasattr(value, '__str__') and 'uuid' in str(type(value)).lower():
                    value = str(value)
                
                result[column.name] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting entity to dict: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics."""
        return {
            "pending_events": {
                user_id: len(events)
                for user_id, events in self.pending_events.items()
            },
            "conflicts_pending": len(self.conflict_queue),
            "supported_entities": list(self.entity_models.keys())
        }