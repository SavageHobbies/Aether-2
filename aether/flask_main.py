"""
Flask-based main entry point for Aether AI Companion - Windows compatible.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify

# Simple configuration
class SimpleSettings:
    def __init__(self):
        self.name = "Aether AI Companion"
        self.version = "0.1.0"
        self.debug = False
        self.host = "localhost"
        self.port = 5000
        self.data_dir = Path.home() / ".aether"
        self.data_dir.mkdir(parents=True, exist_ok=True)

def create_app():
    """Create Flask application."""
    settings = SimpleSettings()
    
    app = Flask(__name__)
    app.config['DEBUG'] = settings.debug
    
    @app.route('/')
    def root():
        return jsonify({
            "message": "Aether AI Companion is running!",
            "version": settings.version,
            "status": "ready",
            "data_dir": str(settings.data_dir)
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy", 
            "service": "aether-ai-companion",
            "version": settings.version
        })
    
    @app.route('/api/info')
    def info():
        return jsonify({
            "name": settings.name,
            "version": settings.version,
            "endpoints": [
                "/",
                "/health", 
                "/api/info",
                "/api/conversation",
                "/api/ideas",
                "/api/tasks"
            ],
            "message": "Core AI components will be available soon!",
            "features": [
                "Conversation Management (Coming Soon)",
                "Idea Stream Processing (Coming Soon)", 
                "Task Management (Coming Soon)",
                "Memory System (Coming Soon)"
            ]
        })
    
    @app.route('/api/conversation', methods=['GET', 'POST'])
    def conversation():
        return jsonify({
            "message": "Conversation API endpoint",
            "status": "coming_soon",
            "description": "This will handle AI conversations with persistent memory"
        })
    
    @app.route('/api/ideas', methods=['GET', 'POST'])
    def ideas():
        return jsonify({
            "message": "Ideas API endpoint", 
            "status": "coming_soon",
            "description": "This will handle rapid idea capture and processing"
        })
    
    @app.route('/api/tasks', methods=['GET', 'POST'])
    def tasks():
        return jsonify({
            "message": "Tasks API endpoint",
            "status": "coming_soon", 
            "description": "This will handle task management and external integrations"
        })
    
    return app, settings

def main():
    """Main application entry point."""
    app, settings = create_app()
    
    print(f"Starting {settings.name} v{settings.version}")
    print(f"Data directory: {settings.data_dir}")
    print(f"Server starting on http://{settings.host}:{settings.port}")
    print("Press Ctrl+C to stop the server")
    print()
    print("Available endpoints:")
    print(f"  http://localhost:{settings.port}/         - Main status")
    print(f"  http://localhost:{settings.port}/health   - Health check")
    print(f"  http://localhost:{settings.port}/api/info - API information")
    print()
    
    try:
        app.run(
            host=settings.host,
            port=settings.port,
            debug=settings.debug
        )
    except KeyboardInterrupt:
        print("\nShutting down Aether AI Companion")

if __name__ == "__main__":
    main()