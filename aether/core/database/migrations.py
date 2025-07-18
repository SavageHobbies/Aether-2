"""
Database migration utilities for Aether AI Companion.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, alembic_ini_path: str = "alembic.ini"):
        """
        Initialize migration manager.
        
        Args:
            alembic_ini_path: Path to alembic.ini file
        """
        self.alembic_ini_path = alembic_ini_path
        self.project_root = Path(__file__).parent.parent.parent
    
    def _run_alembic_command(self, command: list) -> bool:
        """
        Run an Alembic command.
        
        Args:
            command: Alembic command as list of strings
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            # Run the command
            result = subprocess.run(
                ["python", "-m", "alembic"] + command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Alembic command successful: {' '.join(command)}")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Alembic command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error running Alembic: {e}")
            return False
        
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Create a new migration.
        
        Args:
            message: Migration message
            autogenerate: Whether to auto-generate migration from model changes
        
        Returns:
            True if successful, False otherwise
        """
        command = ["revision"]
        if autogenerate:
            command.append("--autogenerate")
        command.extend(["-m", message])
        
        return self._run_alembic_command(command)
    
    def upgrade_database(self, revision: str = "head") -> bool:
        """
        Upgrade database to a specific revision.
        
        Args:
            revision: Target revision (default: "head")
        
        Returns:
            True if successful, False otherwise
        """
        return self._run_alembic_command(["upgrade", revision])
    
    def downgrade_database(self, revision: str = "-1") -> bool:
        """
        Downgrade database to a specific revision.
        
        Args:
            revision: Target revision (default: "-1" for one step back)
        
        Returns:
            True if successful, False otherwise
        """
        return self._run_alembic_command(["downgrade", revision])
    
    def get_current_revision(self) -> str:
        """
        Get current database revision.
        
        Returns:
            Current revision string or empty string if error
        """
        try:
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            result = subprocess.run(
                ["python", "-m", "alembic", "current"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to get revision
            output = result.stdout.strip()
            if output:
                # Extract revision from output like "INFO  [alembic.runtime.migration] Context impl SQLiteImpl."
                # followed by "INFO  [alembic.runtime.migration] Will assume non-transactional DDL."
                # and then the actual revision
                lines = output.split('\n')
                for line in lines:
                    if line and not line.startswith('INFO'):
                        return line.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting current revision: {e}")
            return ""
        
        finally:
            os.chdir(original_cwd)
    
    def get_migration_history(self) -> list:
        """
        Get migration history.
        
        Returns:
            List of migration information
        """
        try:
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            result = subprocess.run(
                ["python", "-m", "alembic", "history"],
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout.strip().split('\n')
            
        except Exception as e:
            logger.error(f"Error getting migration history: {e}")
            return []
        
        finally:
            os.chdir(original_cwd)
    
    def initialize_alembic(self) -> bool:
        """
        Initialize Alembic in the project (if not already initialized).
        
        Returns:
            True if successful, False otherwise
        """
        alembic_dir = self.project_root / "alembic"
        if alembic_dir.exists():
            logger.info("Alembic already initialized")
            return True
        
        return self._run_alembic_command(["init", "alembic"])


def create_initial_migration() -> bool:
    """
    Create the initial database migration.
    
    Returns:
        True if successful, False otherwise
    """
    migration_manager = MigrationManager()
    
    # Create initial migration
    success = migration_manager.create_migration(
        "Initial database schema",
        autogenerate=True
    )
    
    if success:
        logger.info("Initial migration created successfully")
    else:
        logger.error("Failed to create initial migration")
    
    return success


def upgrade_database() -> bool:
    """
    Upgrade database to latest version.
    
    Returns:
        True if successful, False otherwise
    """
    migration_manager = MigrationManager()
    
    success = migration_manager.upgrade_database()
    
    if success:
        logger.info("Database upgraded successfully")
    else:
        logger.error("Failed to upgrade database")
    
    return success


if __name__ == "__main__":
    # Command line interface for migrations
    if len(sys.argv) < 2:
        print("Usage: python migrations.py <command>")
        print("Commands: init, create, upgrade, downgrade, current, history")
        sys.exit(1)
    
    command = sys.argv[1]
    migration_manager = MigrationManager()
    
    if command == "init":
        success = migration_manager.initialize_alembic()
    elif command == "create":
        if len(sys.argv) < 3:
            print("Usage: python migrations.py create <message>")
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        success = migration_manager.create_migration(message)
    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        success = migration_manager.upgrade_database(revision)
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        success = migration_manager.downgrade_database(revision)
    elif command == "current":
        revision = migration_manager.get_current_revision()
        print(f"Current revision: {revision}")
        success = True
    elif command == "history":
        history = migration_manager.get_migration_history()
        for line in history:
            print(line)
        success = True
    else:
        print(f"Unknown command: {command}")
        success = False
    
    sys.exit(0 if success else 1)