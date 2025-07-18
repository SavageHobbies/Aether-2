#!/usr/bin/env python3
"""
Unit tests for Google Calendar integration.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.integrations.google_calendar import GoogleCalendarIntegration
from core.integrations.calendar_types import (
    CalendarEvent, CalendarEventType, CalendarAuthConfig, CalendarPreferences,
    CalendarAttendee, ConflictType, CalendarConflict
)


class TestGoogleCalendarIntegration(unittest.TestCase):
    """Test cases for Google Calendar integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_config = CalendarAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        self.preferences = CalendarPreferences(
            default_event_duration_minutes=60,
            work_start_hour=9,
            work_end_hour=17
        )
        
        self.calendar = GoogleCalendarIntegration(self.auth_config, self.preferences)
    
    def test_initialization(self):
        """Test calendar integration initialization."""
        self.assertIsNotNone(self.calendar)
        self.assertEqual(self.calendar.auth_config.client_id, "test_client_id")
        self.assertEqual(self.calendar.preferences.default_event_duration_minutes, 60)
        self.assertTrue(hasattr(self.calendar, 'mock_mode'))  # Should be in mock mode
    
    def test_authentication(self):
        """Test authentication process."""
        auth_result = self.calendar.authenticate()
        self.assertTrue(auth_result)  # Should succeed in mock mode
    
    def test_event_creation(self):
        """Test creating calendar events."""
        event = CalendarEvent(
            title="Test Meeting",
            description="A test meeting",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            event_type=CalendarEventType.MEETING
        )
        
        event_id = self.calendar.create_event(event)
        
        self.assertIsNotNone(event_id)
        self.assertEqual(event.google_event_id, event_id)
        self.assertIn(event, self.calendar.mock_events)
    
    def test_event_update(self):
        """Test updating calendar events."""
        # Create an event first
        event = CalendarEvent(
            title="Original Title",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )
        
        event_id = self.calendar.create_event(event)
        self.assertIsNotNone(event_id)
        
        # Update the event
        event.title = "Updated Title"
        event.description = "Updated description"
        
        update_result = self.calendar.update_event(event)
        self.assertTrue(update_result)
        
        # Verify the update
        updated_event = next(
            (e for e in self.calendar.mock_events if e.google_event_id == event_id),
            None
        )
        self.assertIsNotNone(updated_event)
        self.assertEqual(updated_event.title, "Updated Title")
    
    def test_event_deletion(self):
        """Test deleting calendar events."""
        # Create an event first
        event = CalendarEvent(
            title="Event to Delete",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )
        
        event_id = self.calendar.create_event(event)
        initial_count = len(self.calendar.mock_events)
        
        # Delete the event
        delete_result = self.calendar.delete_event(event_id)
        self.assertTrue(delete_result)
        
        # Verify deletion
        self.assertEqual(len(self.calendar.mock_events), initial_count - 1)
        deleted_event = next(
            (e for e in self.calendar.mock_events if e.google_event_id == event_id),
            None
        )
        self.assertIsNone(deleted_event)
    
    def test_get_events(self):
        """Test retrieving events within a time range."""
        # Create test events
        base_time = datetime.now()
        
        event1 = CalendarEvent(
            title="Event 1",
            start_time=base_time + timedelta(hours=1),
            end_time=base_time + timedelta(hours=2)
        )
        
        event2 = CalendarEvent(
            title="Event 2", 
            start_time=base_time + timedelta(hours=3),
            end_time=base_time + timedelta(hours=4)
        )
        
        event3 = CalendarEvent(
            title="Event 3",
            start_time=base_time + timedelta(days=1),
            end_time=base_time + timedelta(days=1, hours=1)
        )
        
        self.calendar.create_event(event1)
        self.calendar.create_event(event2)
        self.calendar.create_event(event3)
        
        # Get events for today
        today_start = base_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        events = self.calendar.get_events(today_start, today_end)
        
        # Should get event1 and event2, but not event3
        self.assertEqual(len(events), 2)
        event_titles = [e.title for e in events]
        self.assertIn("Event 1", event_titles)
        self.assertIn("Event 2", event_titles)
        self.assertNotIn("Event 3", event_titles)
    
    def test_conflict_detection(self):
        """Test conflict detection between events."""
        base_time = datetime.now() + timedelta(hours=1)
        
        # Create existing event
        existing_event = CalendarEvent(
            title="Existing Meeting",
            start_time=base_time,
            end_time=base_time + timedelta(hours=1)
        )
        
        # Create overlapping event
        overlapping_event = CalendarEvent(
            title="Overlapping Meeting",
            start_time=base_time + timedelta(minutes=30),
            end_time=base_time + timedelta(hours=1, minutes=30)
        )
        
        # Create back-to-back event
        back_to_back_event = CalendarEvent(
            title="Back-to-back Meeting",
            start_time=base_time + timedelta(hours=1),
            end_time=base_time + timedelta(hours=2)
        )
        
        # Test overlap detection
        conflicts = self.calendar.detect_conflicts(overlapping_event, [existing_event])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, ConflictType.OVERLAP)
        
        # Test back-to-back detection
        conflicts = self.calendar.detect_conflicts(back_to_back_event, [existing_event])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, ConflictType.BACK_TO_BACK)
    
    def test_alternative_time_suggestions(self):
        """Test suggesting alternative times for events."""
        # Create an event that needs alternative times
        event = CalendarEvent(
            title="Meeting needing alternatives",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )
        
        suggestions = self.calendar.suggest_alternative_times(event, 60)
        
        # Should get some suggestions
        self.assertGreater(len(suggestions), 0)
        self.assertLessEqual(len(suggestions), 5)  # Limited to 5 suggestions
        
        # Each suggestion should be a tuple of (start_time, end_time)
        for start, end in suggestions:
            self.assertIsInstance(start, datetime)
            self.assertIsInstance(end, datetime)
            self.assertEqual((end - start).total_seconds() / 60, 60)  # 60 minutes duration
    
    def test_task_to_calendar_sync(self):
        """Test syncing tasks with calendar events."""
        # Create mock tasks
        class MockTask:
            def __init__(self, id, title, description, due_date):
                self.id = id
                self.title = title
                self.description = description
                self.due_date = due_date
                self.status = type('Status', (), {'value': 'todo'})()
                self.estimated_duration_minutes = 90
        
        tasks = [
            MockTask("task_1", "Task 1", "Description 1", datetime.now() + timedelta(days=1)),
            MockTask("task_2", "Task 2", "Description 2", datetime.now() + timedelta(days=2))
        ]
        
        initial_event_count = len(self.calendar.mock_events)
        
        # Sync tasks
        sync_result = self.calendar.sync_with_tasks(tasks)
        
        self.assertTrue(sync_result.success)
        self.assertEqual(sync_result.events_created, 2)
        self.assertEqual(sync_result.events_updated, 0)
        self.assertEqual(len(self.calendar.mock_events), initial_event_count + 2)
        
        # Verify task events were created correctly
        task_events = [e for e in self.calendar.mock_events if e.event_type == CalendarEventType.TASK]
        self.assertEqual(len(task_events), 2)
        
        for event in task_events:
            self.assertTrue(event.title.startswith("Task: "))
            self.assertIsNotNone(event.source_task_id)


