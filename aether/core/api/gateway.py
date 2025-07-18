"""
API Gateway for Aether AI Companion.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from shared.config.settings import get_settings
from shared.utils.logging import get_logger, setup_logging
from core.database.connection import init_database
from core.database.migrations import init_database_schema
from .middleware import setup_middleware
from .routes import setup_routes
from .websocket import WebSocketManager
from .sync import SyncManager, SyncEvent

logger = get_logger(__name__)


class APIGateway:
    """Main API Gateway class for Aether AI Companion."""
    
    def __init__(self):
        self.settings = get_settings()
        self.app: FastAPI = None
        self.websocket_manager = WebSocketManager()
        self.sync_manager = SyncManager(self.websocket_manager)
        
    def create_app(self) -> FastAPI:
        """
        Create and configure the FastAPI application.
        
        Returns:
            Configured FastAPI application
        """
        # Lifespan context manager for startup/shutdown
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("Starting Aether AI Companion API Gateway")
            
            # Initialize database
            try:
                init_database(self.settings)
                init_database_schema()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
            
            # Additional startup tasks
            await self._startup_tasks()
            
            yield
            
            # Shutdown
            logger.info("Shutting down Aether AI Companion API Gateway")
            await self._shutdown_tasks()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Aether AI Companion API",
            description="Intelligent AI companion for conversations, ideas, tasks, and memory management",
            version="0.1.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            lifespan=lifespan
        )
        
        # Set up middleware
        setup_middleware(self.app)
        
        # Set up routes
        api_router = setup_routes()
        self.app.include_router(api_router)
        
        # Add root endpoint
        @self.app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "name": "Aether AI Companion API",
                "version": "0.1.0",
                "status": "running",
                "docs": "/docs",
                "health": "/api/v1/health",
                "websocket": "/ws",
                "features": [
                    "JWT Authentication",
                    "Rate Limiting",
                    "Real-time WebSocket",
                    "Conversation Management",
                    "Idea Processing",
                    "Task Management",
                    "Memory System"
                ]
            }
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_json()
                    
                    # Process message
                    response = await self._process_websocket_message(data)
                    
                    # Send response back to client
                    await websocket.send_json(response)
                    
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close(code=1011, reason="Internal server error")
                self.websocket_manager.disconnect(websocket)
        
        # Global exception handler
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request, exc):
            """Global exception handler for unhandled errors."""
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred"
                }
            )
        
        return self.app
    
    async def _startup_tasks(self):
        """Perform startup tasks."""
        logger.info("Performing startup tasks...")
        
        # Initialize WebSocket manager
        await self.websocket_manager.initialize()
        
        # Additional startup tasks can be added here
        logger.info("Startup tasks completed")
    
    async def _shutdown_tasks(self):
        """Perform shutdown tasks."""
        logger.info("Performing shutdown tasks...")
        
        # Close WebSocket connections
        await self.websocket_manager.shutdown()
        
        # Additional cleanup tasks can be added here
        logger.info("Shutdown tasks completed")
    
    async def _process_websocket_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming WebSocket message.
        
        Args:
            data: Message data from client
        
        Returns:
            Response data to send back to client
        """
        try:
            message_type = data.get("type")
            
            if message_type == "ping":
                return {"type": "pong", "timestamp": data.get("timestamp")}
            
            elif message_type == "sync_event":
                # Handle real-time synchronization events
                return await self._handle_sync_event(data)
            
            elif message_type == "sync_reconnect":
                # Handle client reconnection and sync
                return await self._handle_sync_reconnect(data)
            
            elif message_type == "resolve_conflict":
                # Handle conflict resolution
                return await self._handle_conflict_resolution(data)
            
            elif message_type == "conversation":
                # Handle real-time conversation updates
                return await self._handle_conversation_message(data)
            
            elif message_type == "idea":
                # Handle real-time idea updates
                return await self._handle_idea_message(data)
            
            elif message_type == "task":
                # Handle real-time task updates
                return await self._handle_task_message(data)
            
            else:
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            return {
                "type": "error",
                "message": "Failed to process message"
            }
    
    async def _handle_conversation_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation-related WebSocket messages."""
        # Placeholder for real-time conversation handling
        return {
            "type": "conversation_response",
            "message": "Conversation message received",
            "data": data
        }
    
    async def _handle_idea_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle idea-related WebSocket messages."""
        # Placeholder for real-time idea handling
        return {
            "type": "idea_response",
            "message": "Idea message received",
            "data": data
        }
    
    async def _handle_task_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task-related WebSocket messages."""
        # Placeholder for real-time task handling
        return {
            "type": "task_response",
            "message": "Task message received",
            "data": data
        }
    
    async def _handle_sync_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle real-time synchronization events."""
        try:
            # Parse sync event from message data
            event_data = data.get("event", {})
            sync_event = SyncEvent.from_dict(event_data)
            
            # Process the sync event
            result = await self.sync_manager.process_sync_event(sync_event)
            
            return {
                "type": "sync_response",
                "success": result["success"],
                "event_id": sync_event.id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling sync event: {e}")
            return {
                "type": "sync_response",
                "success": False,
                "error": str(e)
            }
    
    async def _handle_sync_reconnect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle client reconnection and synchronization."""
        try:
            user_id = data.get("user_id")
            last_sync_timestamp = data.get("last_sync_timestamp")
            
            if not user_id:
                return {
                    "type": "sync_reconnect_response",
                    "success": False,
                    "error": "User ID required for sync reconnect"
                }
            
            # Handle reconnection
            result = await self.sync_manager.handle_client_reconnect(user_id, last_sync_timestamp)
            
            return {
                "type": "sync_reconnect_response",
                "success": result["success"],
                "events_sent": result.get("events_sent", 0),
                "timestamp": data.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Error handling sync reconnect: {e}")
            return {
                "type": "sync_reconnect_response",
                "success": False,
                "error": str(e)
            }
    
    async def _handle_conflict_resolution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conflict resolution from client."""
        try:
            conflict_id = data.get("conflict_id")
            resolution = data.get("resolution", {})
            
            if not conflict_id:
                return {
                    "type": "conflict_resolution_response",
                    "success": False,
                    "error": "Conflict ID required"
                }
            
            # Resolve the conflict
            result = await self.sync_manager.resolve_conflict(conflict_id, resolution)
            
            return {
                "type": "conflict_resolution_response",
                "success": result["success"],
                "conflict_id": conflict_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling conflict resolution: {e}")
            return {
                "type": "conflict_resolution_response",
                "success": False,
                "error": str(e)
            }
    
    def run(self, host: str = None, port: int = None, **kwargs):
        """
        Run the API gateway server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn arguments
        """
        if not self.app:
            self.create_app()
        
        host = host or self.settings.host
        port = port or self.settings.port
        
        logger.info(f"Starting Aether API Gateway on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            **kwargs
        )


def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    gateway = APIGateway()
    return gateway.create_app()


def main():
    """Main entry point for the API gateway."""
    # Set up logging
    settings = get_settings()
    setup_logging(
        level="DEBUG" if settings.debug else "INFO",
        log_file=settings.data_dir / "logs" / "api.log"
    )
    
    # Create and run gateway
    gateway = APIGateway()
    gateway.create_app()
    gateway.run()


if __name__ == "__main__":
    main()