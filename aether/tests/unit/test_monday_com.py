#!/usr/bin/env python3
"""
Unit tests for Monday.com integration.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.integrations.monday_com import MondayComIntegration
from core.integrations.monday_types import (
    MondayItem, MondayBoard, MondayAuthConfig, MondayPreferences,
    MondayItemStatus, MondayPriority, MondayColumnValue, MondayUser,
    MondayColumn, MondayGroup, MondayQuery, MondayQueries
)


class TestMondayComIntegration(unittest.TestCase):
    """Test cases for Monday.com integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_config = MondayAuthConfig(
            api_token="test_api_token_12345",
            api_version="2023-10"
        )
        
        self.preferences = MondayPreferences(
            auto_create_items_from_tasks=True,
            sync_task_status=True,
            default_board_id="123456789"
        )
        
        self.monday = MondayComIntegration(self.auth_config, self.preferences)
    
    def test_initialization(self):
        """Test Monday.com integration initialization."""
        self.assertIsNotNone(self.monday)
        self.assertEqual(self.monday.auth_config.api_token, "test_api_token_12345")
        self.assertEqual(self.monday.preferences.default_board_id, "123456789")
        self.assertTrue(self.monday.mock_mode)  # Should be in mock mode
    
    def test_get_boards(self):
        """Test retrieving boards."""
        boards = self.monday.get_boards()
        
        self.assertIsInstance(boards, list)
        self.assertGreater(len(boards), 0)
        
        # Check first board structure
        board = boards[0]
        self.assertIsInstance(board, MondayBoard)
        self.assertEqual(board.name, "Aether Tasks")
        self.assertGreater(len(board.columns), 0)
        self.assertGreater(len(board.groups), 0)
    
    def test_get_specific_board(self):
        """Test retrieving a specific board by ID."""
        board = self.monday.get_board("123456789")
        
        self.assertIsNotNone(board)
        self.assertEqual(board.id, "123456789")
        self.assertEqual(board.name, "Aether Tasks")
        
        # Test non-existent board
        non_existent = self.monday.get_board("999999999")
        self.assertIsNone(non_existent)
    
    def test_create_item(self):
        """Test creating Monday.com items."""
        item_id = self.monday.create_item(
            board_id="123456789",
            item_name="Test Item",
            column_values={
                "status": {"label": "Working on it"},
                "priority": {"label": "High"}
            }
        )
        
        self.assertIsNotNone(item_id)
        self.assertTrue(item_id.startswith("mock_item_"))
        
        # Verify item was added to mock storage
        mock_item = next(
            (item for item in self.monday.mock_items if item.id == item_id),
            None
        )
        self.assertIsNotNone(mock_item)
        self.assertEqual(mock_item.name, "Test Item")
        self.assertEqual(mock_item.board_id, "123456789")
    
    def test_update_item(self):
        """Test updating Monday.com items."""
        # Create an item first
        item_id = self.monday.create_item(
            board_id="123456789",
            item_name="Item to Update"
        )
        
        # Update the item
        update_success = self.monday.update_item(
            item_id,
            {
                "status": {"label": "Done"},
                "priority": {"label": "Critical"}
            }
        )
        
        self.assertTrue(update_success)
        
        # Verify the update
        mock_item = next(
            (item for item in self.monday.mock_items if item.id == item_id),
            None
        )
        self.assertIsNotNone(mock_item)
        
        # Check if column values were updated
        status_value = mock_item.get_column_value("status")
        self.assertIsNotNone(status_value)
    
    def test_delete_item(self):
        """Test deleting Monday.com items."""
        # Create an item first
        item_id = self.monday.create_item(
            board_id="123456789",
            item_name="Item to Delete"
        )
        
        initial_count = len(self.monday.mock_items)
        
        # Delete the item
        delete_success = self.monday.delete_item(item_id)
        self.assertTrue(delete_success)
        
        # Verify deletion
        self.assertEqual(len(self.monday.mock_items), initial_count - 1)
        
        # Verify item is no longer in mock storage
        deleted_item = next(
            (item for item in self.monday.mock_items if item.id == item_id),
            None
        )
        self.assertIsNone(deleted_item)
    
    def test_task_synchronization(self):
        """Test synchronizing tasks with Monday.com items."""
        # Create mock tasks
        class MockTask:
            def __init__(self, id, title, description, status="todo", priority="medium"):
                self.id = id
                self.title = title
                self.description = description
                self.status = type('Status', (), {'value': status})()
                self.priority = type('Priority', (), {'value': priority})()
        
        tasks = [
            MockTask("task_1", "Task 1", "Description 1", "in_progress", "high"),
            MockTask("task_2", "Task 2", "Description 2", "todo", "medium")
        ]
        
        initial_item_count = len(self.monday.mock_items)
        
        # Sync tasks
        sync_result = self.monday.sync_with_tasks(tasks)
        
        self.assertTrue(sync_result.success)
        self.assertEqual(sync_result.items_created, 2)
        self.assertEqual(sync_result.items_updated, 0)
        self.assertEqual(sync_result.boards_accessed, 1)
        self.assertEqual(len(self.monday.mock_items), initial_item_count + 2)
    
    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        # Create a test item
        item_id = self.monday.create_item(
            board_id="123456789",
            item_name="Progress Test Item"
        )
        
        # Test progress tracking
        track_success = self.monday.track_progress(
            item_id, 
            75.0, 
            "Three quarters complete"
        )
        
        self.assertTrue(track_success)
        
        # Verify the item was updated
        mock_item = next(
            (item for item in self.monday.mock_items if item.id == item_id),
            None
        )
        self.assertIsNotNone(mock_item)
    
    def test_assignment_functionality(self):
        """Test item assignment functionality."""
        # Create a test item
        item_id = self.monday.create_item(
            board_id="123456789",
            item_name="Assignment Test Item"
        )
        
        # Test assignment
        assign_success = self.monday.assign_item(item_id, "12345")
        self.assertTrue(assign_success)
        
        # Test due date setting
        due_date = datetime.now() + timedelta(days=3)
        due_date_success = self.monday.set_due_date(item_id, due_date)
        self.assertTrue(due_date_success)
    
    def test_automation_and_webhooks(self):
        """Test automation and webhook setup."""
        # Test automation creation
        automation_config = {
            "name": "Test Automation",
            "trigger": {"type": "when_status_changes"},
            "actions": [{"type": "notify_person"}]
        }
        
        automation_id = self.monday.create_automation("123456789", automation_config)
        self.assertIsNotNone(automation_id)
        self.assertTrue(automation_id.startswith("mock_automation_"))
        
        # Test webhook setup
        webhook_id = self.monday.setup_webhook(
            "123456789",
            "https://example.com/webhook",
            ["create_item", "change_status"]
        )
        self.assertIsNotNone(webhook_id)
        self.assertTrue(webhook_id.startswith("mock_webhook_"))


