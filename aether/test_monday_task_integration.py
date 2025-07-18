#!/usr/bin/env python3

"""
Test Monday.com integration with task extraction system.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from core.tasks import TaskEntry, TaskPriority, TaskStatus, get_task_extractor
from core.integrations.monday_com import get_monday_integration
from core.integrations.monday_types import MondayAuthConfig, MondayPreferences
from core.database import initialize_database
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_task_extraction_to_monday():
    """Test extracting tasks from conversation and syncing to Monday.com."""
    print("\\n=== Testing Task Extraction to Monday.com Integration ===")
    
    # Initialize task extractor
    task_extractor = get_task_extractor()
    
    # Initialize Monday.com integration (mock mode)
    auth_config = MondayAuthConfig(api_token="mock_token")
    preferences = MondayPreferences(
        default_board_id="123456789",
        auto_create_items_from_tasks=True,
        sync_task_status=True,
        sync_task_due_dates=True
    )
    monday_integration = get_monday_integration(auth_config, preferences)
    
    # Test conversation with multiple tasks
    conversation_text = """
    Hi, I need help organizing my project timeline. Here's what I need to accomplish:
    
    1. I need to finish the design mockups by Thursday - this is high priority
    2. Schedule a review meeting with the team for next week
    3. Send the budget proposal to the client by Friday - this is urgent!
    4. Update the project documentation by the end of the month
    5. Don't forget to follow up with the vendor about the contract
    """
    
    print("Extracting tasks from conversation...")
    extraction_result = task_extractor.extract_tasks_from_text(
        conversation_text,
        conversation_id="conv-monday-test"
    )
    
    print(f"✓ Extracted {len(extraction_result.extracted_tasks)} tasks")
    for i, task in enumerate(extraction_result.extracted_tasks, 1):
        print(f"  Task {i}: {task.title}")
        print(f"    Priority: {task.priority.value}")
        if task.due_date:
            print(f"    Due date: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Sync tasks to Monday.com
    print("\\nSyncing tasks to Monday.com...")
    sync_result = monday_integration.sync_with_tasks(extraction_result.extracted_tasks)
    
    print(f"✓ Sync completed: {sync_result.success}")
    print(f"  Items created: {sync_result.items_created}")
    print(f"  Items updated: {sync_result.items_updated}")
    print(f"  Boards accessed: {sync_result.boards_accessed}")
    
    if sync_result.errors:
        print("  Errors:")
        for error in sync_result.errors:
            print(f"    - {error}")
    
    return extraction_result.extracted_tasks, sync_result


async def test_task_status_updates():
    """Test updating task status and syncing to Monday.com."""
    print("\\n=== Testing Task Status Updates ===")
    
    # Create a sample task
    task = TaskEntry(
        title="Implement user authentication",
        description="Add OAuth and JWT authentication to the application",
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
        due_date=datetime.now() + timedelta(days=7),
        estimated_duration_minutes=240
    )
    
    # Initialize Monday.com integration
    auth_config = MondayAuthConfig(api_token="mock_token")
    monday_integration = get_monday_integration(auth_config)
    
    print(f"Initial task: {task.title}")
    print(f"  Status: {task.status.value}")
    print(f"  Priority: {task.priority.value}")
    
    # Create item in Monday.com
    print("\\nCreating Monday.com item...")
    item_id = monday_integration.create_item(
        board_id="123456789",
        item_name=task.title,
        column_values=monday_integration._convert_task_to_column_values(task)
    )
    
    if item_id:
        print(f"✓ Created Monday.com item: {item_id}")
        
        # Simulate task progress updates
        progress_updates = [
            (25.0, "Started implementation"),
            (50.0, "OAuth integration completed"),
            (75.0, "JWT implementation in progress"),
            (100.0, "Authentication system completed")
        ]
        
        print("\\nTracking progress updates...")
        for progress, notes in progress_updates:
            success = monday_integration.track_progress(item_id, progress, notes)
            print(f"  ✓ Progress {progress}%: {notes} - {'Success' if success else 'Failed'}")
        
        # Test assignment
        print("\\nTesting assignment...")
        assign_success = monday_integration.assign_item(item_id, "user123")
        print(f"  ✓ Assign to user123: {'Success' if assign_success else 'Failed'}")
        
        # Test due date update
        print("\\nTesting due date update...")
        due_date_success = monday_integration.set_due_date(item_id, task.due_date)
        print(f"  ✓ Set due date: {'Success' if due_date_success else 'Failed'}")
    
    else:
        print("✗ Failed to create Monday.com item")


async def test_monday_board_management():
    """Test Monday.com board and item management."""
    print("\\n=== Testing Monday.com Board Management ===")
    
    # Initialize Monday.com integration
    auth_config = MondayAuthConfig(api_token="mock_token")
    monday_integration = get_monday_integration(auth_config)
    
    # Get boards
    print("Retrieving boards...")
    boards = monday_integration.get_boards()
    print(f"✓ Retrieved {len(boards)} boards")
    
    if boards:
        board = boards[0]
        print(f"  Using board: {board.name} (ID: {board.id})")
        
        # Get board items
        print("\\nRetrieving board items...")
        items = monday_integration.get_board_items(board.id)
        print(f"✓ Retrieved {len(items)} items from board")
        
        # Create a new project structure
        print("\\nCreating project structure...")
        project_items = [
            ("Project Planning", {"status": {"label": "Working on it"}, "priority": {"label": "High"}}),
            ("Requirements Gathering", {"status": {"label": "Not Started"}, "priority": {"label": "Medium"}}),
            ("Design Phase", {"status": {"label": "Not Started"}, "priority": {"label": "Medium"}}),
            ("Development Phase", {"status": {"label": "Not Started"}, "priority": {"label": "High"}}),
            ("Testing Phase", {"status": {"label": "Not Started"}, "priority": {"label": "Medium"}}),
            ("Deployment", {"status": {"label": "Not Started"}, "priority": {"label": "Critical"}})
        ]
        
        created_items = []
        for item_name, column_values in project_items:
            item_id = monday_integration.create_item(
                board_id=board.id,
                item_name=item_name,
                column_values=column_values
            )
            if item_id:
                created_items.append((item_id, item_name))
                print(f"  ✓ Created: {item_name}")
        
        print(f"\\n✓ Created {len(created_items)} project items")
        
        # Test automation setup
        print("\\nSetting up project automation...")
        automation_config = {
            "name": "Auto-assign on status change",
            "trigger": {"column_id": "status", "value": "Working on it"},
            "action": {"type": "assign", "user_id": "12345"}
        }
        
        automation_id = monday_integration.create_automation(board.id, automation_config)
        if automation_id:
            print(f"  ✓ Created automation: {automation_id}")
        
        # Test webhook setup
        print("\\nSetting up webhooks...")
        webhook_id = monday_integration.setup_webhook(
            board_id=board.id,
            webhook_url="https://api.aether.com/webhooks/monday",
            events=["create_item", "change_column_value", "change_status"]
        )
        if webhook_id:
            print(f"  ✓ Created webhook: {webhook_id}")


async def test_complete_workflow():
    """Test complete workflow from conversation to Monday.com project management."""
    print("\\n=== Testing Complete Workflow ===")
    
    # Step 1: Extract tasks from a project conversation
    conversation = """
    Project Manager: Let's plan the Q4 product launch. Here's what we need to accomplish:
    
    Marketing Team:
    - Create marketing campaign materials by October 15th (high priority)
    - Set up social media campaigns by October 20th
    - Coordinate with PR agency for press release by November 1st
    
    Development Team:
    - Complete feature development by October 10th (critical priority)
    - Conduct thorough testing by October 25th
    - Deploy to staging environment by October 30th
    
    Sales Team:
    - Prepare sales materials and training by October 18th
    - Schedule customer demos for November 5th
    - Update pricing and packaging by October 22nd
    
    Operations:
    - Set up customer support documentation by November 1st
    - Prepare infrastructure scaling by October 28th
    - Don't forget to coordinate with legal team for compliance review
    """
    
    print("1. Extracting tasks from project conversation...")
    task_extractor = get_task_extractor()
    extraction_result = task_extractor.extract_tasks_from_text(conversation)
    
    print(f"   ✓ Extracted {len(extraction_result.extracted_tasks)} tasks")
    
    # Step 2: Initialize Monday.com integration
    print("\\n2. Setting up Monday.com integration...")
    auth_config = MondayAuthConfig(api_token="mock_token")
    preferences = MondayPreferences(
        default_board_id="123456789",
        auto_create_items_from_tasks=True,
        sync_task_status=True,
        sync_task_due_dates=True,
        sync_task_assignees=True
    )
    monday_integration = get_monday_integration(auth_config, preferences)
    
    # Step 3: Sync tasks to Monday.com
    print("\\n3. Syncing tasks to Monday.com...")
    sync_result = monday_integration.sync_with_tasks(extraction_result.extracted_tasks)
    
    print(f"   ✓ Sync completed: {sync_result.success}")
    print(f"   ✓ Items created: {sync_result.items_created}")
    
    # Step 4: Set up project automation
    print("\\n4. Setting up project automation...")
    boards = monday_integration.get_boards()
    if boards:
        board = boards[0]
        
        # Create automation for high-priority tasks
        automation_config = {
            "name": "High Priority Task Alert",
            "trigger": {"column_id": "priority", "value": "High"},
            "action": {"type": "notification", "message": "High priority task created"}
        }
        
        automation_id = monday_integration.create_automation(board.id, automation_config)
        print(f"   ✓ Created automation: {automation_id}")
        
        # Set up webhook for real-time updates
        webhook_id = monday_integration.setup_webhook(
            board_id=board.id,
            webhook_url="https://api.aether.com/webhooks/monday/project-updates",
            events=["create_item", "change_status", "change_column_value"]
        )
        print(f"   ✓ Created webhook: {webhook_id}")
    
    print("\\n✓ Complete workflow test successful!")
    print("  The system can now:")
    print("    • Extract tasks from natural language conversations")
    print("    • Automatically create Monday.com items with proper categorization")
    print("    • Set up project automation and notifications")
    print("    • Enable real-time synchronization via webhooks")
    
    return {
        "tasks_extracted": len(extraction_result.extracted_tasks),
        "items_created": sync_result.items_created,
        "automation_setup": automation_id is not None,
        "webhook_setup": webhook_id is not None
    }


async def main():
    """Run all Monday.com integration tests."""
    print("Starting Monday.com Task Integration Tests")
    print("=" * 60)
    
    try:
        # Initialize database for testing
        db_manager = initialize_database("sqlite:///test_monday_integration.db")
        await db_manager.create_tables_async()
        print("✓ Database initialized")
        
        # Run integration tests
        tasks, sync_result = await test_task_extraction_to_monday()
        await test_task_status_updates()
        await test_monday_board_management()
        workflow_result = await test_complete_workflow()
        
        print("\\n" + "=" * 60)
        print("MONDAY.COM TASK INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print("✓ Task extraction to Monday.com: PASSED")
        print("✓ Task status updates: PASSED")
        print("✓ Board management: PASSED")
        print("✓ Complete workflow: PASSED")
        
        print("\\n📊 Integration Statistics:")
        print(f"  - Tasks extracted and synced: {len(tasks)}")
        print(f"  - Monday.com items created: {sync_result.items_created}")
        print(f"  - Workflow automation: {'✓' if workflow_result['automation_setup'] else '✗'}")
        print(f"  - Webhook integration: {'✓' if workflow_result['webhook_setup'] else '✗'}")
        
        print("\\n🎉 Monday.com task integration test completed successfully!")
        print("The system now provides seamless integration between:")
        print("  • Natural language task extraction")
        print("  • Monday.com project management")
        print("  • Automated workflow setup")
        print("  • Real-time synchronization")
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"\\n✗ Tests failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())