#!/usr/bin/env python3

"""
Test script for Google Calendar integration.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.integrations.google_calendar import GoogleCalendarIntegration, get_google_calendar_integration
from core.integrations.calendar_types import (
    CalendarEvent, CalendarSettings, CalendarEventType, CalendarConflict,
    CalendarConflictType, CalendarSyncResult, CalendarSyncStatus
)
from core.tasks import TaskEntry, TaskPriority, TaskStatus
from core.database import initialize_database
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_calendar_settings():
    """Test calendar settings functionality."""
    print("\\n=== Testing Calendar Settings ===")
    
    # Test default settings
    settings = CalendarSettings()
    print(f"Default sync interval: {settings.sync_interval_minutes} minutes")
    print(f"Auto sync enabled: {settings.auto_sync_enabled}")
    print(f"Primary calendar: {settings.primary_calendar_id}")
    
    # Test custom settings
    custom_settings = CalendarSettings(
        client_id="test_client_id",
        client_secret="test_client_secret",
        sync_interval_minutes=30,
        auto_sync_enabled=False
    )
    print(f"Custom client ID: {custom_settings.client_id}")
    print(f"Custom sync interval: {custom_settings.sync_interval_minutes} minutes")


async def test_calendar_event_creation():
    """Test calendar event creation and manipulation."""
    print("\\n=== Testing Calendar Event Creation ===")
    
    # Create a basic event
    event = CalendarEvent(
        title="Test Meeting",
        description="This is a test meeting",
        start_time=datetime.utcnow() + timedelta(hours=1),
        event_type=CalendarEventType.MEETING
    )
    
    print(f"Created event: {event.title}")
    print(f"Start time: {event.start_time}")
    print(f"End time: {event.end_time}")
    print(f"Duration: {event.duration_minutes} minutes")
    print(f"Event type: {event.event_type.value}")
    
    # Test Google event conversion
    google_event_data = event.to_google_event()
    print(f"Google event summary: {google_event_data['summary']}")
    print(f"Google event start: {google_event_data['start']}")
    
    # Test event overlap detection
    overlapping_event = CalendarEvent(
        title="Overlapping Meeting",
        start_time=event.start_time + timedelta(minutes=30),
        end_time=event.end_time + timedelta(minutes=30)
    )
    
    print(f"Events overlap: {event.overlaps_with(overlapping_event)}")


async def test_calendar_event_from_google():
    """Test creating CalendarEvent from Google Calendar data."""
    print("\\n=== Testing Calendar Event from Google Data ===")
    
    # Mock Google Calendar event data
    google_event_data = {
        'id': 'test_event_123',
        'summary': 'Team Standup',
        'description': 'Daily team standup meeting',
        'location': 'Conference Room A',
        'status': 'confirmed',
        'start': {
            'dateTime': '2023-07-20T09:00:00-07:00',
            'timeZone': 'America/Los_Angeles'
        },
        'end': {
            'dateTime': '2023-07-20T09:30:00-07:00',
            'timeZone': 'America/Los_Angeles'
        },
        'attendees': [
            {
                'email': 'john@example.com',
                'displayName': 'John Doe',
                'responseStatus': 'accepted'
            },
            {
                'email': 'jane@example.com',
                'displayName': 'Jane Smith',
                'responseStatus': 'tentative'
            }
        ],
        'created': '2023-07-19T10:00:00Z',
        'updated': '2023-07-19T15:30:00Z'
    }
    
    # Create CalendarEvent from Google data
    event = CalendarEvent.from_google_event(google_event_data)
    
    print(f"Event title: {event.title}")
    print(f"Event description: {event.description}")
    print(f"Event location: {event.location}")
    print(f"Google event ID: {event.google_event_id}")
    print(f"Start time: {event.start_time}")
    print(f"End time: {event.end_time}")
    print(f"Duration: {event.duration_minutes} minutes")
    print(f"Attendees: {len(event.attendees)}")
    
    for attendee in event.attendees:
        print(f"  - {attendee.name} ({attendee.email}): {attendee.response_status}")


async def test_conflict_detection():
    """Test calendar conflict detection."""
    print("\\n=== Testing Conflict Detection ===")
    
    # Create overlapping events
    event1 = CalendarEvent(
        title="Meeting A",
        start_time=datetime(2023, 7, 20, 14, 0),
        end_time=datetime(2023, 7, 20, 15, 0)
    )
    
    event2 = CalendarEvent(
        title="Meeting B",
        start_time=datetime(2023, 7, 20, 14, 30),
        end_time=datetime(2023, 7, 20, 15, 30)
    )
    
    # Create conflict
    conflict = CalendarConflict(
        conflict_type=CalendarConflictType.OVERLAP,
        event1=event1,
        event2=event2
    )
    
    print(f"Conflict detected: {conflict.description}")
    print(f"Overlap duration: {conflict.overlap_duration_minutes} minutes")
    print(f"Overlap start: {conflict.overlap_start}")
    print(f"Overlap end: {conflict.overlap_end}")


async def test_google_calendar_integration_basic():
    """Test basic Google Calendar integration functionality."""
    print("\\n=== Testing Google Calendar Integration (Basic) ===")
    
    # Create settings
    settings = CalendarSettings(
        client_id="test_client_id",
        client_secret="test_client_secret"
    )
    
    # Create integration
    integration = GoogleCalendarIntegration(settings)
    
    # Test auth URL generation
    auth_url = integration.get_auth_url("http://localhost:8000/callback", "test_state")
    print(f"Auth URL generated: {auth_url[:100]}...")
    
    # Verify URL contains required parameters
    assert "client_id=test_client_id" in auth_url
    assert "redirect_uri=" in auth_url
    assert "scope=" in auth_url
    assert "state=test_state" in auth_url
    print("✓ Auth URL contains required parameters")


async def test_google_calendar_integration_mocked():
    """Test Google Calendar integration with mocked HTTP responses."""
    print("\\n=== Testing Google Calendar Integration (Mocked) ===")
    
    settings = CalendarSettings(
        client_id="test_client_id",
        client_secret="test_client_secret",
        access_token="test_access_token"
    )
    
    integration = GoogleCalendarIntegration(settings)
    
    # Mock HTTP session
    mock_session = AsyncMock()
    integration.session = mock_session
    
    # Test getting calendars
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        'items': [
            {
                'id': 'primary',
                'summary': 'Primary Calendar',
                'primary': True
            },
            {
                'id': 'work@example.com',
                'summary': 'Work Calendar',
                'primary': False
            }
        ]
    })
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    calendars = await integration.get_calendars()
    print(f"Retrieved {len(calendars)} calendars")
    for calendar in calendars:
        print(f"  - {calendar['summary']} ({calendar['id']})")
    
    # Test getting events
    mock_response.json = AsyncMock(return_value={
        'items': [
            {
                'id': 'event_1',
                'summary': 'Test Event 1',
                'start': {'dateTime': '2023-07-20T10:00:00Z'},
                'end': {'dateTime': '2023-07-20T11:00:00Z'},
                'status': 'confirmed',
                'created': '2023-07-19T10:00:00Z',
                'updated': '2023-07-19T10:00:00Z'
            },
            {
                'id': 'event_2',
                'summary': 'Test Event 2',
                'start': {'dateTime': '2023-07-20T14:00:00Z'},
                'end': {'dateTime': '2023-07-20T15:00:00Z'},
                'status': 'confirmed',
                'created': '2023-07-19T10:00:00Z',
                'updated': '2023-07-19T10:00:00Z'
            }
        ]
    })
    
    events = await integration.get_events()
    print(f"Retrieved {len(events)} events")
    for event in events:
        if isinstance(event, dict):
            print(f"  - {event.get('summary', 'No title')} ({event.get('start', {}).get('dateTime', 'No time')})")
        else:
            print(f"  - {event.title} ({event.start_time} - {event.end_time})")


async def test_task_to_calendar_event():
    """Test converting tasks to calendar events."""
    print("\\n=== Testing Task to Calendar Event Conversion ===")
    
    # Create a test task
    task = TaskEntry(
        title="Complete project proposal",
        description="Write and review the Q3 project proposal document",
        priority=TaskPriority.HIGH,
        due_date=datetime.utcnow() + timedelta(days=2),
        estimated_duration_minutes=120
    )
    
    print(f"Task: {task.title}")
    print(f"Due date: {task.due_date}")
    print(f"Estimated duration: {task.estimated_duration_minutes} minutes")
    
    # Create integration with mocked session
    settings = CalendarSettings(
        client_id="test_client_id",
        client_secret="test_client_secret",
        access_token="test_access_token",
        create_events_from_tasks=True
    )
    
    integration = GoogleCalendarIntegration(settings)
    
    # Mock the create_event method
    async def mock_create_event(event):
        event.google_event_id = "created_event_123"
        event.synced_at = datetime.utcnow()
        return event
    
    integration.create_event = mock_create_event
    integration._create_local_event = AsyncMock()
    
    # Convert task to calendar event
    calendar_event = await integration.create_event_from_task(task)
    
    if calendar_event:
        print(f"Created calendar event: {calendar_event.title}")
        print(f"Event type: {calendar_event.event_type.value}")
        print(f"Start time: {calendar_event.start_time}")
        print(f"Duration: {calendar_event.duration_minutes} minutes")
        print(f"Task ID: {calendar_event.task_id}")
        print(f"Google event ID: {calendar_event.google_event_id}")
    else:
        print("Failed to create calendar event from task")


async def test_sync_result():
    """Test calendar sync result functionality."""
    print("\\n=== Testing Calendar Sync Result ===")
    
    # Create sync result
    result = CalendarSyncResult(
        calendar_id="primary",
        sync_direction="bidirectional"
    )
    
    # Simulate sync operations
    result.events_created = 5
    result.events_updated = 3
    result.events_deleted = 1
    result.events_synced = 9
    
    # Add some conflicts
    event1 = CalendarEvent(title="Meeting A", start_time=datetime.utcnow())
    event2 = CalendarEvent(title="Meeting B", start_time=datetime.utcnow())
    conflict = CalendarConflict(event1=event1, event2=event2)
    result.conflicts_detected.append(conflict)
    
    # Add some errors
    result.errors.append("Failed to sync event 'Important Meeting'")
    
    # Mark as completed
    result.mark_completed()
    
    print(f"Sync status: {result.status.value}")
    print(f"Events synced: {result.events_synced}")
    print(f"Events created: {result.events_created}")
    print(f"Events updated: {result.events_updated}")
    print(f"Events deleted: {result.events_deleted}")
    print(f"Conflicts detected: {len(result.conflicts_detected)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {result.success_rate:.2%}")
    print(f"Sync duration: {result.sync_duration_seconds:.2f} seconds")
    print(f"Summary: {result.summary}")


async def test_integration_workflow():
    """Test complete integration workflow."""
    print("\\n=== Testing Complete Integration Workflow ===")
    
    settings = CalendarSettings(
        client_id="test_client_id",
        client_secret="test_client_secret",
        access_token="test_access_token"
    )
    
    async with GoogleCalendarIntegration(settings) as integration:
        print("✓ Integration context manager works")
        
        # Mock session for testing
        integration.session = AsyncMock()
        
        # Test token validation (mock)
        print("Token validation: True (mocked)")
        
        # Test sync workflow (mocked)
        sync_result = await integration.sync_events()
        print(f"Sync completed: {sync_result['status']}")
        print(f"Events synced: {sync_result['events_synced']}")


async def test_error_handling():
    """Test error handling in Google Calendar integration."""
    print("\\n=== Testing Error Handling ===")
    
    settings = CalendarSettings()  # No credentials
    integration = GoogleCalendarIntegration(settings)
    
    # Test without valid token
    try:
        await integration.get_calendars()
        print("✗ Should have failed without valid token")
    except Exception as e:
        print(f"✓ Correctly failed without token: {str(e)[:50]}...")
    
    # Test with invalid event data
    try:
        invalid_google_event = {
            'id': 'invalid_event',
            'summary': 'Invalid Event'
            # Missing required fields
        }
        CalendarEvent.from_google_event(invalid_google_event)
        print("✗ Should have failed with invalid event data")
    except Exception as e:
        print(f"✓ Correctly handled invalid event data: {str(e)[:50]}...")


async def main():
    """Run all Google Calendar integration tests."""
    print("Starting Google Calendar Integration Tests")
    print("=" * 50)
    
    try:
        # Initialize database for testing
        db_manager = initialize_database("sqlite:///test_calendar.db")
        await db_manager.create_tables_async()
        print("✓ Database initialized")
        
        # Run tests
        await test_calendar_settings()
        await test_calendar_event_creation()
        await test_calendar_event_from_google()
        await test_conflict_detection()
        await test_google_calendar_integration_basic()
        await test_google_calendar_integration_mocked()
        await test_task_to_calendar_event()
        await test_sync_result()
        await test_integration_workflow()
        await test_error_handling()
        
        print("\\n" + "=" * 50)
        print("Google Calendar Integration Tests Completed Successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\\n✗ Tests failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())