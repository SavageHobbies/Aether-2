"""
Reminder engine for monitoring deadlines and scheduling notifications.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import threading
import time
from dataclasses import dataclass

from .notification_types import (
    Notification, NotificationType, NotificationPriority, NotificationChannel,
    ReminderRule, ReminderInterval, NotificationPreferences
)

logger = logging.getLogger(__name__)


@dataclass
class MonitoredItem:
    """Represents an item being monitored for reminders."""
    id: str
    title: str
    due_time: datetime
    item_type: str  # "task", "event", "deadline"
    priority: NotificationPriority
    tags: List[str]
    
    # Context
    source_task_id: Optional[str] = None
    source_event_id: Optional[str] = None
    source_conversation_id: Optional[str] = None
    
    # Reminder tracking
    reminders_sent: int = 0
    last_reminder_sent: Optional[datetime] = None
    
    def is_overdue(self) -> bool:
        """Check if the item is overdue."""
        return datetime.utcnow() > self.due_time
    
    def time_until_due(self) -> timedelta:
        """Get time remaining until due."""
        return self.due_time - datetime.utcnow()
    
    def minutes_until_due(self) -> int:
        """Get minutes remaining until due."""
        delta = self.time_until_due()
        return int(delta.total_seconds() / 60)


class ReminderEngine:
    """Engine for monitoring deadlines and scheduling reminders."""
    
    def __init__(self, preferences: NotificationPreferences = None):
        """Initialize the reminder engine."""
        self.preferences = preferences or NotificationPreferences()
        self.reminder_rules: List[ReminderRule] = []
        self.monitored_items: Dict[str, MonitoredItem] = {}
        self.scheduled_notifications: List[Tuple[datetime, Notification]] = []
        
        # Threading for background monitoring
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._monitoring_interval = 60  # Check every minute
        
        # Callbacks
        self._notification_callback = None
        
        # Setup default reminder rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default reminder rules."""
        # High priority tasks
        high_priority_rule = ReminderRule(
            name="High Priority Tasks",
            applies_to_types=["task", "deadline"],
            applies_to_priorities=[NotificationPriority.HIGH, NotificationPriority.URGENT],
            intervals=[ReminderInterval.HOUR_1, ReminderInterval.HOURS_4, ReminderInterval.DAY_1],
            preferred_channels=[NotificationChannel.DESKTOP, NotificationChannel.MOBILE_PUSH],
            title_template="⚠️ High Priority: {title}",
            message_template="Don't forget: {title} is due {due_time_relative}"
        )
        
        # Meeting reminders
        meeting_rule = ReminderRule(
            name="Meeting Reminders",
            applies_to_types=["meeting", "event"],
            intervals=[ReminderInterval.MINUTES_15, ReminderInterval.HOUR_1],
            preferred_channels=[NotificationChannel.DESKTOP, NotificationChannel.IN_APP],
            title_template="📅 Meeting Reminder",
            message_template="Meeting '{title}' starts in {time_until_due}"
        )
        
        # General task reminders
        general_rule = ReminderRule(
            name="General Task Reminders",
            applies_to_types=["task"],
            intervals=[ReminderInterval.HOUR_1, ReminderInterval.DAY_1],
            preferred_channels=[NotificationChannel.IN_APP],
            title_template="📋 Task Reminder",
            message_template="Task '{title}' is due {due_time_relative}"
        )
        
        # Overdue items
        overdue_rule = ReminderRule(
            name="Overdue Items",
            applies_to_types=["task", "deadline", "meeting"],
            custom_intervals_minutes=[0],  # Immediate notification when overdue
            preferred_channels=[NotificationChannel.DESKTOP, NotificationChannel.MOBILE_PUSH],
            title_template="🚨 OVERDUE: {title}",
            message_template="'{title}' was due {overdue_time_ago} ago and needs attention",
            max_reminders=5  # More reminders for overdue items
        )
        
        self.reminder_rules = [high_priority_rule, meeting_rule, general_rule, overdue_rule]
    
    def add_reminder_rule(self, rule: ReminderRule):
        """Add a custom reminder rule."""
        self.reminder_rules.append(rule)
        logger.info(f"Added reminder rule: {rule.name}")
    
    def remove_reminder_rule(self, rule_id: str):
        """Remove a reminder rule by ID."""
        self.reminder_rules = [rule for rule in self.reminder_rules if rule.id != rule_id]
        logger.info(f"Removed reminder rule: {rule_id}")
    
    def add_monitored_item(self, item: MonitoredItem):
        """Add an item to be monitored for reminders."""
        self.monitored_items[item.id] = item
        self._schedule_reminders_for_item(item)
        logger.info(f"Added monitored item: {item.title} (due: {item.due_time})")
    
    def remove_monitored_item(self, item_id: str):
        """Remove an item from monitoring."""
        if item_id in self.monitored_items:
            item = self.monitored_items[item_id]
            del self.monitored_items[item_id]
            self._cancel_reminders_for_item(item_id)
            logger.info(f"Removed monitored item: {item.title}")
    
    def update_monitored_item(self, item: MonitoredItem):
        """Update a monitored item (reschedules reminders)."""
        if item.id in self.monitored_items:
            self._cancel_reminders_for_item(item.id)
            self.monitored_items[item.id] = item
            self._schedule_reminders_for_item(item)
            logger.info(f"Updated monitored item: {item.title}")
    
    def _schedule_reminders_for_item(self, item: MonitoredItem):
        """Schedule reminders for a specific item based on applicable rules."""
        for rule in self.reminder_rules:
            if rule.should_remind_for_item(item.item_type, item.priority, item.tags):
                reminder_times = rule.get_reminder_times(item.due_time)
                
                for reminder_time in reminder_times:
                    # Skip if in quiet hours (unless urgent/critical)
                    if rule.is_quiet_time(reminder_time) and item.priority not in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
                        continue
                    
                    notification = self._create_reminder_notification(item, rule, reminder_time)
                    self.scheduled_notifications.append((reminder_time, notification))
        
        # Sort scheduled notifications by time
        self.scheduled_notifications.sort(key=lambda x: x[0])
    
    def _cancel_reminders_for_item(self, item_id: str):
        """Cancel all scheduled reminders for an item."""
        self.scheduled_notifications = [
            (time, notif) for time, notif in self.scheduled_notifications
            if notif.source_task_id != item_id and notif.source_event_id != item_id
        ]
    
    def _create_reminder_notification(self, item: MonitoredItem, rule: ReminderRule, reminder_time: datetime) -> Notification:
        """Create a reminder notification for an item."""
        # Calculate relative time strings
        time_until_due = item.due_time - reminder_time
        due_time_relative = self._format_relative_time(time_until_due)
        time_until_due_str = self._format_time_duration(time_until_due)
        
        # Template variables
        variables = {
            "title": item.title,
            "due_time": item.due_time.strftime("%Y-%m-%d %H:%M"),
            "due_time_relative": due_time_relative,
            "time_until_due": time_until_due_str,
            "item_type": item.item_type,
            "priority": item.priority.value
        }
        
        # Handle overdue items
        if item.is_overdue():
            overdue_time = datetime.utcnow() - item.due_time
            variables["overdue_time_ago"] = self._format_time_duration(overdue_time)
        
        # Render templates
        title = rule.title_template or "Reminder: {title}"
        message = rule.message_template or "Don't forget: {title}"
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        # Determine notification type
        if item.is_overdue():
            notification_type = NotificationType.TASK_OVERDUE
            priority = NotificationPriority.URGENT
        elif item.item_type == "meeting":
            notification_type = NotificationType.MEETING_REMINDER
            priority = item.priority
        elif time_until_due.total_seconds() < 3600:  # Less than 1 hour
            notification_type = NotificationType.DEADLINE_WARNING
            # Use higher priority for urgent deadlines
            priority_levels = {
                NotificationPriority.LOW: 1,
                NotificationPriority.MEDIUM: 2,
                NotificationPriority.HIGH: 3,
                NotificationPriority.URGENT: 4,
                NotificationPriority.CRITICAL: 5
            }
            current_level = priority_levels.get(item.priority, 2)
            high_level = priority_levels.get(NotificationPriority.HIGH, 3)
            priority = item.priority if current_level >= high_level else NotificationPriority.HIGH
        else:
            notification_type = NotificationType.TASK_REMINDER
            priority = item.priority
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channels=rule.preferred_channels.copy(),
            scheduled_time=reminder_time,
            source_task_id=item.source_task_id,
            source_event_id=item.source_event_id,
            source_conversation_id=item.source_conversation_id,
            tags=item.tags.copy()
        )
        
        # Add actions
        notification.add_action("view", "View Details", "callback", {"action": "view_item", "item_id": item.id})
        notification.add_action("snooze", "Snooze", "callback", {"action": "snooze", "item_id": item.id, "minutes": self.preferences.snooze_duration_minutes})
        notification.add_action("complete", "Mark Complete", "callback", {"action": "complete_item", "item_id": item.id}, is_primary=True)
        
        return notification
    
    def _format_relative_time(self, time_delta: timedelta) -> str:
        """Format a time delta as a relative time string."""
        total_seconds = int(time_delta.total_seconds())
        
        if total_seconds < 0:
            return "overdue"
        elif total_seconds < 60:
            return "in less than a minute"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"in {minutes} minute{'s' if minutes != 1 else ''}"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"in {hours} hour{'s' if hours != 1 else ''}"
        else:
            days = total_seconds // 86400
            return f"in {days} day{'s' if days != 1 else ''}"
    
    def _format_time_duration(self, time_delta: timedelta) -> str:
        """Format a time delta as a duration string."""
        total_seconds = int(abs(time_delta.total_seconds()))
        
        if total_seconds < 60:
            return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours > 0:
                return f"{days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{days} day{'s' if days != 1 else ''}"
    
    def start_monitoring(self, notification_callback=None):
        """Start the background monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoring is already running")
            return
        
        self._notification_callback = notification_callback
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Started reminder monitoring")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5)
            logger.info("Stopped reminder monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in the background."""
        while not self._stop_monitoring.is_set():
            try:
                self._check_and_send_reminders()
                self._cleanup_expired_items()
                
                # Wait for the next check interval
                self._stop_monitoring.wait(self._monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Continue monitoring even if there's an error
                time.sleep(self._monitoring_interval)
    
    def _check_and_send_reminders(self):
        """Check for reminders that should be sent now."""
        current_time = datetime.utcnow()
        reminders_to_send = []
        
        # Find reminders that should be sent
        for i, (scheduled_time, notification) in enumerate(self.scheduled_notifications):
            if scheduled_time <= current_time:
                reminders_to_send.append((i, notification))
            else:
                break  # List is sorted, so we can stop here
        
        # Send reminders and remove from schedule
        for i, notification in reversed(reminders_to_send):  # Reverse to maintain indices
            if self.preferences.should_send_notification(notification):
                self._send_notification(notification)
                
                # Update reminder count for the item
                item_id = notification.source_task_id or notification.source_event_id
                if item_id and item_id in self.monitored_items:
                    item = self.monitored_items[item_id]
                    item.reminders_sent += 1
                    item.last_reminder_sent = current_time
            
            # Remove from scheduled notifications
            del self.scheduled_notifications[i]
    
    def _send_notification(self, notification: Notification):
        """Send a notification using the configured callback."""
        if self._notification_callback:
            try:
                self._notification_callback(notification)
                notification.status = notification.status.SENT
                notification.sent_at = datetime.utcnow()
                logger.info(f"Sent notification: {notification.title}")
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                notification.status = notification.status.FAILED
        else:
            logger.warning(f"No notification callback configured, skipping: {notification.title}")
    
    def _cleanup_expired_items(self):
        """Remove expired items and notifications."""
        current_time = datetime.utcnow()
        
        # Remove items that are very overdue (more than 7 days)
        expired_items = []
        for item_id, item in self.monitored_items.items():
            if item.is_overdue() and (current_time - item.due_time).days > 7:
                expired_items.append(item_id)
        
        for item_id in expired_items:
            self.remove_monitored_item(item_id)
            logger.info(f"Removed expired item: {item_id}")
        
        # Remove expired scheduled notifications
        self.scheduled_notifications = [
            (time, notif) for time, notif in self.scheduled_notifications
            if not notif.is_expired()
        ]
    
    def get_upcoming_reminders(self, hours_ahead: int = 24) -> List[Tuple[datetime, Notification]]:
        """Get reminders scheduled within the next N hours."""
        cutoff_time = datetime.utcnow() + timedelta(hours=hours_ahead)
        
        return [
            (time, notif) for time, notif in self.scheduled_notifications
            if time <= cutoff_time
        ]
    
    def get_overdue_items(self) -> List[MonitoredItem]:
        """Get all overdue items."""
        return [item for item in self.monitored_items.values() if item.is_overdue()]
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get statistics about the monitoring system."""
        current_time = datetime.utcnow()
        
        # Count items by status
        total_items = len(self.monitored_items)
        overdue_items = len(self.get_overdue_items())
        due_today = len([
            item for item in self.monitored_items.values()
            if item.due_time.date() == current_time.date() and not item.is_overdue()
        ])
        due_this_week = len([
            item for item in self.monitored_items.values()
            if (item.due_time - current_time).days <= 7 and not item.is_overdue()
        ])
        
        # Count scheduled reminders
        upcoming_reminders = len(self.get_upcoming_reminders(24))
        total_scheduled = len(self.scheduled_notifications)
        
        return {
            "total_monitored_items": total_items,
            "overdue_items": overdue_items,
            "due_today": due_today,
            "due_this_week": due_this_week,
            "upcoming_reminders_24h": upcoming_reminders,
            "total_scheduled_reminders": total_scheduled,
            "active_reminder_rules": len(self.reminder_rules),
            "monitoring_active": self._monitoring_thread and self._monitoring_thread.is_alive()
        }
    
    def snooze_item(self, item_id: str, minutes: int = None):
        """Snooze reminders for an item."""
        if minutes is None:
            minutes = self.preferences.snooze_duration_minutes
        
        if item_id in self.monitored_items:
            item = self.monitored_items[item_id]
            
            # Update due time
            item.due_time += timedelta(minutes=minutes)
            
            # Reschedule reminders
            self._cancel_reminders_for_item(item_id)
            self._schedule_reminders_for_item(item)
            
            logger.info(f"Snoozed item {item.title} for {minutes} minutes")
    
    def mark_item_complete(self, item_id: str):
        """Mark an item as complete and remove from monitoring."""
        if item_id in self.monitored_items:
            item = self.monitored_items[item_id]
            self.remove_monitored_item(item_id)
            logger.info(f"Marked item complete: {item.title}")


# Global reminder engine instance
_reminder_engine = None


def get_reminder_engine(preferences: NotificationPreferences = None) -> ReminderEngine:
    """Get a singleton instance of the reminder engine."""
    global _reminder_engine
    if _reminder_engine is None:
        _reminder_engine = ReminderEngine(preferences)
    return _reminder_engine