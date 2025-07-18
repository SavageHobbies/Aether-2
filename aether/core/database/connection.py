"""
Database connection management for Aether AI Companion.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.echo = echo
        
        # Handle SQLite URLs for async
        if database_url.startswith("sqlite:///"):
            # Convert to async SQLite URL
            self.async_database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            self.async_database_url = database_url
        
        # Create engines
        self.engine = create_engine(database_url, echo=echo)
        self.async_engine = create_async_engine(self.async_database_url, echo=echo)
        
        # Create session factories
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Enable foreign keys for SQLite
        if "sqlite" in database_url.lower():
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    def create_tables(self):
        """Create all database tables."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    async def create_tables_async(self):
        """Create all database tables asynchronously."""
        logger.info("Creating database tables (async)...")
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully (async)")
    
    def drop_tables(self):
        """Drop all database tables."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    async def drop_tables_async(self):
        """Drop all database tables asynchronously."""
        logger.warning("Dropping all database tables (async)...")
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped (async)")
    
    def get_session(self) -> Session:
        """Get a synchronous database session."""
        return self.SessionLocal()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session."""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connections."""
        await self.async_engine.dispose()
        self.engine.dispose()
        logger.info("Database connections closed")


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


def initialize_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize the global database manager.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
    
    Returns:
        DatabaseManager instance
    """
    global _database_manager
    _database_manager = DatabaseManager(database_url, echo)
    return _database_manager


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
    
    Raises:
        RuntimeError: If database manager is not initialized
    """
    if _database_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database() first.")
    return _database_manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session (convenience function).
    
    Yields:
        AsyncSession: Database session
    """
    db_manager = get_database_manager()
    async with db_manager.get_async_session() as session:
        yield session