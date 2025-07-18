"""
WebSocket manager for real-time communication in Aether AI Companion.
"""

import json
import asyncio
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket
from datetime import datetime
import logging

from shared.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages individual WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected: {len(self.active_connections)} active connections")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_info:
            del self.connection_info[websocket]
            
        logger.info(f"WebSocket disconnected: {len(self.active_connections)} active connections")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
            
            # Update last activity
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_activity"] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                
                # Update last activity
                if connection in self.connection_info:
                    self.connection_info[connection]["last_activity"] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_user(self, message: Dict[str, Any], user_id: str):
        """Broadcast a message to all connections for a specific user."""
        user_connections = [
            ws for ws, info in self.connection_info.items()
            if info.get("user_id") == user_id
        ]
        
        disconnected = []
        
        for connection in user_connections:
            try:
                await connection.send_json(message)
                
                # Update last activity
                self.connection_info[connection]["last_activity"] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_user_connections(self, user_id: str) -> List[WebSocket]:
        """Get all connections for a specific user."""
        return [
            ws for ws, info in self.connection_info.items()
            if info.get("user_id") == user_id
        ]


class WebSocketManager:
    """High-level WebSocket manager with event handling."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.event_handlers: Dict[str, List[callable]] = {}
        self.background_tasks: Set[asyncio.Task] = set()
        self.sync_manager = None  # Will be set by SyncManager
    
    async def initialize(self):
        """Initialize the WebSocket manager."""
        logger.info("Initializing WebSocket manager")
        
        # Start background tasks
        cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("WebSocket manager initialized")
    
    async def shutdown(self):
        """Shutdown the WebSocket manager."""
        logger.info("Shutting down WebSocket manager")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close all connections
        for connection in self.connection_manager.active_connections.copy():
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
        
        logger.info("WebSocket manager shutdown complete")
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Connect a new WebSocket client."""
        await self.connection_manager.connect(websocket, user_id)
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to Aether AI Companion",
            "timestamp": datetime.utcnow().isoformat(),
            "connection_count": self.connection_manager.get_connection_count()
        }
        
        await self.connection_manager.send_personal_message(welcome_message, websocket)
        
        # Trigger connection event
        await self._trigger_event("client_connected", {
            "user_id": user_id,
            "connection_count": self.connection_manager.get_connection_count()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        user_id = self.connection_manager.connection_info.get(websocket, {}).get("user_id")
        self.connection_manager.disconnect(websocket)
        
        # Trigger disconnection event
        asyncio.create_task(self._trigger_event("client_disconnected", {
            "user_id": user_id,
            "connection_count": self.connection_manager.get_connection_count()
        }))
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a specific user."""
        await self.connection_manager.broadcast_to_user(message, user_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        await self.connection_manager.broadcast(message)
    
    async def notify_conversation_update(self, conversation_data: Dict[str, Any], user_id: Optional[str] = None):
        """Notify clients about conversation updates."""
        message = {
            "type": "conversation_update",
            "data": conversation_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_idea_update(self, idea_data: Dict[str, Any], user_id: Optional[str] = None):
        """Notify clients about idea updates."""
        message = {
            "type": "idea_update",
            "data": idea_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_task_update(self, task_data: Dict[str, Any], user_id: Optional[str] = None):
        """Notify clients about task updates."""
        message = {
            "type": "task_update",
            "data": task_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_memory_update(self, memory_data: Dict[str, Any], user_id: Optional[str] = None):
        """Notify clients about memory updates."""
        message = {
            "type": "memory_update",
            "data": memory_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    def add_event_handler(self, event_type: str, handler: callable):
        """Add an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger all handlers for a specific event type."""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def _cleanup_stale_connections(self):
        """Background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                now = datetime.utcnow()
                stale_connections = []
                
                for ws, info in self.connection_manager.connection_info.items():
                    last_activity = info.get("last_activity", info.get("connected_at"))
                    if (now - last_activity).total_seconds() > 1800:  # 30 minutes
                        stale_connections.append(ws)
                
                # Close stale connections
                for ws in stale_connections:
                    try:
                        await ws.close(code=1000, reason="Connection timeout")
                    except Exception as e:
                        logger.error(f"Error closing stale connection: {e}")
                    finally:
                        self.connection_manager.disconnect(ws)
                
                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale connections")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection cleanup task: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "active_connections": self.connection_manager.get_connection_count(),
            "background_tasks": len(self.background_tasks),
            "event_handlers": {
                event_type: len(handlers)
                for event_type, handlers in self.event_handlers.items()
            }
        }