class TestMondayTypes(unittest.TestCase):
    """Test cases for Monday.com data types."""
    
    def test_monday_item_creation(self):
        """Test creating Monday.com items."""
        item = MondayItem(
            name="Test Item",
            board_id="123456789"
        )
        
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.board_id, "123456789")
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)
    
    def test_column_value_management(self):
        """Test column value management."""
        item = MondayItem(name="Test Item")
        
        # Set column values
        item.set_column_value("status", {"label": "Working on it"})
        item.set_column_value("priority", {"label": "High"})
        
        # Get column values
        status_value = item.get_column_value("status")
        self.assertIsNotNone(status_value)
        self.assertEqual(status_value.column_id, "status")
        
        priority_value = item.get_column_value("priority")
        self.assertIsNotNone(priority_value)
        self.assertEqual(priority_value.column_id, "priority")
        
        # Test non-existent column
        non_existent = item.get_column_value("non_existent")
        self.assertIsNone(non_existent)
    
    def test_status_management(self):
        """Test status management methods."""
        item = MondayItem(name="Test Item")
        
        # Set status using enum
        item.set_status(MondayItemStatus.WORKING_ON_IT)
        status = item.get_status()
        self.assertEqual(status, "working_on_it")
        
        # Set status using string
        item.set_status("done")
        status = item.get_status()
        self.assertEqual(status, "done")
    
    def test_monday_board_structure(self):
        """Test Monday.com board structure."""
        board = MondayBoard(
            name="Test Board",
            description="A test board"
        )
        
        # Add columns
        board.columns.append(MondayColumn(
            id="title",
            title="Task",
            type="text"
        ))
        board.columns.append(MondayColumn(
            id="status",
            title="Status", 
            type="status"
        ))
        
        # Add groups
        board.groups.append(MondayGroup(
            id="group1",
            title="To Do",
            color="#ff0000"
        ))
        
        # Test column lookup
        title_column = board.get_column_by_title("Task")
        self.assertIsNotNone(title_column)
        self.assertEqual(title_column.id, "title")
        
        # Test group lookup
        todo_group = board.get_group_by_title("To Do")
        self.assertIsNotNone(todo_group)
        self.assertEqual(todo_group.id, "group1")
    
    def test_column_value_formatting(self):
        """Test column value formatting for Monday.com API."""
        # Test different value types
        text_value = MondayColumnValue("text_col", "Hello World")
        text_format = text_value.to_monday_format()
        self.assertEqual(text_format, {"text": "Hello World"})
        
        bool_value = MondayColumnValue("checkbox_col", True)
        bool_format = bool_value.to_monday_format()
        self.assertEqual(bool_format, {"checked": "true"})
        
        number_value = MondayColumnValue("number_col", 42)
        number_format = number_value.to_monday_format()
        self.assertEqual(number_format, {"number": "42"})
        
        date_value = MondayColumnValue("date_col", datetime(2023, 12, 25))
        date_format = date_value.to_monday_format()
        self.assertEqual(date_format, {"date": "2023-12-25"})
    
    def test_monday_queries(self):
        """Test Monday.com GraphQL query generation."""
        # Test boards query
        boards_query = MondayQueries.get_boards()
        self.assertIsInstance(boards_query, MondayQuery)
        self.assertIn("boards", boards_query.query)
        
        # Test board items query
        items_query = MondayQueries.get_board_items("123456789")
        self.assertIsInstance(items_query, MondayQuery)
        self.assertIn("boards", items_query.query)
        self.assertEqual(items_query.variables["board_id"], [123456789])
        
        # Test create item query
        create_query = MondayQueries.create_item("123456789", "group1", "Test Item")
        self.assertIsInstance(create_query, MondayQuery)
        self.assertIn("create_item", create_query.query)
        self.assertEqual(create_query.variables["board_id"], 123456789)
        self.assertEqual(create_query.variables["item_name"], "Test Item")
        
        # Test update item query
        update_query = MondayQueries.update_item("987654321", {"status": {"label": "Done"}})
        self.assertIsInstance(update_query, MondayQuery)
        self.assertIn("change_multiple_column_values", update_query.query)
        self.assertEqual(update_query.variables["item_id"], 987654321)
        
        # Test delete item query
        delete_query = MondayQueries.delete_item("987654321")
        self.assertIsInstance(delete_query, MondayQuery)
        self.assertIn("delete_item", delete_query.query)
        self.assertEqual(delete_query.variables["item_id"], 987654321)
    
    def test_auth_config(self):
        """Test Monday.com authentication configuration."""
        auth_config = MondayAuthConfig(
            api_token="test_token_123",
            api_version="2023-10"
        )
        
        self.assertEqual(auth_config.api_token, "test_token_123")
        self.assertEqual(auth_config.api_version, "2023-10")
        self.assertEqual(auth_config.base_url, "https://api.monday.com/v2")
    
    def test_preferences(self):
        """Test Monday.com preferences."""
        preferences = MondayPreferences(
            default_board_id="123456789",
            auto_create_items_from_tasks=True,
            sync_task_status=True,
            status_column_id="status",
            assignee_column_id="person"
        )
        
        self.assertEqual(preferences.default_board_id, "123456789")
        self.assertTrue(preferences.auto_create_items_from_tasks)
        self.assertTrue(preferences.sync_task_status)
        self.assertEqual(preferences.status_column_id, "status")
        self.assertEqual(preferences.assignee_column_id, "person")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)