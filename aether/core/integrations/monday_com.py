"""
Monday.com API integration for Aether AI Companion.
"""

import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .monday_types import (
    MondayItem, MondayBoard, MondayWorkspace, MondayUser, MondayColumn,
    MondayGroup, MondayColumnValue, MondayItemStatus, MondayPriority,
    MondaySyncResult, MondayAuthConfig, MondayPreferences, MondayQuery,
    MondayQueries, MondayWebhook, MondayAutomation
)

logger = logging.getLogger(__name__)


class MondayComIntegration:
    """Monday.com API integration."""
    
    def __init__(self, auth_config: MondayAuthConfig, preferences: MondayPreferences = None):
        """Initialize Monday.com integration."""
        self.auth_config = auth_config
        self.preferences = preferences or MondayPreferences()
        self.session = requests.Session()
        self._setup_session()
        
        # Mock mode for development/testing
        self.mock_mode = False
        self.mock_boards = []
        self.mock_items = []
        
        # Test connection
        self._test_connection()
    
    def _setup_session(self):
        """Set up HTTP session with authentication."""
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_config.api_token}",
            "Content-Type": "application/json",
            "API-Version": self.auth_config.api_version
        })
    
    def _test_connection(self):
        """Test connection to Monday.com API."""
        try:
            # Simple query to test authentication
            query = MondayQuery(query="query { me { id name email } }")
            response = self._execute_query(query)
            
            if response and "data" in response and "me" in response["data"]:
                user_info = response["data"]["me"]
                logger.info(f"Connected to Monday.com as {user_info['name']} ({user_info['email']})")
                return True
            else:
                logger.warning("Monday.com API connection test failed, using mock mode")
                self._setup_mock_mode()
                return False
                
        except Exception as e:
            logger.warning(f"Monday.com API not available: {e}")
            self._setup_mock_mode()
            return False
    
    def _setup_mock_mode(self):
        """Set up mock mode when Monday.com API isn't available."""
        logger.info("Setting up Monday.com integration in mock mode")
        self.mock_mode = True
        
        # Create sample mock data
        self._create_mock_data()
    
    def _create_mock_data(self):
        """Create sample mock data for testing."""
        # Mock board
        mock_board = MondayBoard(
            id="123456789",
            name="Aether Tasks",
            description="Tasks managed by Aether AI"
        )
        
        # Add columns
        mock_board.columns = [
            MondayColumn(id="title", title="Task", type="text"),
            MondayColumn(id="status", title="Status", type="status"),
            MondayColumn(id="person", title="Assignee", type="person"),
            MondayColumn(id="date", title="Due Date", type="date"),
            MondayColumn(id="priority", title="Priority", type="dropdown")
        ]
        
        # Add groups
        mock_board.groups = [
            MondayGroup(id="topics", title="Tasks", color="#037f4c"),
            MondayGroup(id="group1", title="In Progress", color="#fdab3d"),
            MondayGroup(id="group2", title="Completed", color="#00c875")
        ]
        
        self.mock_boards.append(mock_board)
    
    def _execute_query(self, query: MondayQuery) -> Optional[Dict[str, Any]]:
        """Execute a GraphQL query against Monday.com API."""
        if self.mock_mode:
            return self._mock_execute_query(query)
        
        try:
            response = self.session.post(
                self.auth_config.base_url,
                json=query.to_request_body(),
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                logger.error(f"Monday.com API errors: {result['errors']}")
                return None
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Monday.com API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Monday.com API response: {e}")
            return None
    
    def get_boards(self) -> List[MondayBoard]:
        """Get all accessible boards."""
        if self.mock_mode:
            return self.mock_boards.copy()
        
        query = MondayQueries.get_boards()
        response = self._execute_query(query)
        
        if not response or "data" not in response:
            return []
        
        boards = []
        for board_data in response["data"]["boards"]:
            board = self._parse_board_data(board_data)
            if board:
                boards.append(board)
        
        logger.info(f"Retrieved {len(boards)} boards from Monday.com")
        return boards
    
    def get_board(self, board_id: str) -> Optional[MondayBoard]:
        """Get a specific board by ID."""
        if self.mock_mode:
            for board in self.mock_boards:
                if board.id == board_id:
                    return board
            return None
        
        boards = self.get_boards()
        for board in boards:
            if board.id == board_id:
                return board
        return None
    
    def get_board_items(self, board_id: str) -> List[MondayItem]:
        """Get all items from a specific board."""
        if self.mock_mode:
            return [item for item in self.mock_items if item.board_id == board_id]
        
        query = MondayQueries.get_board_items(board_id)
        response = self._execute_query(query)
        
        if not response or "data" not in response:
            return []
        
        items = []
        for board_data in response["data"]["boards"]:
            for item_data in board_data.get("items", []):
                item = self._parse_item_data(item_data, board_id)
                if item:
                    items.append(item)
        
        logger.info(f"Retrieved {len(items)} items from board {board_id}")
        return items
    
    def create_item(
        self, 
        board_id: str, 
        item_name: str, 
        group_id: str = None,
        column_values: Dict[str, Any] = None
    ) -> Optional[str]:
        """Create a new item in a board."""
        if self.mock_mode:
            return self._mock_create_item(board_id, item_name, group_id, column_values)
        
        # Use default group if not specified
        if not group_id:
            board = self.get_board(board_id)
            if board and board.groups:
                group_id = board.groups[0].id
            else:
                group_id = "topics"  # Default group name
        
        # Format column values for Monday.com API
        formatted_values = {}
        if column_values:
            for column_id, value in column_values.items():
                if isinstance(value, dict):
                    formatted_values[column_id] = json.dumps(value)
                else:
                    formatted_values[column_id] = json.dumps({"text": str(value)})
        
        query = MondayQueries.create_item(board_id, group_id, item_name, formatted_values)
        response = self._execute_query(query)
        
        if response and "data" in response and "create_item" in response["data"]:
            item_data = response["data"]["create_item"]
            item_id = item_data["id"]
            logger.info(f"Created Monday.com item: {item_id}")
            return item_id
        
        return None
    
    def update_item(self, item_id: str, column_values: Dict[str, Any]) -> bool:
        """Update an existing item."""
        if self.mock_mode:
            return self._mock_update_item(item_id, column_values)
        
        # Format column values for Monday.com API
        formatted_values = {}
        for column_id, value in column_values.items():
            if isinstance(value, dict):
                formatted_values[column_id] = json.dumps(value)
            else:
                formatted_values[column_id] = json.dumps({"text": str(value)})
        
        query = MondayQueries.update_item(item_id, formatted_values)
        response = self._execute_query(query)
        
        if response and "data" in response:
            logger.info(f"Updated Monday.com item: {item_id}")
            return True
        
        return False
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item."""
        if self.mock_mode:
            return self._mock_delete_item(item_id)
        
        query = MondayQueries.delete_item(item_id)
        response = self._execute_query(query)
        
        if response and "data" in response:
            logger.info(f"Deleted Monday.com item: {item_id}")
            return True
        
        return False    

    def sync_with_tasks(self, tasks: List[Any]) -> MondaySyncResult:
        """Synchronize tasks with Monday.com items."""
        result = MondaySyncResult(success=True)
        
        try:
            # Get default board
            board_id = self.preferences.default_board_id
            if not board_id:
                boards = self.get_boards()
                if boards:
                    board_id = boards[0].id
                    logger.info(f"Using default board: {board_id}")
                else:
                    result.success = False
                    result.errors.append("No boards available")
                    return result
            
            for task in tasks:
                # Only sync tasks that are not completed
                if hasattr(task, 'status') and task.status.value == 'completed':
                    continue
                
                # Check if item already exists
                existing_item_id = self._find_item_by_task_id(task.id)
                
                if existing_item_id:
                    # Update existing item
                    column_values = self._convert_task_to_column_values(task)
                    if self.update_item(existing_item_id, column_values):
                        result.items_updated += 1
                else:
                    # Create new item
                    column_values = self._convert_task_to_column_values(task)
                    item_id = self.create_item(
                        board_id=board_id,
                        item_name=task.title,
                        column_values=column_values
                    )
                    
                    if item_id:
                        result.items_created += 1
                        # Store the mapping for future updates
                        self._store_task_item_mapping(task.id, item_id)
            
            result.boards_accessed = 1
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Task sync failed: {e}")
        
        return result
    
    def track_progress(self, item_id: str, progress_percentage: float, notes: str = None) -> bool:
        """Track progress on a Monday.com item."""
        column_values = {}
        
        # Update progress if there's a numbers column
        if hasattr(self.preferences, 'progress_column_id'):
            column_values[self.preferences.progress_column_id] = progress_percentage
        
        # Add notes if there's a long text column
        if notes and hasattr(self.preferences, 'notes_column_id'):
            column_values[self.preferences.notes_column_id] = notes
        
        # Update status based on progress
        if progress_percentage >= 100:
            column_values[self.preferences.status_column_id] = {"label": "Done"}
        elif progress_percentage > 0:
            column_values[self.preferences.status_column_id] = {"label": "Working on it"}
        
        return self.update_item(item_id, column_values)
    
    def assign_item(self, item_id: str, user_id: str) -> bool:
        """Assign an item to a user."""
        # Try to convert user_id to int, fallback to string for mock mode
        try:
            user_id_int = int(user_id)
            column_values = {
                self.preferences.assignee_column_id: {"personsAndTeams": [{"id": user_id_int, "kind": "person"}]}
            }
        except ValueError:
            # For mock mode or string user IDs
            column_values = {
                self.preferences.assignee_column_id: {"text": f"Assigned to {user_id}"}
            }
        
        return self.update_item(item_id, column_values)
    
    def set_due_date(self, item_id: str, due_date: datetime) -> bool:
        """Set due date for an item."""
        column_values = {
            self.preferences.due_date_column_id: {"date": due_date.strftime("%Y-%m-%d")}
        }
        
        return self.update_item(item_id, column_values)
    
    def create_automation(self, board_id: str, automation_config: Dict[str, Any]) -> Optional[str]:
        """Create an automation rule."""
        # This would typically use Monday.com's automation API
        # For now, we'll log the automation request
        logger.info(f"Automation requested for board {board_id}: {automation_config}")
        
        if self.mock_mode:
            return f"mock_automation_{len(self.mock_boards) + 1}"
        
        # In a real implementation, this would create the automation
        return None
    
    def setup_webhook(self, board_id: str, webhook_url: str, events: List[str]) -> Optional[str]:
        """Set up a webhook for board events."""
        webhook_config = {
            "board_id": board_id,
            "url": webhook_url,
            "events": events
        }
        
        logger.info(f"Webhook setup requested: {webhook_config}")
        
        if self.mock_mode:
            return f"mock_webhook_{len(self.mock_boards) + 1}"
        
        # In a real implementation, this would create the webhook
        return None
    
    def _parse_board_data(self, board_data: Dict[str, Any]) -> Optional[MondayBoard]:
        """Parse board data from Monday.com API response."""
        try:
            board = MondayBoard(
                id=str(board_data["id"]),
                name=board_data["name"],
                description=board_data.get("description")
            )
            
            # Parse columns
            for col_data in board_data.get("columns", []):
                column = MondayColumn(
                    id=col_data["id"],
                    title=col_data["title"],
                    type=col_data["type"],
                    settings_str=col_data.get("settings_str")
                )
                board.columns.append(column)
            
            # Parse groups
            for group_data in board_data.get("groups", []):
                group = MondayGroup(
                    id=group_data["id"],
                    title=group_data["title"],
                    color=group_data.get("color")
                )
                board.groups.append(group)
            
            # Parse owners
            for owner_data in board_data.get("owners", []):
                user = MondayUser(
                    id=str(owner_data["id"]),
                    name=owner_data["name"],
                    email=owner_data["email"]
                )
                board.owners.append(user)
            
            return board
            
        except Exception as e:
            logger.error(f"Failed to parse board data: {e}")
            return None
    
    def _parse_item_data(self, item_data: Dict[str, Any], board_id: str) -> Optional[MondayItem]:
        """Parse item data from Monday.com API response."""
        try:
            item = MondayItem(
                id=str(item_data["id"]),
                name=item_data["name"],
                board_id=board_id
            )
            
            # Parse group
            if "group" in item_data and item_data["group"]:
                item.group_id = item_data["group"]["id"]
            
            # Parse column values
            for cv_data in item_data.get("column_values", []):
                column_value = MondayColumnValue(
                    column_id=cv_data["id"],
                    value=cv_data.get("value"),
                    text=cv_data.get("text")
                )
                item.column_values.append(column_value)
            
            # Parse timestamps
            if "created_at" in item_data:
                item.created_at = datetime.fromisoformat(item_data["created_at"].replace("Z", "+00:00"))
            if "updated_at" in item_data:
                item.updated_at = datetime.fromisoformat(item_data["updated_at"].replace("Z", "+00:00"))
            
            # Parse creator
            if "creator" in item_data and item_data["creator"]:
                item.creator_id = str(item_data["creator"]["id"])
            
            return item
            
        except Exception as e:
            logger.error(f"Failed to parse item data: {e}")
            return None
    
    def _convert_task_to_column_values(self, task) -> Dict[str, Any]:
        """Convert a task to Monday.com column values."""
        column_values = {}
        
        # Status mapping
        if hasattr(task, 'status'):
            status_map = {
                'todo': 'Not Started',
                'in_progress': 'Working on it',
                'completed': 'Done',
                'cancelled': 'Cancelled'
            }
            monday_status = status_map.get(task.status.value, 'Not Started')
            column_values[self.preferences.status_column_id] = {"label": monday_status}
        
        # Priority mapping
        if hasattr(task, 'priority'):
            priority_map = {
                'low': 'Low',
                'medium': 'Medium', 
                'high': 'High',
                'urgent': 'Critical'
            }
            monday_priority = priority_map.get(task.priority.value, 'Medium')
            column_values[self.preferences.priority_column_id] = {"label": monday_priority}
        
        # Due date
        if hasattr(task, 'due_date') and task.due_date:
            column_values[self.preferences.due_date_column_id] = {
                "date": task.due_date.strftime("%Y-%m-%d")
            }
        
        # Description in long text column
        if hasattr(task, 'description') and task.description:
            column_values["long_text"] = {"text": task.description}
        
        return column_values
    
    def _find_item_by_task_id(self, task_id: str) -> Optional[str]:
        """Find Monday.com item ID associated with a task."""
        # This would typically query a local database or cache
        # For now, return None (item doesn't exist)
        return None
    
    def _store_task_item_mapping(self, task_id: str, item_id: str):
        """Store mapping between task ID and Monday.com item ID."""
        # This would typically store in a local database
        logger.info(f"Storing mapping: task {task_id} -> Monday.com item {item_id}")
    
    # Mock methods for testing
    def _mock_execute_query(self, query: MondayQuery) -> Dict[str, Any]:
        """Mock query execution for testing."""
        # Simple mock responses based on query content
        if "me {" in query.query:
            return {
                "data": {
                    "me": {
                        "id": "12345",
                        "name": "Test User",
                        "email": "test@example.com"
                    }
                }
            }
        elif "boards {" in query.query:
            return {
                "data": {
                    "boards": [
                        {
                            "id": "123456789",
                            "name": "Aether Tasks",
                            "description": "Tasks managed by Aether AI",
                            "columns": [
                                {"id": "title", "title": "Task", "type": "text"},
                                {"id": "status", "title": "Status", "type": "status"},
                                {"id": "person", "title": "Assignee", "type": "person"},
                                {"id": "date", "title": "Due Date", "type": "date"}
                            ],
                            "groups": [
                                {"id": "topics", "title": "Tasks", "color": "#037f4c"}
                            ],
                            "owners": [
                                {"id": "12345", "name": "Test User", "email": "test@example.com"}
                            ]
                        }
                    ]
                }
            }
        elif "create_item" in query.query:
            return {
                "data": {
                    "create_item": {
                        "id": f"mock_item_{len(self.mock_items) + 1}",
                        "name": query.variables.get("item_name", "Mock Item"),
                        "created_at": datetime.utcnow().isoformat()
                    }
                }
            }
        else:
            return {"data": {}}
    
    def _mock_create_item(self, board_id: str, item_name: str, group_id: str, column_values: Dict[str, Any]) -> str:
        """Mock item creation for testing."""
        item_id = f"mock_item_{len(self.mock_items) + 1}"
        
        item = MondayItem(
            id=item_id,
            name=item_name,
            board_id=board_id,
            group_id=group_id or "topics"
        )
        
        # Add column values
        if column_values:
            for col_id, value in column_values.items():
                item.set_column_value(col_id, value)
        
        self.mock_items.append(item)
        logger.info(f"Mock: Created item {item_id}")
        return item_id
    
    def _mock_update_item(self, item_id: str, column_values: Dict[str, Any]) -> bool:
        """Mock item update for testing."""
        for item in self.mock_items:
            if item.id == item_id:
                for col_id, value in column_values.items():
                    item.set_column_value(col_id, value)
                item.updated_at = datetime.utcnow()
                logger.info(f"Mock: Updated item {item_id}")
                return True
        return False
    
    def _mock_delete_item(self, item_id: str) -> bool:
        """Mock item deletion for testing."""
        for i, item in enumerate(self.mock_items):
            if item.id == item_id:
                del self.mock_items[i]
                logger.info(f"Mock: Deleted item {item_id}")
                return True
        return False


# Global Monday.com integration instance
_monday_integration = None


def get_monday_integration(
    auth_config: MondayAuthConfig = None,
    preferences: MondayPreferences = None
) -> MondayComIntegration:
    """Get a singleton instance of the Monday.com integration."""
    global _monday_integration
    
    if _monday_integration is None:
        if not auth_config:
            # Use mock configuration for testing
            auth_config = MondayAuthConfig(api_token="mock_token")
        
        _monday_integration = MondayComIntegration(auth_config, preferences)
    
    return _monday_integration