"""
Main entry point for Aether AI Companion.
"""

import asyncio
import sys
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_settings, load_env_file
from shared.utils import get_logger, setup_logging, setup_privacy_logging


def main():
    """Main application entry point."""
    # Load environment configuration
    load_env_file()
    settings = get_settings()
    
    # Set up logging
    log_file = settings.data_dir / "logs" / "aether.log"
    setup_logging(
        level="DEBUG" if settings.debug else "INFO",
        log_file=log_file
    )
    setup_privacy_logging()
    
    logger = get_logger(__name__)
    logger.info(f"Starting Aether AI Companion v{settings.version}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Debug mode: {settings.debug}")
    
    try:
        # Create a simple FastAPI app for testing
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI(title="Aether AI Companion", version=settings.version)
        
        @app.get("/")
        async def root():
            return {
                "message": "Aether AI Companion is running!",
                "version": settings.version,
                "status": "ready"
            }
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "aether-ai-companion"}
        
        logger.info("Starting Aether AI Companion server...")
        logger.info(f"Server will be available at http://{settings.host}:{settings.port}")
        
        # Run with uvicorn
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down Aether AI Companion")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start Aether AI Companion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()