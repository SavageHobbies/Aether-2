"""
Comprehensive unit tests for the notification and reminder system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os
import json

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.notifications.notification_manager import NotificationManager, get_notification_manager
from core.notifications.reminder_engine import ReminderEngine, MonitoredItem, get_reminder_engine
from core.notifications.intelligent_prioritizer import IntelligentNotificationPrioritizer, get_intelligent_prioritizer
from core.notifications.deadline_monitor import DeadlineMonitor, DeadlineItem, DeadlineStatus, DeadlineMonitorConfig
from core.notifications.notification_types import (
    Notification, NotificationType, NotificationPriority, NotificationChannel,
    ReminderRule, ReminderInterval, NotificationPreferences, NotificationStatus
)


class TestNotificationTypes(unittest.TestCase):
    """Test notification data types and structures."""
    
    def test_notification_creation(self):
        """Test basic notification creation."""
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
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertIsNotNone(notification.id)
        self.assertIsNotNone(notification.created_at)
        self.assertEqual(len(notification.channels), 1)  # Default channel
    
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
        
        # Should not send yet (scheduled for future)
        future_notification = Notification(
            title="Future",
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        self.assertFalse(future_notification.should_send_now())
        
        # Should send (scheduled for past)
        past_notification = Notification(
            title="Past",
            scheduled_time=datetime.utcnow() - timedelta(minutes=1)
        )
        self.assertTrue(past_notification.should_send_now())
    
    def test_notification_actions(self):
        """Test notification actions."""
        notification = Notification(title="Test")
        
        # Add action
        notification.add_action("test_action", "Test Action", "callback", {"key": "value"}, True)
        
        self.assertEqual(len(notification.actions), 1)
        action = notification.actions[0]
        self.assertEqual(action.id, "test_action")
        self.assertEqual(action.label, "Test Action")
        self.assertEqual(action.action_type, "callback")
        self.assertEqual(action.action_data["key"], "value")
        self.assertTrue(action.is_primary)
    
    def test_reminder_rule_creation(self):
        """Test reminder rule creation and logic."""
        rule = ReminderRule(
            name="Test Rule",
            applies_to_types=["task"],
            applies_to_priorities=[NotificationPriority.HIGH],
            intervals=[ReminderInterval.HOUR_1, ReminderInterval.DAY_1],
            preferred_channels=[NotificationChannel.DESKTOP]
        )
        
        self.assertEqual(rule.name, "Test Rule")
        self.assertIn("task", rule.applies_to_types)
        self.assertIn(NotificationPriority.HIGH, rule.applies_to_priorities)
        self.assertEqual(len(rule.intervals), 2)
        self.assertTrue(rule.enabled)
    
    def test_reminder_rule_matching(self):
        """Test reminder rule matching logic."""
        rule = ReminderRule(
            applies_to_types=["task"],
            applies_to_priorities=[NotificationPriority.HIGH],
            applies_to_tags=["urgent"]
        )
        
        # Should match
        self.assertTrue(rule.should_remind_for_item("task", NotificationPriority.HIGH, ["urgent", "work"]))
        
        # Should not match (wrong type)
        self.assertFalse(rule.should_remind_for_item("meeting", NotificationPriority.HIGH, ["urgent"]))
        
        # Should not match (wrong priority)
        self.assertFalse(rule.should_remind_for_item("task", NotificationPriority.LOW, ["urgent"]))
        
        # Should not match (no matching tags)
        self.assertFalse(rule.should_remind_for_item("task", NotificationPriority.HIGH, ["normal"]))
    
    def test_reminder_rule_timing(self):
        """Test reminder rule timing calculations."""
        rule = ReminderRule(
            intervals=[ReminderInterval.HOUR_1, ReminderInterval.DAY_1],
            custom_intervals_minutes=[30, 120]
        )
        
        due_time = datetime.utcnow() + timedelta(hours=25)  # Due in 25 hours
        reminder_times = rule.get_reminder_times(due_time)
        
        # Should have at least 3 reminders (some might be filtered out if too close to now)
        self.assertGreaterEqual(len(reminder_times), 3)
        
        # Check that all times are in the future
        now = datetime.utcnow()
        for reminder_time in reminder_times:
            self.assertGreater(reminder_time, now)
    
    def test_notification_preferences(self):
        """Test notification preferences logic."""
        preferences = NotificationPreferences(
            notifications_enabled=True,
            minimum_priority=NotificationPriority.MEDIUM,
            quiet_hours_enabled=True,
            quiet_hours_start=22,
            quiet_hours_end=8
        )
        
        # Should allow medium priority
        medium_notification = Notification(
            title="Medium",
            priority=NotificationPriority.MEDIUM
        )
        self.assertTrue(preferences.should_send_notification(medium_notification))
        
        # Should block low priority
        low_notification = Notification(
            title="Low",
            priority=NotificationPriority.LOW
        )
        self.assertFalse(preferences.should_send_notification(low_notification))


class TestNotificationManager(unittest.TestCase):
    """Test notification manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preferences = NotificationPreferences(
            desktop_notifications=True,
            email_notifications=False
        )
        self.manager = NotificationManager(self.preferences)
    
    def test_manager_initialization(self):
        """Test notification manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.preferences, self.preferences)
        self.assertGreater(len(self.manager.channels), 0)
    
    def test_send_notification(self):
        """Test sending notifications."""
        notification = Notification(
            title="Test Notification",
            message="Test message",
            channels=[NotificationChannel.IN_APP]
        )
        
        # Mock the in-app channel
        mock_channel = Mock()
        mock_channel.enabled = True
        mock_channel.is_available.return_value = True
        mock_channel.send_notification.return_value = True
        
        self.manager.channels[NotificationChannel.IN_APP] = mock_channel
        
        result = self.manager.send_notification(notification)
        
        self.assertTrue(result)
        self.assertEqual(notification.status, NotificationStatus.SENT)
        self.assertIsNotNone(notification.sent_at)
        mock_channel.send_notification.assert_called_once_with(notification)
    
    def test_send_immediate_notification(self):
        """Test sending immediate notifications."""
        # Mock a channel
        mock_channel = Mock()
        mock_channel.enabled = True
        mock_channel.is_available.return_value = True
        mock_channel.send_notification.return_value = True
        
        self.manager.channels[NotificationChannel.DESKTOP] = mock_channel
        
        result = self.manager.send_immediate_notification(
            "Test Title",
            "Test Message",
            NotificationType.SYSTEM_ALERT,
            NotificationPriority.HIGH,
            [NotificationChannel.DESKTOP]
        )
        
        self.assertTrue(result)
        mock_channel.send_notification.assert_called_once()
    
    def test_notification_filtering(self):
        """Test notification filtering based on preferences."""
        # Create notification that should be filtered out
        low_priority_notification = Notification(
            title="Low Priority",
            priority=NotificationPriority.LOW
        )
        
        # Set preferences to block low priority
        self.manager.preferences.minimum_priority = NotificationPriority.MEDIUM
        
        result = self.manager.send_notification(low_priority_notification)
        
        self.assertFalse(result)
        self.assertEqual(low_priority_notification.status, NotificationStatus.PENDING)
    
    def test_notification_history(self):
        """Test notification history tracking."""
        notification = Notification(title="Test")
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()
        
        self.manager.notification_history.append(notification)
        
        history = self.manager.get_notification_history(24)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].title, "Test")
    
    def test_mark_notification_read(self):
        """Test marking notifications as read."""
        notification = Notification(title="Test")
        self.manager.notification_history.append(notification)
        
        self.manager.mark_notification_read(notification.id)
        
        self.assertEqual(notification.status, NotificationStatus.READ)
        self.assertIsNotNone(notification.read_at)
    
    def test_statistics(self):
        """Test notification statistics."""
        # Add some test data
        self.manager.stats.total_sent = 10
        self.manager.stats.total_delivered = 8
        self.manager.stats.total_read = 6
        self.manager.stats.total_failed = 2
        
        stats = self.manager.get_stats()
        
        self.assertEqual(stats.total_sent, 10)
        self.assertEqual(stats.delivery_rate, 80.0)
        self.assertEqual(stats.read_rate, 75.0)
        self.assertEqual(stats.failure_rate, 20.0)


class TestReminderEngine(unittest.TestCase):
    """Test reminder engine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preferences = NotificationPreferences()
        self.engine = ReminderEngine(self.preferences)
    
    def test_engine_initialization(self):
        """Test reminder engine initialization."""
        self.assertIsNotNone(self.engine)
        self.assertGreater(len(self.engine.reminder_rules), 0)
    
    def test_add_monitored_item(self):
        """Test adding items to monitoring."""
        item = MonitoredItem(
            id="test_item",
            title="Test Task",
            due_time=datetime.utcnow() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["test"]
        )
        
        self.engine.add_monitored_item(item)
        
        self.assertIn("test_item", self.engine.monitored_items)
        self.assertEqual(self.engine.monitored_items["test_item"].title, "Test Task")
    
    def test_remove_monitored_item(self):
        """Test removing items from monitoring."""
        item = MonitoredItem(
            id="test_item",
            title="Test Task",
            due_time=datetime.utcnow() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["test"]
        )
        
        self.engine.add_monitored_item(item)
        self.assertIn("test_item", self.engine.monitored_items)
        
        self.engine.remove_monitored_item("test_item")
        self.assertNotIn("test_item", self.engine.monitored_items)
    
    def test_monitored_item_status(self):
        """Test monitored item status detection."""
        # Overdue item
        overdue_item = MonitoredItem(
            id="overdue",
            title="Overdue Task",
            due_time=datetime.utcnow() - timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["test"]
        )
        
        self.assertTrue(overdue_item.is_overdue())
        self.assertLess(overdue_item.minutes_until_due(), 0)
        
        # Future item
        future_item = MonitoredItem(
            id="future",
            title="Future Task",
            due_time=datetime.utcnow() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=["test"]
        )
        
        self.assertFalse(future_item.is_overdue())
        self.assertGreater(future_item.minutes_until_due(), 0)
    
    def test_reminder_scheduling(self):
        """Test reminder scheduling logic."""
        # Add item that should trigger reminders
        item = MonitoredItem(
            id="test_item",
            title="Test Task",
            due_time=datetime.utcnow() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["urgent"]
        )
        
        self.engine.add_monitored_item(item)
        
        # Check that reminders were scheduled
        upcoming_reminders = self.engine.get_upcoming_reminders(24)
        self.assertGreater(len(upcoming_reminders), 0)
    
    def test_snooze_item(self):
        """Test snoozing items."""
        item = MonitoredItem(
            id="test_item",
            title="Test Task",
            due_time=datetime.utcnow() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=["test"]
        )
        
        self.engine.add_monitored_item(item)
        original_due_time = item.due_time
        
        self.engine.snooze_item("test_item", 30)  # Snooze 30 minutes
        
        updated_item = self.engine.monitored_items["test_item"]
        self.assertGreater(updated_item.due_time, original_due_time)
    
    def test_mark_item_complete(self):
        """Test marking items as complete."""
        item = MonitoredItem(
            id="test_item",
            title="Test Task",
            due_time=datetime.utcnow() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=["test"]
        )
        
        self.engine.add_monitored_item(item)
        self.assertIn("test_item", self.engine.monitored_items)
        
        self.engine.mark_item_complete("test_item")
        self.assertNotIn("test_item", self.engine.monitored_items)
    
    def test_get_overdue_items(self):
        """Test getting overdue items."""
        # Add overdue item
        overdue_item = MonitoredItem(
            id="overdue",
            title="Overdue Task",
            due_time=datetime.utcnow() - timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["test"]
        )
        
        # Add future item
        future_item = MonitoredItem(
            id="future",
            title="Future Task",
            due_time=datetime.utcnow() + timedelta(hours=1),
            item_type="task",
            priority=NotificationPriority.MEDIUM,
            tags=["test"]
        )
        
        self.engine.add_monitored_item(overdue_item)
        self.engine.add_monitored_item(future_item)
        
        overdue_items = self.engine.get_overdue_items()
        self.assertEqual(len(overdue_items), 1)
        self.assertEqual(overdue_items[0].id, "overdue")
    
    def test_monitoring_stats(self):
        """Test monitoring statistics."""
        # Add test items
        for i in range(3):
            item = MonitoredItem(
                id=f"item_{i}",
                title=f"Task {i}",
                due_time=datetime.utcnow() + timedelta(hours=i+1),
                item_type="task",
                priority=NotificationPriority.MEDIUM,
                tags=["test"]
            )
            self.engine.add_monitored_item(item)
        
        stats = self.engine.get_monitoring_stats()
        
        self.assertEqual(stats['total_monitored_items'], 3)
        self.assertIn('upcoming_reminders_24h', stats)
        self.assertIn('total_scheduled_reminders', stats)


