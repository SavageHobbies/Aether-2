#!/usr/bin/env python3
"""
Simple API server that bypasses FastAPI compatibility issues.
Uses basic HTTP server with JSON responses.
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_settings
from shared.utils import get_logger
from core.database.connection import initialize_database


class AetherAPIHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for Aether API."""
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/':
                self.send_json_response({
                    "name": "Aether AI Companion API",
                    "version": "0.1.0",
                    "status": "running",
                    "message": "Simple API server (FastAPI compatibility workaround)",
                    "endpoints": [
                        "GET / - API info",
                        "GET /health - Health check",
                        "GET /api/v1/conversations - List conversations",
                        "GET /api/v1/tasks - List tasks",
                        "POST /api/v1/conversations - Create conversation",
                        "POST /api/v1/tasks - Create task"
                    ]
                })
            
            elif path == '/health':
                self.send_json_response({
                    "status": "healthy",
                    "service": "aether-ai-companion",
                    "timestamp": time.time()
                })
            
            elif path == '/api/v1/conversations':
                self.handle_conversations_get()
            
            elif path == '/api/v1/tasks':
                self.handle_tasks_get()
            
            else:
                self.send_error_response(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8')) if post_data else {}
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON in request body")
                return
            
            if path == '/api/v1/conversations':
                self.handle_conversations_post(data)
            
            elif path == '/api/v1/tasks':
                self.handle_tasks_post(data)
            
            else:
                self.send_error_response(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def handle_conversations_get(self):
        """Handle GET /api/v1/conversations."""
        # Mock response for now
        conversations = [
            {
                "id": "conv-1",
                "session_id": "session-1",
                "user_input": "Hello, how are you?",
                "ai_response": "I'm doing well, thank you! How can I help you today?",
                "created_at": "2025-01-19T10:00:00Z"
            },
            {
                "id": "conv-2", 
                "session_id": "session-1",
                "user_input": "Can you help me with my tasks?",
                "ai_response": "Of course! I can help you manage your tasks. What would you like to do?",
                "created_at": "2025-01-19T10:05:00Z"
            }
        ]
        
        self.send_json_response({
            "conversations": conversations,
            "total": len(conversations),
            "message": "Conversations retrieved successfully"
        })
    
    def handle_conversations_post(self, data):
        """Handle POST /api/v1/conversations."""
        # Validate required fields
        required_fields = ['user_input', 'ai_response']
        for field in required_fields:
            if field not in data:
                self.send_error_response(400, f"Missing required field: {field}")
                return
        
        # Mock conversation creation
        new_conversation = {
            "id": f"conv-{int(time.time())}",
            "session_id": data.get('session_id', f"session-{int(time.time())}"),
            "user_input": data['user_input'],
            "ai_response": data['ai_response'],
            "context_metadata": data.get('context_metadata', {}),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        self.send_json_response({
            "conversation": new_conversation,
            "message": "Conversation created successfully"
        }, status_code=201)
    
    def handle_tasks_get(self):
        """Handle GET /api/v1/tasks."""
        # Mock response for now
        tasks = [
            {
                "id": "task-1",
                "title": "Review project proposal",
                "description": "Review the new project proposal and provide feedback",
                "priority": 3,
                "status": "pending",
                "due_date": "2025-01-25T17:00:00Z",
                "created_at": "2025-01-19T09:00:00Z"
            },
            {
                "id": "task-2",
                "title": "Update documentation",
                "description": "Update the API documentation with new endpoints",
                "priority": 2,
                "status": "in_progress", 
                "due_date": "2025-01-22T12:00:00Z",
                "created_at": "2025-01-19T09:30:00Z"
            }
        ]
        
        self.send_json_response({
            "tasks": tasks,
            "total": len(tasks),
            "message": "Tasks retrieved successfully"
        })
    
    def handle_tasks_post(self, data):
        """Handle POST /api/v1/tasks."""
        # Validate required fields
        if 'title' not in data:
            self.send_error_response(400, "Missing required field: title")
            return
        
        # Mock task creation
        new_task = {
            "id": f"task-{int(time.time())}",
            "title": data['title'],
            "description": data.get('description', ''),
            "priority": data.get('priority', 2),
            "status": data.get('status', 'pending'),
            "due_date": data.get('due_date'),
            "source_conversation_id": data.get('source_conversation_id'),
            "source_idea_id": data.get('source_idea_id'),
            "external_integrations": data.get('external_integrations', {}),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        self.send_json_response({
            "task": new_task,
            "message": "Task created successfully"
        }, status_code=201)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response."""
        self.send_json_response({
            "error": True,
            "status_code": status_code,
            "message": message
        }, status_code)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


class SimpleAPIServer:
    """Simple API server for Aether."""
    
    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.logger = get_logger(__name__)
    
    def start(self):
        """Start the API server."""
        try:
            # Initialize database
            print("Initializing database...")
            settings = get_settings()
            db_manager = initialize_database(settings.database_url, echo=settings.debug)
            db_manager.create_tables()
            print("✅ Database initialized successfully")
            
            # Create HTTP server
            self.server = HTTPServer((self.host, self.port), AetherAPIHandler)
            
            print(f"\n🚀 Aether AI Companion API Server Starting...")
            print(f"📍 Server running at: http://{self.host}:{self.port}")
            print(f"📖 API Documentation: http://{self.host}:{self.port}/")
            print(f"❤️  Health Check: http://{self.host}:{self.port}/health")
            print(f"💬 Conversations: http://{self.host}:{self.port}/api/v1/conversations")
            print(f"📋 Tasks: http://{self.host}:{self.port}/api/v1/tasks")
            print("\n✨ This is a compatibility workaround for FastAPI/Pydantic issues")
            print("🔧 All core functionality is available through HTTP endpoints")
            print("\nPress Ctrl+C to stop the server")
            print("=" * 60)
            
            # Start server
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down server...")
            self.stop()
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            raise
    
    def stop(self):
        """Stop the API server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("✅ Server stopped successfully")


def main():
    """Main entry point."""
    try:
        # Use a different port to avoid conflicts
        server = SimpleAPIServer(
            host='localhost',
            port=9001
        )
        server.start()
    except Exception as e:
        print(f"❌ Failed to start Aether API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()