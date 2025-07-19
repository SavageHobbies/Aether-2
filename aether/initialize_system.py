#!/usr/bin/env python3
"""
Initialize the Aether system with proper database setup.
"""

import asyncio
import logging
import os
from pathlib import Path

from core.database.connection import initialize_database
from core.database.vector_store import initialize_vector_store
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def initialize_aether_system(database_url: str = None, echo: bool = False):
    """
    Initialize the Aether system with all required components.
    
    Args:
        database_url: Database connection URL (defaults to SQLite)
        echo: Whether to echo SQL statements
    """
    if database_url is None:
        # Default to SQLite in the aether directory
        db_path = Path(__file__).parent / "aether.db"
        database_url = f"sqlite:///{db_path}"
    
    logger.info(f"Initializing Aether system with database: {database_url}")
    
    # Initialize database
    db_manager = initialize_database(database_url, echo=echo)
    
    # Create tables
    db_manager.create_tables()
    
    # Initialize vector store
    vector_store = initialize_vector_store(store_type="simple")
    
    logger.info("Aether system initialized successfully")
    return db_manager


async def initialize_aether_system_async(database_url: str = None, echo: bool = False):
    """
    Initialize the Aether system asynchronously.
    
    Args:
        database_url: Database connection URL (defaults to SQLite)
        echo: Whether to echo SQL statements
    """
    if database_url is None:
        # Default to SQLite in the aether directory
        db_path = Path(__file__).parent / "aether.db"
        database_url = f"sqlite:///{db_path}"
    
    logger.info(f"Initializing Aether system (async) with database: {database_url}")
    
    # Initialize database
    db_manager = initialize_database(database_url, echo=echo)
    
    # Create tables asynchronously
    await db_manager.create_tables_async()
    
    # Initialize vector store
    vector_store = initialize_vector_store(store_type="simple")
    
    logger.info("Aether system initialized successfully (async)")
    return db_manager


def main():
    """Main initialization function."""
    print("Initializing Aether AI Companion System...")
    
    try:
        # Initialize synchronously
        db_manager = initialize_aether_system(echo=True)
        print("✓ Database initialized successfully")
        
        # Test basic functionality
        with db_manager.get_session() as session:
            print("✓ Database session created successfully")
        
        print("✓ Aether system ready!")
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)