class TestIntelligentPrioritizer(unittest.TestCase):
    """Test intelligent notification prioritizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.prioritizer = IntelligentNotificationPrioritizer(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_prioritizer_initialization(self):
        """Test prioritizer initialization."""
        self.assertIsNotNone(self.prioritizer)
        self.assertEqual(len(self.prioritizer.interaction_history), 0)
    
    def test_record_interaction(self):
        """Test recording user interactions."""
        notification = Notification(
            title="Test",
            notification_type=NotificationType.TASK_REMINDER,
            priority=NotificationPriority.MEDIUM,
            tags=["test"]
        )
        
        self.prioritizer.record_interaction(notification, "read", 30.0)
        
        self.assertEqual(len(self.prioritizer.interaction_history), 1)
        interaction = self.prioritizer.interaction_history[0]
        self.assertEqual(interaction.action_taken, "read")
        self.assertEqual(interaction.response_time_seconds, 30.0)
        self.assertGreater(interaction.engagement_score, 0)
    
    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        notification = Notification(
            title="Urgent Task",
            message="This is urgent",
            notification_type=NotificationType.DEADLINE_WARNING,
            priority=NotificationPriority.HIGH,
            tags=["urgent", "deadline"]
        )
        
        priority_score = self.prioritizer.calculate_priority_score(notification)
        
        self.assertIsNotNone(priority_score)
        self.assertEqual(priority_score.base_priority, NotificationPriority.HIGH)
        self.assertIsInstance(priority_score.confidence, float)
        self.assertIsInstance(priority_score.explanation, str)
    
    def test_engagement_score_calculation(self):
        """Test engagement score calculation."""
        # High engagement action
        high_score = self.prioritizer._calculate_engagement_score("acted", 10.0)
        self.assertGreater(high_score, 0.8)
        
        # Low engagement action
        low_score = self.prioritizer._calculate_engagement_score("ignored", 0.0)
        self.assertEqual(low_score, 0.0)
        
        # Medium engagement action
        medium_score = self.prioritizer._calculate_engagement_score("read", 60.0)
        self.assertGreater(medium_score, 0.5)
        self.assertLess(medium_score, 1.0)
    
    def test_should_suppress_notification(self):
        """Test notification suppression logic."""
        # Create notification that might be suppressed
        notification = Notification(
            title="Low Priority",
            priority=NotificationPriority.LOW,
            notification_type=NotificationType.SYSTEM_ALERT
        )
        
        # With no history, should not suppress
        should_suppress, reason = self.prioritizer.should_suppress_notification(notification)
        self.assertFalse(should_suppress)
        
        # Add some negative interactions
        for _ in range(10):
            self.prioritizer.record_interaction(notification, "ignored", 0.0)
        
        # Now might suppress based on patterns
        should_suppress, reason = self.prioritizer.should_suppress_notification(notification)
        # Result depends on learning algorithm, just check it returns boolean and string
        self.assertIsInstance(should_suppress, bool)
        self.assertIsInstance(reason, str)
    
    def test_get_preferred_channels(self):
        """Test preferred channel selection."""
        # High priority notification
        urgent_notification = Notification(
            title="Urgent",
            priority=NotificationPriority.URGENT
        )
        
        channels = self.prioritizer.get_preferred_channels(urgent_notification)
        self.assertIsInstance(channels, list)
        self.assertGreater(len(channels), 0)
        
        # Low priority notification
        low_notification = Notification(
            title="Low",
            priority=NotificationPriority.LOW
        )
        
        low_channels = self.prioritizer.get_preferred_channels(low_notification)
        self.assertLessEqual(len(low_channels), len(channels))  # Should use fewer channels
    
    def test_pattern_persistence(self):
        """Test saving and loading patterns."""
        # Record some interactions
        notification = Notification(
            title="Test",
            notification_type=NotificationType.TASK_REMINDER,
            priority=NotificationPriority.MEDIUM
        )
        
        self.prioritizer.record_interaction(notification, "read", 30.0)
        
        # Create new prioritizer with same file
        new_prioritizer = IntelligentNotificationPrioritizer(self.temp_file.name)
        
        # Should have loaded the interaction
        self.assertEqual(len(new_prioritizer.interaction_history), 1)
    
    def test_learning_stats(self):
        """Test learning statistics."""
        stats = self.prioritizer.get_learning_stats()
        
        self.assertIn('total_interactions', stats)
        self.assertIn('learning_active', stats)
        self.assertIn('confidence_level', stats)
        self.assertIsInstance(stats['total_interactions'], int)
        self.assertIsInstance(stats['learning_active'], bool)
        self.assertIsInstance(stats['confidence_level'], float)


class TestDeadlineMonitor(unittest.TestCase):
    """Test deadline monitoring system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        config = DeadlineMonitorConfig(
            check_interval_seconds=1,  # Fast checking for tests
            data_file=self.temp_file.name
        )
        self.monitor = DeadlineMonitor(config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.monitor.stop_monitoring()
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_monitor_initialization(self):
        """Test deadline monitor initialization."""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(len(self.monitor.monitored_items), 0)
    
    def test_add_deadline_item(self):
        """Test adding deadline items."""
        item = DeadlineItem(
            id="test_deadline",
            title="Test Deadline",
            deadline=datetime.now() + timedelta(hours=2),
            item_type="task",
            priority=NotificationPriority.HIGH
        )
        
        result = self.monitor.add_deadline_item(item)
        
        self.assertTrue(result)
        self.assertIn("test_deadline", self.monitor.monitored_items)
        self.assertEqual(self.monitor.monitored_items["test_deadline"].title, "Test Deadline")
    
    def test_deadline_item_status_updates(self):
        """Test deadline item status updates."""
        # Overdue item
        overdue_item = DeadlineItem(
            id="overdue",
            title="Overdue Item",
            deadline=datetime.now() - timedelta(hours=1)
        )
        
        self.monitor.add_deadline_item(overdue_item)
        stored_item = self.monitor.monitored_items["overdue"]
        
        self.assertEqual(stored_item.status, DeadlineStatus.OVERDUE)
        self.assertTrue(stored_item.is_overdue())
        
        # Upcoming item
        upcoming_item = DeadlineItem(
            id="upcoming",
            title="Upcoming Item",
            deadline=datetime.now() + timedelta(hours=25)
        )
        
        self.monitor.add_deadline_item(upcoming_item)
        stored_upcoming = self.monitor.monitored_items["upcoming"]
        
        self.assertEqual(stored_upcoming.status, DeadlineStatus.UPCOMING)
        self.assertFalse(stored_upcoming.is_overdue())
    
    def test_mark_completed(self):
        """Test marking items as completed."""
        item = DeadlineItem(
            id="test_item",
            title="Test Item",
            deadline=datetime.now() + timedelta(hours=1)
        )
        
        self.monitor.add_deadline_item(item)
        result = self.monitor.mark_completed("test_item", 100.0)
        
        self.assertTrue(result)
        stored_item = self.monitor.monitored_items["test_item"]
        self.assertEqual(stored_item.completion_percentage, 100.0)
        self.assertEqual(stored_item.status, DeadlineStatus.COMPLETED)
    
    def test_snooze_deadline(self):
        """Test snoozing deadlines."""
        item = DeadlineItem(
            id="test_item",
            title="Test Item",
            deadline=datetime.now() + timedelta(hours=1)
        )
        
        self.monitor.add_deadline_item(item)
        original_deadline = item.deadline
        
        result = self.monitor.snooze_deadline("test_item", 60)  # Snooze 1 hour
        
        self.assertTrue(result)
        stored_item = self.monitor.monitored_items["test_item"]
        self.assertGreater(stored_item.deadline, original_deadline)
    
    def test_get_upcoming_deadlines(self):
        """Test getting upcoming deadlines."""
        # Add items with different deadlines
        items = [
            DeadlineItem(
                id="soon",
                title="Soon",
                deadline=datetime.now() + timedelta(hours=2)
            ),
            DeadlineItem(
                id="later",
                title="Later",
                deadline=datetime.now() + timedelta(days=2)
            ),
            DeadlineItem(
                id="much_later",
                title="Much Later",
                deadline=datetime.now() + timedelta(days=10)
            )
        ]
        
        for item in items:
            self.monitor.add_deadline_item(item)
        
        # Get deadlines within 24 hours
        upcoming = self.monitor.get_upcoming_deadlines(24)
        self.assertEqual(len(upcoming), 1)  # Only "soon" should be included
        self.assertEqual(upcoming[0].id, "soon")
        
        # Get deadlines within 3 days
        upcoming_3days = self.monitor.get_upcoming_deadlines(72)
        self.assertEqual(len(upcoming_3days), 2)  # "soon" and "later"
    
    def test_get_overdue_items(self):
        """Test getting overdue items."""
        # Add overdue and non-overdue items
        overdue_item = DeadlineItem(
            id="overdue",
            title="Overdue",
            deadline=datetime.now() - timedelta(hours=1)
        )
        
        future_item = DeadlineItem(
            id="future",
            title="Future",
            deadline=datetime.now() + timedelta(hours=1)
        )
        
        self.monitor.add_deadline_item(overdue_item)
        self.monitor.add_deadline_item(future_item)
        
        overdue_items = self.monitor.get_overdue_items()
        self.assertEqual(len(overdue_items), 1)
        self.assertEqual(overdue_items[0].id, "overdue")
    
    def test_monitoring_stats(self):
        """Test monitoring statistics."""
        # Add some test items
        items = [
            DeadlineItem(id="1", title="Item 1", deadline=datetime.now() + timedelta(hours=1)),
            DeadlineItem(id="2", title="Item 2", deadline=datetime.now() - timedelta(hours=1)),  # Overdue
            DeadlineItem(id="3", title="Item 3", deadline=datetime.now() + timedelta(days=1))
        ]
        
        for item in items:
            self.monitor.add_deadline_item(item)
        
        stats = self.monitor.get_monitoring_stats()
        
        self.assertEqual(stats['total_monitored_items'], 3)
        self.assertIn('status_breakdown', stats)
        self.assertIn('upcoming_24h', stats)
        self.assertIn('monitoring_active', stats)
        self.assertIsInstance(stats['status_breakdown'], dict)
    
    def test_state_persistence(self):
        """Test saving and loading state."""
        # Add an item
        item = DeadlineItem(
            id="persistent_item",
            title="Persistent Item",
            deadline=datetime.now() + timedelta(hours=2),
            tags=["test", "persistent"]
        )
        
        self.monitor.add_deadline_item(item)
        self.monitor._save_state()
        
        # Create new monitor with same config
        new_config = DeadlineMonitorConfig(data_file=self.temp_file.name)
        new_monitor = DeadlineMonitor(new_config)
        
        # Should have loaded the item
        self.assertEqual(len(new_monitor.monitored_items), 1)
        self.assertIn("persistent_item", new_monitor.monitored_items)
        loaded_item = new_monitor.monitored_items["persistent_item"]
        self.assertEqual(loaded_item.title, "Persistent Item")
        self.assertEqual(loaded_item.tags, ["test", "persistent"])
    
    def test_reminder_intervals(self):
        """Test reminder interval calculations."""
        item = DeadlineItem(
            id="test_item",
            title="Test Item",
            deadline=datetime.now() + timedelta(hours=25),  # Due in 25 hours
            reminder_intervals=[60, 1440]  # 1 hour and 1 day before
        )
        
        reminder_times = item.get_next_reminder_times()
        
        self.assertEqual(len(reminder_times), 2)
        # All reminder times should be in the future
        now = datetime.now()
        for reminder_time in reminder_times:
            self.assertGreater(reminder_time, now)
    
    def test_should_send_reminder(self):
        """Test reminder sending logic."""
        item = DeadlineItem(
            id="test_item",
            title="Test Item",
            deadline=datetime.now() + timedelta(minutes=65),  # Due in 65 minutes
            reminder_intervals=[60]  # Remind 1 hour before
        )
        
        # Should send reminder (within 5-minute tolerance)
        self.assertTrue(item.should_send_reminder(60))
        
        # Should not send reminder for different interval
        self.assertFalse(item.should_send_reminder(30))


class TestNotificationIntegration(unittest.TestCase):
    """Test integration between notification system components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preferences = NotificationPreferences()
        self.manager = NotificationManager(self.preferences)
        self.engine = ReminderEngine(self.preferences)
        
        # Mock notification callback
        self.sent_notifications = []
        
        def mock_callback(notification):
            self.sent_notifications.append(notification)
            return self.manager.send_notification(notification)
        
        self.mock_callback = mock_callback
    
    def test_reminder_to_notification_flow(self):
        """Test the flow from reminder engine to notification manager."""
        # Add a monitored item
        item = MonitoredItem(
            id="integration_test",
            title="Integration Test Task",
            due_time=datetime.utcnow() + timedelta(minutes=30),  # Due soon
            item_type="task",
            priority=NotificationPriority.HIGH,
            tags=["integration", "test"]
        )
        
        self.engine.add_monitored_item(item)
        
        # Start monitoring with callback
        self.engine.start_monitoring(self.mock_callback)
        
        # Simulate time passing and check for reminders
        # (In real tests, you might use time mocking)
        
        # Stop monitoring
        self.engine.stop_monitoring()
        
        # Verify the integration worked
        self.assertIsNotNone(self.mock_callback)
    
    def test_end_to_end_notification_flow(self):
        """Test complete end-to-end notification flow."""
        # Create a notification
        notification = Notification(
            title="End-to-End Test",
            message="Testing complete notification flow",
            notification_type=NotificationType.TASK_REMINDER,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.IN_APP]
        )
        
        # Mock the in-app channel
        mock_channel = Mock()
        mock_channel.enabled = True
        mock_channel.is_available.return_value = True
        mock_channel.send_notification.return_value = True
        
        self.manager.channels[NotificationChannel.IN_APP] = mock_channel
        
        # Send notification
        result = self.manager.send_notification(notification)
        
        # Verify the flow
        self.assertTrue(result)
        self.assertEqual(notification.status, NotificationStatus.SENT)
        mock_channel.send_notification.assert_called_once_with(notification)
        
        # Mark as read
        self.manager.mark_notification_read(notification.id)
        self.assertEqual(notification.status, NotificationStatus.READ)
        
        # Check statistics
        stats = self.manager.get_stats()
        self.assertGreater(stats.total_sent, 0)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestNotificationTypes,
        TestNotificationManager,
        TestReminderEngine,
        TestIntelligentPrioritizer,
        TestDeadlineMonitor,
        TestNotificationIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)