class TestCalendarTypes(unittest.TestCase):
    """Test cases for calendar data types."""
    
    def test_calendar_event_creation(self):
        """Test creating calendar events."""
        event = CalendarEvent(
            title="Test Event",
            description="Test Description",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1)
        )
        
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.description, "Test Description")
        self.assertEqual(event.duration_minutes, 60)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)
    
    def test_event_overlap_detection(self):
        """Test event overlap detection."""
        base_time = datetime.now()
        
        event1 = CalendarEvent(
            title="Event 1",
            start_time=base_time,
            end_time=base_time + timedelta(hours=1)
        )
        
        event2 = CalendarEvent(
            title="Event 2",
            start_time=base_time + timedelta(minutes=30),
            end_time=base_time + timedelta(hours=1, minutes=30)
        )
        
        event3 = CalendarEvent(
            title="Event 3",
            start_time=base_time + timedelta(hours=2),
            end_time=base_time + timedelta(hours=3)
        )
        
        # Test overlapping events
        self.assertTrue(event1.overlaps_with(event2))
        self.assertTrue(event2.overlaps_with(event1))
        
        # Test non-overlapping events
        self.assertFalse(event1.overlaps_with(event3))
        self.assertFalse(event3.overlaps_with(event1))
    
    def test_calendar_attendee(self):
        """Test calendar attendee creation."""
        attendee = CalendarAttendee(
            email="test@example.com",
            name="Test User",
            response_status="accepted",
            optional=False
        )
        
        self.assertEqual(attendee.email, "test@example.com")
        self.assertEqual(attendee.name, "Test User")
        self.assertEqual(attendee.response_status, "accepted")
        self.assertFalse(attendee.optional)
    
    def test_calendar_preferences(self):
        """Test calendar preferences."""
        preferences = CalendarPreferences(
            default_event_duration_minutes=90,
            work_start_hour=8,
            work_end_hour=18,
            auto_create_events_from_tasks=True
        )
        
        self.assertEqual(preferences.default_event_duration_minutes, 90)
        self.assertEqual(preferences.work_start_hour, 8)
        self.assertEqual(preferences.work_end_hour, 18)
        self.assertTrue(preferences.auto_create_events_from_tasks)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)