#!/usr/bin/env python3
"""
Unit tests for notification and reminder system.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import time

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.notifications.notification_manager import NotificationManager
from core.notifications.reminder_engine import ReminderEngine, MonitoredItem
from core.notifications.notification_types import (
    Notification, NotificationType, NotificationPriority, NotificationChannel,
    ReminderRule, ReminderInterval, NotificationPreferences, NotificationStatus
)


class TestNotificationTypes(unittest.TestCase):
    """Test cases for notification data types."""
    
    def test_notification_creation(self):
        """Test creating notifications."""
        notification = Notification(
            title="Test Notification",
            message="This is a test message",
            notification_type=NotificationType.TASK_REMINDER,
            priority=NotificationPriority.HIGH
        )
        
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.message, "This is a test message")
        self.assertEqual(notification.notification_type, NotificationType.TASK_REMINDER)
        self.assertEqual(notification.priority, NotificationPriority.HIGH)
        self.assertIsNotNone(notification.id)
        self.assertIsNotNone(notification.created_at)
        self.assertEqual(notification.status, NotificationStatus.PENDING)
    
    def test_notification_expiration(self):
        """Test notification expiration logic."""
        # Non-expired notification
        notification = Notification(
            title="Test",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.assertFalse(notification.is_expired())
        
        # Expired notification
        expired_notification = Notification(
            title="Expired",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        self.assertTrue(expired_notification.is_expired())
    
    def test_notification_scheduling(self):
        """Test notification scheduling logic."""
        # Should send now
        notification = Notification(title="Now")
        self.assertTrue(notification.should_send_now())
        
        # Scheduled for future
        future_notification = Notification(
            title="Future",
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        self.assertFalse(future_notification.should_send_now())
        
        # Scheduled for past
        past_notification = Notification(
            title="Past",
            scheduled_time=datetime.utcnow() - timedelta(hours=1)
        )
        self.assertTrue(past_notification.should_send_now())
    
    def test_notification_actions(self):
        """Test notification actions."""
        notification = Notification(title="Test")
        
        notification.add_action("test", "Test Action", "callback", {"key": "value"}, True)
        
        self.assertEqual(len(notification.actions), 1)
        action = notification.actions[0]
        self.assertEqual(action.id, "test")
        self.assertEqual(action.label, "Test Action")
        self.assertEqual(action.action_type, "callback")
        self.assertEqual(action.action_data["key"], "value")
        self.assertTrue(action.is_primary)
    
    def test_reminder_rule(self):
        """Test reminder rule functionality."""
        rule = ReminderRule(
            name="Test Rule",
            applies_to_types=["task"],
            applies_to_priorities=[NotificationPriority.HIGH],
            intervals=[ReminderInterval.HOUR_1, ReminderInterval.DAY_1]
        )
        
        # Should apply to high priority task
        self.assertTrue(rule.should_remind_for_item("task", NotificationPriority.HIGH, []))
        
        # Should not apply to low priority task
        self.assertFalse(rule.should_remind_for_item("task", NotificationPriority.LOW, []))
        
        # Should not apply to meeting
        self.assertFalse(rule.should_remind_for_item("meeting", NotificationPriority.HIGH, []))
    
    def test_reminder_timing(self):
        """Test reminder timing calculations."""
        rule = ReminderRule(
            intervals=[ReminderInterval.HOUR_1, ReminderInterval.DAY_1]
        )
        
        due_time = datetime.utcnow() + timedelta(hours=25)  # Due in 25 hours
        reminder_times = rule.get_reminder_times(due_time)
        
        # Should get 2 reminder times (1 hour and 1 day before)
        self.assertEqual(len(reminder_times), 2)
        
        # Times should be in the future
        for reminder_time in reminder_times:
            self.assertGreater(reminder_time, datetime.utcnow())
    
    def test_notification_preferences(self):
        """Test notification preferences."""
        preferences = NotificationPreferences(
            minimum_priority=NotificationPriority.HIGH,
            quiet_hours_enabled=True,
            quiet_hours_start=22,
            quiet_hours_end=8
        )
        
        # High priority notification should be allowed
        high_notification = Notification(
            title="High Priority",
            priority=NotificationPriority.HIGH
        )
        self.assertTrue(preferences.should_send_notification(high_notification))
        
        # Low priority notification should be blocked
        low_notification = Notification(
            title="Low Priority",
            priority=NotificationPriority.LOW
        )
        self.assertFalse(preferences.should_send_notification(low_notification))


class TestNotificationManager(unittest.TestCase):
    """Test cases for notification manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preferences = NotificationPreferences(
            desktop_notifications=True,
            mobile_push_notifications=False,
            email_notifications=False
        )
        self.manager = NotificationManager(self.preferences)
    
    def test_initialization(self):
        """Test notification manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertGreater(len(self.manager.channels), 0)
        self.assertEqual(self.manager.preferences, self.preferences)
    
    def test_send_notification(self):
        """Test sending notifications."""
        notification = Notification(
            title="Test Notification",
            message="Test message",
            channels=[NotificationChannel.IN_APP]
        )
        
        success = self.manager.send_notification(notification)
        self.assertTrue(success)
        self.assertEqual(notification.status, NotificationStatus.SENT)
        self.assertIsNotNone(notification.sent_at)
    
    def test_send_immediate_notification(self):
        """Test sending immediate notifications."""
        success = self.manager.send_immediate_notification(
            "Quick Test",
            "This is a quick test",
            NotificationType.SYSTEM_ALERT,
            NotificationPriority.MEDIUM
        )
        self.assertTrue(success)
    
    def test_notification_filtering(self):
        """Test notification filtering by preferences."""
        # Create notification below minimum priority
        low_priority_notification = Notification(
            title="Low Priority",
            priority=NotificationPriority.LOW,
            channels=[NotificationChannel.IN_APP]
        )
        
        # Should be filtered out if minimum priority is MEDIUM
        self.manager.preferences.minimum_priority = NotificationPriority.MEDIUM
        success = self.manager.send_notification(low_priority_notification)
        self.assertFalse(success)
    
    def test_notification_history(self):
        """Test notification history tracking."""
        # Send a notification
        notification = Notification(
            title="History Test",
            channels=[NotificationChannel.IN_APP]
        )
        self.manager.send_notification(notification)
        
        # Check history
        history = self.manager.get_notification_history(1)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[-1].title, "History Test")
    
    def test_notification_stats(self):
        """Test notification statistics."""
        initial_stats = self.manager.get_stats()
        initial_sent = initial_stats.total_sent
        
        # Send a notification
        notification = Notification(
            title="Stats Test",
            channels=[NotificationChannel.IN_APP]
        )
        self.manager.send_notification(notification)
        
        # Check updated stats
        updated_stats = self.manager.get_stats()
        self.assertEqual(updated_stats.total_sent, initial_sent + 1)
    
    def test_mark_notification_read(self):
        """Test marking notifications as read."""
        notification = Notification(
            title="Read Test",
            channels=[NotificationChannel.IN_APP]
        )
        self.manager.send_notification(notification)
        
        # Mark as read
        self.manager.mark_notification_read(notification.id)
        
        # Check status
        history = self.manager.get_notification_history(1)
        read_notification = next((n for n in history if n.id == notification.id), None)
        self.assertIsNotNone(read_notification)
        self.assertEqual(read_notification.status, NotificationStatus.READ)
        self.assertIsNotNone(read_notification.read_at)


class TestReminderEngine(unittest.TestCase):
    """Test cases for reminder engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preferences = NotificationPreferences()
        self.engine = ReminderEngine(self.preferences)
    
    def test_initialization(self):
        """Test reminder engine initialization."""
        self.assertIsNotNone(self.engine)
        self.assertGreater(len(self.engine.reminder_rules), 0)
        self.assertEqual(len(self.engine.monitored_items), 0)
    
    def test_add_monitored_item(self):
        """Test adding items to monitor."""
        item = MonitoredItem(
            id="test_item",
            title="Test Item",
            due_time=datetime.now() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=["test"]
        )
        
        self.engine.add_monitored_item(item)
        
        self.assertIn("test_item", self.engine.monitored_items)
        self.assertEqual(self.engine.monitored_items["test_item"].title, "Test Item")
    
    def test_remove_monitored_item(self):
        """Test removing items from monitoring."""
        item = MonitoredItem(
            id="remove_test",
            title="Remove Test",
            due_time=datetime.now() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        
        self.engine.add_monitored_item(item)
        self.assertIn("remove_test", self.engine.monitored_items)
        
        self.engine.remove_monitored_item("remove_test")
        self.assertNotIn("remove_test", self.engine.monitored_items)
    
    def test_update_monitored_item(self):
        """Test updating monitored items."""
        item = MonitoredItem(
            id="update_test",
            title="Original Title",
            due_time=datetime.now() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        
        self.engine.add_monitored_item(item)
        
        # Update the item
        item.title = "Updated Title"
        item.priority = NotificationPriority.HIGH
        self.engine.update_monitored_item(item)
        
        updated_item = self.engine.monitored_items["update_test"]
        self.assertEqual(updated_item.title, "Updated Title")
        self.assertEqual(updated_item.priority, NotificationPriority.HIGH)
    
    def test_overdue_detection(self):
        """Test overdue item detection."""
        # Create overdue item
        overdue_item = MonitoredItem(
            id="overdue_test",
            title="Overdue Item",
            due_time=datetime.now() - timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        
        self.engine.add_monitored_item(overdue_item)
        
        overdue_items = self.engine.get_overdue_items()
        self.assertEqual(len(overdue_items), 1)
        self.assertEqual(overdue_items[0].id, "overdue_test")
    
    def test_snooze_item(self):
        """Test snoozing items."""
        item = MonitoredItem(
            id="snooze_test",
            title="Snooze Test",
            due_time=datetime.now() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        
        self.engine.add_monitored_item(item)
        original_due_time = item.due_time
        
        # Snooze for 30 minutes
        self.engine.snooze_item("snooze_test", 30)
        
        updated_item = self.engine.monitored_items["snooze_test"]
        self.assertGreater(updated_item.due_time, original_due_time)
        
        # Should be approximately 30 minutes later
        time_diff = updated_item.due_time - original_due_time
        self.assertAlmostEqual(time_diff.total_seconds(), 30 * 60, delta=60)
    
    def test_mark_item_complete(self):
        """Test marking items as complete."""
        item = MonitoredItem(
            id="complete_test",
            title="Complete Test",
            due_time=datetime.now() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        
        self.engine.add_monitored_item(item)
        self.assertIn("complete_test", self.engine.monitored_items)
        
        self.engine.mark_item_complete("complete_test")
        self.assertNotIn("complete_test", self.engine.monitored_items)
    
    def test_monitoring_stats(self):
        """Test monitoring statistics."""
        # Add various items
        items = [
            MonitoredItem(
                id="stats_test_1",
                title="Due Today",
                due_time=datetime.now() + timedelta(hours=2),
                item_type="task",
                priority=NotificationPriority.MEDIUM,
                tags=[]
            ),
            MonitoredItem(
                id="stats_test_2",
                title="Overdue",
                due_time=datetime.now() - timedelta(hours=1),
                item_type="task",
                priority=NotificationPriority.HIGH,
                tags=[]
            )
        ]
        
        for item in items:
            self.engine.add_monitored_item(item)
        
        stats = self.engine.get_monitoring_stats()
        
        self.assertEqual(stats["total_monitored_items"], 2)
        self.assertEqual(stats["overdue_items"], 1)
        self.assertGreaterEqual(stats["due_today"], 0)
        self.assertGreaterEqual(stats["total_scheduled_reminders"], 0)
    
    def test_custom_reminder_rule(self):
        """Test adding custom reminder rules."""
        initial_rule_count = len(self.engine.reminder_rules)
        
        custom_rule = ReminderRule(
            name="Custom Test Rule",
            applies_to_types=["test"],
            intervals=[ReminderInterval.MINUTES_5]
        )
        
        self.engine.add_reminder_rule(custom_rule)
        
        self.assertEqual(len(self.engine.reminder_rules), initial_rule_count + 1)
        
        # Remove the rule
        self.engine.remove_reminder_rule(custom_rule.id)
        self.assertEqual(len(self.engine.reminder_rules), initial_rule_count)


class TestMonitoredItem(unittest.TestCase):
    """Test cases for monitored items."""
    
    def test_monitored_item_creation(self):
        """Test creating monitored items."""
        item = MonitoredItem(
            id="test_item",
            title="Test Item",
            due_time=datetime.now() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["test", "important"]
        )
        
        self.assertEqual(item.id, "test_item")
        self.assertEqual(item.title, "Test Item")
        self.assertEqual(item.item_type, "task")
        self.assertEqual(item.priority, NotificationPriority.HIGH)
        self.assertEqual(item.tags, ["test", "important"])
    
    def test_overdue_detection(self):
        """Test overdue detection for items."""
        # Future item - use utcnow to match the MonitoredItem implementation
        future_item = MonitoredItem(
            id="future",
            title="Future Item",
            due_time=datetime.utcnow() + timedelta(hours=2),  # More buffer time
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        self.assertFalse(future_item.is_overdue())
        
        # Overdue item
        overdue_item = MonitoredItem(
            id="overdue",
            title="Overdue Item",
            due_time=datetime.now() - timedelta(hours=2),  # More clearly overdue
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        self.assertTrue(overdue_item.is_overdue())
    
    def test_time_calculations(self):
        """Test time calculation methods."""
        item = MonitoredItem(
            id="time_test",
            title="Time Test",
            due_time=datetime.now() + timedelta(hours=3, minutes=30),  # More buffer time
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=[]
        )
        
        time_until = item.time_until_due()
        self.assertGreater(time_until.total_seconds(), 0)
        
        minutes_until = item.minutes_until_due()
        self.assertGreater(minutes_until, 0)
        self.assertAlmostEqual(minutes_until, 210, delta=10)  # ~3.5 hours


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)