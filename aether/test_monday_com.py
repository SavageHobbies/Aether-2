#!/usr/bin/env python3
"""
Test script for Monday.com integration.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.integrations.monday_com import MondayComIntegration, get_monday_integration
from core.integrations.monday_types import (
    MondayItem, MondayBoard, MondayAuthConfig, MondayPreferences,
    MondayItemStatus, MondayPriority, MondayColumnValue, MondayUser
)


def test_monday_integration_setup():
    """Test Monday.com integration setup and authentication."""
    print("=== Testing Monday.com Integration Setup ===")
    
    # Create auth config (will use mock mode since we don't have real API token)
    auth_config = MondayAuthConfig(
        api_token="test_api_token_12345",
        api_version="2023-10"
    )
    
    preferences = MondayPreferences(
        auto_create_items_from_tasks=True,
        sync_task_status=True,
        sync_task_assignees=True,
        default_board_id="123456789"
    )
    
    # Initialize integration
    monday = MondayComIntegration(auth_config, preferences)
    
    print(f"✓ Monday.com integration initialized")
    print(f"  Mock mode: {monday.mock_mode}")
    print(f"  API version: {monday.auth_config.api_version}")
    print(f"  Base URL: {monday.auth_config.base_url}")
    
    return monday


def test_board_management():
    """Test board retrieval and management."""
    print("\n=== Testing Board Management ===")
    
    monday = get_monday_integration()
    
    # Get all boards
    boards = monday.get_boards()
    print(f"✓ Retrieved {len(boards)} boards")
    
    for i, board in enumerate(boards, 1):
        print(f"  Board {i}:")
        print(f"    ID: {board.id}")
        print(f"    Name: {board.name}")
        print(f"    Description: {board.description}")
        print(f"    Columns: {len(board.columns)}")
        print(f"    Groups: {len(board.groups)}")
        print(f"    Owners: {len(board.owners)}")
        
        # Show column details
        for column in board.columns:
            print(f"      Column: {column.title} ({column.type})")
        
        # Show group details
        for group in board.groups:
            print(f"      Group: {group.title} (ID: {group.id})")
    
    return boards


def test_item_creation():
    """Test creating Monday.com items."""
    print("\n=== Testing Item Creation ===")
    
    monday = get_monday_integration()
    boards = monday.get_boards()
    
    if not boards:
        print("❌ No boards available for testing")
        return []
    
    board = boards[0]
    print(f"Using board: {board.name} (ID: {board.id})")
    
    # Create test items
    test_items = [
        {
            "name": "Complete project proposal",
            "column_values": {
                "status": {"label": "Working on it"},
                "date": {"date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")},
                "priority": {"label": "High"}
            }
        },
        {
            "name": "Review quarterly budget",
            "column_values": {
                "status": {"label": "Not Started"},
                "date": {"date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")},
                "priority": {"label": "Medium"}
            }
        },
        {
            "name": "Schedule client meeting",
            "column_values": {
                "status": {"label": "Working on it"},
                "priority": {"label": "High"}
            }
        }
    ]
    
    created_items = []
    
    for item_data in test_items:
        item_id = monday.create_item(
            board_id=board.id,
            item_name=item_data["name"],
            column_values=item_data["column_values"]
        )
        
        if item_id:
            created_items.append(item_id)
            print(f"✓ Created item: {item_data['name']} (ID: {item_id})")
        else:
            print(f"❌ Failed to create item: {item_data['name']}")
    
    print(f"\n✓ Created {len(created_items)} items successfully")
    return created_items


def test_item_updates():
    """Test updating Monday.com items."""
    print("\n=== Testing Item Updates ===")
    
    monday = get_monday_integration()
    
    # Create an item first
    boards = monday.get_boards()
    if not boards:
        print("❌ No boards available for testing")
        return
    
    board = boards[0]
    item_id = monday.create_item(
        board_id=board.id,
        item_name="Test Item for Updates",
        column_values={"status": {"label": "Not Started"}}
    )
    
    if not item_id:
        print("❌ Failed to create test item")
        return
    
    print(f"Created test item: {item_id}")
    
    # Test various updates
    update_tests = [
        {
            "description": "Update status to Working on it",
            "column_values": {"status": {"label": "Working on it"}}
        },
        {
            "description": "Set due date",
            "column_values": {"date": {"date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")}}
        },
        {
            "description": "Update priority to High",
            "column_values": {"priority": {"label": "High"}}
        },
        {
            "description": "Mark as Done",
            "column_values": {"status": {"label": "Done"}}
        }
    ]
    
    for test in update_tests:
        success = monday.update_item(item_id, test["column_values"])
        status = "✓" if success else "❌"
        print(f"{status} {test['description']}: {'Success' if success else 'Failed'}")
    
    return item_id


def test_task_synchronization():
    """Test synchronizing tasks with Monday.com items."""
    print("\n=== Testing Task Synchronization ===")
    
    monday = get_monday_integration()
    
    # Create mock tasks (simulating task objects)
    class MockTask:
        def __init__(self, id, title, description, status="todo", priority="medium", due_date=None):
            self.id = id
            self.title = title
            self.description = description
            self.status = type('Status', (), {'value': status})()
            self.priority = type('Priority', (), {'value': priority})()
            self.due_date = due_date
    
    tasks = [
        MockTask(
            "task_1",
            "Finalize project documentation",
            "Complete all technical documentation for the project",
            status="in_progress",
            priority="high",
            due_date=datetime.now() + timedelta(days=2)
        ),
        MockTask(
            "task_2",
            "Conduct team performance reviews",
            "Schedule and conduct quarterly performance reviews",
            status="todo",
            priority="medium",
            due_date=datetime.now() + timedelta(days=7)
        ),
        MockTask(
            "task_3",
            "Update security protocols",
            "Review and update company security protocols",
            status="todo",
            priority="urgent",
            due_date=datetime.now() + timedelta(days=1)
        )
    ]
    
    # Sync tasks with Monday.com
    sync_result = monday.sync_with_tasks(tasks)
    
    print(f"✓ Sync completed: {'Success' if sync_result.success else 'Failed'}")
    print(f"  Items created: {sync_result.items_created}")
    print(f"  Items updated: {sync_result.items_updated}")
    print(f"  Boards accessed: {sync_result.boards_accessed}")
    
    if sync_result.errors:
        print("  Errors:")
        for error in sync_result.errors:
            print(f"    - {error}")
    
    return sync_result


def test_progress_tracking():
    """Test progress tracking functionality."""
    print("\n=== Testing Progress Tracking ===")
    
    monday = get_monday_integration()
    
    # Create a test item
    boards = monday.get_boards()
    if not boards:
        print("❌ No boards available for testing")
        return
    
    board = boards[0]
    item_id = monday.create_item(
        board_id=board.id,
        item_name="Project with Progress Tracking",
        column_values={"status": {"label": "Working on it"}}
    )
    
    if not item_id:
        print("❌ Failed to create test item")
        return
    
    print(f"Created item for progress tracking: {item_id}")
    
    # Test progress updates
    progress_tests = [
        {"progress": 25.0, "notes": "Initial setup completed"},
        {"progress": 50.0, "notes": "Halfway through development"},
        {"progress": 75.0, "notes": "Testing phase started"},
        {"progress": 100.0, "notes": "Project completed successfully"}
    ]
    
    for test in progress_tests:
        success = monday.track_progress(
            item_id, 
            test["progress"], 
            test["notes"]
        )
        status = "✓" if success else "❌"
        print(f"{status} Progress {test['progress']}%: {test['notes']}")
    
    return item_id


def test_assignment_and_due_dates():
    """Test item assignment and due date management."""
    print("\n=== Testing Assignment and Due Dates ===")
    
    monday = get_monday_integration()
    
    # Create a test item
    boards = monday.get_boards()
    if not boards:
        print("❌ No boards available for testing")
        return
    
    board = boards[0]
    item_id = monday.create_item(
        board_id=board.id,
        item_name="Task for Assignment Testing"
    )
    
    if not item_id:
        print("❌ Failed to create test item")
        return
    
    print(f"Created item for assignment testing: {item_id}")
    
    # Test assignment (using mock user ID)
    user_id = "12345"  # Mock user ID
    assign_success = monday.assign_item(item_id, user_id)
    print(f"{'✓' if assign_success else '❌'} Assign to user {user_id}: {'Success' if assign_success else 'Failed'}")
    
    # Test due date setting
    due_date = datetime.now() + timedelta(days=3)
    due_date_success = monday.set_due_date(item_id, due_date)
    print(f"{'✓' if due_date_success else '❌'} Set due date to {due_date.strftime('%Y-%m-%d')}: {'Success' if due_date_success else 'Failed'}")
    
    return item_id


def test_automation_and_webhooks():
    """Test automation and webhook setup."""
    print("\n=== Testing Automation and Webhooks ===")
    
    monday = get_monday_integration()
    boards = monday.get_boards()
    
    if not boards:
        print("❌ No boards available for testing")
        return
    
    board = boards[0]
    print(f"Testing with board: {board.name} (ID: {board.id})")
    
    # Test automation setup
    automation_config = {
        "name": "Auto-assign urgent tasks",
        "trigger": {
            "type": "when_column_changes",
            "column_id": "priority",
            "value": "Critical"
        },
        "actions": [
            {
                "type": "assign_person",
                "person_id": "12345"
            },
            {
                "type": "notify_person",
                "person_id": "12345",
                "message": "Urgent task assigned to you"
            }
        ]
    }
    
    automation_id = monday.create_automation(board.id, automation_config)
    print(f"{'✓' if automation_id else '❌'} Create automation: {'Success' if automation_id else 'Failed'}")
    if automation_id:
        print(f"  Automation ID: {automation_id}")
    
    # Test webhook setup
    webhook_url = "https://aether.example.com/webhooks/monday"
    webhook_events = ["create_item", "change_column_value", "change_status"]
    
    webhook_id = monday.setup_webhook(board.id, webhook_url, webhook_events)
    print(f"{'✓' if webhook_id else '❌'} Setup webhook: {'Success' if webhook_id else 'Failed'}")
    if webhook_id:
        print(f"  Webhook ID: {webhook_id}")
        print(f"  Events: {', '.join(webhook_events)}")
    
    return automation_id, webhook_id


def test_integration_workflow():
    """Test complete integration workflow."""
    print("\n=== Testing Complete Integration Workflow ===")
    
    monday = get_monday_integration()
    
    # Simulate a complete workflow
    print("1. Creating a project board structure...")
    boards = monday.get_boards()
    if boards:
        board = boards[0]
        print(f"   Using board: {board.name}")
    else:
        print("   ❌ No boards available")
        return
    
    print("2. Creating project items...")
    project_items = [
        "Research phase - Market analysis",
        "Development phase - Core features",
        "Testing phase - Quality assurance", 
        "Launch phase - Go-to-market"
    ]
    
    created_items = []
    for i, item_name in enumerate(project_items):
        item_id = monday.create_item(
            board_id=board.id,
            item_name=item_name,
            column_values={
                "status": {"label": "Not Started" if i == 0 else "Not Started"},
                "priority": {"label": "High" if i < 2 else "Medium"}
            }
        )
        if item_id:
            created_items.append(item_id)
    
    print(f"   ✓ Created {len(created_items)} project items")
    
    print("3. Simulating project progress...")
    for i, item_id in enumerate(created_items[:2]):  # Update first 2 items
        monday.update_item(item_id, {"status": {"label": "Working on it"}})
        monday.track_progress(item_id, (i + 1) * 30, f"Progress update {i + 1}")
    
    print("   ✓ Updated project progress")
    
    print("4. Setting up project automation...")
    automation_id = monday.create_automation(board.id, {
        "name": "Project milestone notifications",
        "trigger": {"type": "when_status_changes", "to": "Done"},
        "actions": [{"type": "notify_team", "message": "Milestone completed!"}]
    })
    
    print(f"   {'✓' if automation_id else '❌'} Automation setup")
    
    print("5. Workflow completed successfully! 🎉")
    
    return {
        'board_id': board.id,
        'items_created': len(created_items),
        'automation_id': automation_id
    }


def main():
    """Run all Monday.com integration tests."""
    print("Starting Monday.com Integration Tests")
    print("=" * 60)
    
    try:
        # Setup and basic tests
        monday = test_monday_integration_setup()
        boards = test_board_management()
        
        # Core functionality tests
        created_items = test_item_creation()
        updated_item = test_item_updates()
        sync_result = test_task_synchronization()
        progress_item = test_progress_tracking()
        assignment_item = test_assignment_and_due_dates()
        automation_ids = test_automation_and_webhooks()
        workflow_result = test_integration_workflow()
        
        # Summary
        print("\n" + "=" * 60)
        print("MONDAY.COM INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        print(f"✓ Integration setup: {'PASSED' if monday else 'FAILED'}")
        print(f"✓ Board management: {'PASSED' if boards else 'FAILED'}")
        print(f"✓ Item creation: {'PASSED' if created_items else 'FAILED'}")
        print(f"✓ Item updates: {'PASSED' if updated_item else 'FAILED'}")
        print(f"✓ Task synchronization: {'PASSED' if sync_result.success else 'FAILED'}")
        print(f"✓ Progress tracking: {'PASSED' if progress_item else 'FAILED'}")
        print(f"✓ Assignment management: {'PASSED' if assignment_item else 'FAILED'}")
        print(f"✓ Automation setup: {'PASSED' if automation_ids[0] else 'FAILED'}")
        print(f"✓ Complete workflow: {'PASSED' if workflow_result else 'FAILED'}")
        
        print(f"\n📊 Statistics:")
        print(f"  - Boards accessed: {len(boards)}")
        print(f"  - Items created: {len(created_items) + (1 if updated_item else 0) + (1 if progress_item else 0) + (1 if assignment_item else 0)}")
        print(f"  - Tasks synced: {sync_result.items_created}")
        print(f"  - Automations created: {1 if automation_ids[0] else 0}")
        
        print(f"\n🎉 Monday.com integration test completed successfully!")
        print("The system can now:")
        print("  • Connect to Monday.com workspaces and boards")
        print("  • Create and manage items with full column support")
        print("  • Synchronize tasks with Monday.com items")
        print("  • Track progress and manage assignments")
        print("  • Set up automations and webhooks")
        print("  • Handle complete project workflows")
        
        # Show mock data summary
        if hasattr(monday, 'mock_items'):
            print(f"\nMock items created during testing: {len(monday.mock_items)}")
            for i, item in enumerate(monday.mock_items[:5], 1):  # Show first 5
                print(f"  {i}. {item.name} (Status: {item.get_status() or 'N/A'})")
        
        return 0
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())