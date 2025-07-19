"""
Advanced deadline monitoring system with configurable intervals and smart scheduling.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import json
import os

from .notification_types import (
    Notification, NotificationType, NotificationPriority, NotificationChannel,
    ReminderRule, ReminderInterval
)
from .intelligent_prioritizer import get_intelligent_prioritizer

logger = logging.getLogger(__name__)


class DeadlineStatus(Enum):
    """Status of a deadline."""
    UPCOMING = "upcoming"
    APPROACHING = "approaching"  # Within warning threshold
    IMMINENT = "imminent"       # Very close to deadline
    OVERDUE = "overdue"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class DeadlineItem:
    """Represents an item with a deadline to monitor."""
    id: str
    title: str
    description: str = ""
    
    # Timing
    deadline: datetime = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Classification
    item_type: str = "task"  # "task", "project", "meeting", "deadline"
    priority: NotificationPriority = NotificationPriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    
    # Status
    status: DeadlineStatus = DeadlineStatus.UPCOMING
    completion_percentage: float = 0.0
    
    # Reminder configuration
    reminder_intervals: List[int] = field(default_factory=list)  # Minutes before deadline
    custom_reminder_rule: Optional[str] = None  # ID of custom rule
    
    # Context
    source_task_id: Optional[str] = None
    source_event_id: Optional[str] = None
    source_project_id: Optional[str] = None
    assigned_to: Optional[str] = None
    
    # Tracking
    reminders_sent: int = 0
    last_reminder_sent: Optional[datetime] = None
    user_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default values."""
        if not self.reminder_intervals:
            # Default intervals: 1 week, 1 day, 4 hours, 1 hour, 15 minutes
            self.reminder_intervals = [10080, 1440, 240, 60, 15]
    
    def time_until_deadline(self) -> timedelta:
        """Get time remaining until deadline."""
        if not self.deadline:
            return timedelta(0)
        return self.deadline - datetime.now()
    
    def minutes_until_deadline(self) -> int:
        """Get minutes remaining until deadline."""
        delta = self.time_until_deadline()
        return int(delta.total_seconds() / 60)
    
    def is_overdue(self) -> bool:
        """Check if the deadline has passed."""
        return self.deadline and datetime.now() > self.deadline
    
    def is_approaching(self, threshold_hours: int = 24) -> bool:
        """Check if deadline is approaching within threshold."""
        if not self.deadline:
            return False
        return 0 < self.minutes_until_deadline() < (threshold_hours * 60)
    
    def is_imminent(self, threshold_minutes: int = 60) -> bool:
        """Check if deadline is imminent."""
        if not self.deadline:
            return False
        return 0 < self.minutes_until_deadline() < threshold_minutes
    
    def update_status(self):
        """Update the status based on current time and completion."""
        if self.completion_percentage >= 100:
            self.status = DeadlineStatus.COMPLETED
        elif self.is_overdue():
            self.status = DeadlineStatus.OVERDUE
        elif self.is_imminent():
            self.status = DeadlineStatus.IMMINENT
        elif self.is_approaching():
            self.status = DeadlineStatus.APPROACHING
        else:
            self.status = DeadlineStatus.UPCOMING
    
    def get_next_reminder_times(self) -> List[datetime]:
        """Get the next scheduled reminder times."""
        if not self.deadline:
            return []
        
        reminder_times = []
        now = datetime.now()
        
        for minutes_before in self.reminder_intervals:
            reminder_time = self.deadline - timedelta(minutes=minutes_before)
            if reminder_time > now:  # Only future reminders
                reminder_times.append(reminder_time)
        
        return sorted(reminder_times)
    
    def should_send_reminder(self, minutes_before: int) -> bool:
        """Check if a reminder should be sent for the given interval."""
        if not self.deadline:
            return False
        
        current_minutes_until = self.minutes_until_deadline()
        
        # Check if we're within the reminder window (±5 minutes tolerance)
        return abs(current_minutes_until - minutes_before) <= 5
    
    def record_interaction(self, action: str, details: Dict[str, Any] = None):
        """Record a user interaction with this deadline item."""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {}
        }
        self.user_interactions.append(interaction)
        
        # Keep only last 50 interactions
        if len(self.user_interactions) > 50:
            self.user_interactions = self.user_interactions[-50:]


@dataclass
class DeadlineMonitorConfig:
    """Configuration for the deadline monitor."""
    # Monitoring intervals
    check_interval_seconds: int = 60  # How often to check for reminders
    
    # Status thresholds
    approaching_threshold_hours: int = 24
    imminent_threshold_minutes: int = 60
    
    # Reminder settings
    max_reminders_per_item: int = 10
    reminder_cooldown_minutes: int = 5  # Minimum time between reminders for same item
    
    # Overdue handling
    overdue_reminder_interval_hours: int = 24  # How often to remind about overdue items
    max_overdue_reminders: int = 5
    
    # Performance
    max_monitored_items: int = 1000
    cleanup_completed_after_days: int = 7
    cleanup_cancelled_after_days: int = 1
    
    # Persistence
    save_state_interval_minutes: int = 15
    data_file: Optional[str] = None


class DeadlineMonitor:
    """Advanced deadline monitoring system."""
    
    def __init__(self, config: DeadlineMonitorConfig = None):
        """Initialize the deadline monitor."""
        self.config = config or DeadlineMonitorConfig()
        self.monitored_items: Dict[str, DeadlineItem] = {}
        self.reminder_rules: Dict[str, ReminderRule] = {}
        
        # Threading for background monitoring
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._last_save = datetime.now()
        
        # Callbacks
        self._notification_callback: Optional[Callable] = None
        self._status_change_callback: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'total_items_monitored': 0,
            'reminders_sent': 0,
            'overdue_items_detected': 0,
            'completed_items': 0,
            'last_cleanup': datetime.now()
        }
        
        # Setup data file path
        if not self.config.data_file:
            self.config.data_file = os.path.join(
                os.path.expanduser("~"), ".aether", "deadline_monitor.json"
            )
        
        # Load existing state
        self._load_state()
        
        # Get intelligent prioritizer
        self.prioritizer = get_intelligent_prioritizer()
    
    def add_deadline_item(self, item: DeadlineItem) -> bool:
        """Add an item to deadline monitoring."""
        if len(self.monitored_items) >= self.config.max_monitored_items:
            logger.warning(f"Maximum monitored items ({self.config.max_monitored_items}) reached")
            return False
        
        # Update status
        item.update_status()
        
        # Add to monitoring
        self.monitored_items[item.id] = item
        self.stats['total_items_monitored'] += 1
        
        logger.info(f"Added deadline item: {item.title} (due: {item.deadline}, status: {item.status.value})")
        
        # Trigger status change callback
        if self._status_change_callback:
            self._status_change_callback(item, "added")
        
        return True
    
    def remove_deadline_item(self, item_id: str) -> bool:
        """Remove an item from monitoring."""
        if item_id in self.monitored_items:
            item = self.monitored_items[item_id]
            del self.monitored_items[item_id]
            
            logger.info(f"Removed deadline item: {item.title}")
            
            # Trigger status change callback
            if self._status_change_callback:
                self._status_change_callback(item, "removed")
            
            return True
        return False
    
    def update_deadline_item(self, item: DeadlineItem) -> bool:
        """Update an existing deadline item."""
        if item.id not in self.monitored_items:
            return False
        
        old_status = self.monitored_items[item.id].status
        item.update_status()
        
        self.monitored_items[item.id] = item
        
        # Check for status changes
        if old_status != item.status:
            logger.info(f"Status changed for {item.title}: {old_status.value} -> {item.status.value}")
            
            if self._status_change_callback:
                self._status_change_callback(item, "status_changed")
        
        return True
    
    def mark_completed(self, item_id: str, completion_percentage: float = 100.0) -> bool:
        """Mark an item as completed."""
        if item_id in self.monitored_items:
            item = self.monitored_items[item_id]
            item.completion_percentage = completion_percentage
            item.update_status()
            
            if completion_percentage >= 100:
                self.stats['completed_items'] += 1
                item.record_interaction("completed", {"completion_percentage": completion_percentage})
            
            logger.info(f"Marked {item.title} as {completion_percentage}% complete")
            return True
        return False
    
    def snooze_deadline(self, item_id: str, snooze_minutes: int) -> bool:
        """Snooze a deadline by extending it."""
        if item_id in self.monitored_items:
            item = self.monitored_items[item_id]
            if item.deadline:
                old_deadline = item.deadline
                item.deadline += timedelta(minutes=snooze_minutes)
                item.update_status()
                item.record_interaction("snoozed", {
                    "snooze_minutes": snooze_minutes,
                    "old_deadline": old_deadline.isoformat(),
                    "new_deadline": item.deadline.isoformat()
                })
                
                logger.info(f"Snoozed {item.title} by {snooze_minutes} minutes")
                return True
        return False
    
    def get_items_by_status(self, status: DeadlineStatus) -> List[DeadlineItem]:
        """Get all items with a specific status."""
        return [item for item in self.monitored_items.values() if item.status == status]
    
    def get_upcoming_deadlines(self, hours_ahead: int = 24) -> List[DeadlineItem]:
        """Get deadlines coming up within the specified hours."""
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)
        
        upcoming = []
        for item in self.monitored_items.values():
            if (item.deadline and 
                item.deadline <= cutoff_time and 
                item.status not in [DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED]):
                upcoming.append(item)
        
        return sorted(upcoming, key=lambda x: x.deadline)
    
    def get_overdue_items(self) -> List[DeadlineItem]:
        """Get all overdue items."""
        return self.get_items_by_status(DeadlineStatus.OVERDUE)
    
    def start_monitoring(self, notification_callback: Callable = None, status_change_callback: Callable = None):
        """Start the background monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoring is already running")
            return
        
        self._notification_callback = notification_callback
        self._status_change_callback = status_change_callback
        self._stop_monitoring.clear()
        
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        logger.info("Started deadline monitoring")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5)
            logger.info("Stopped deadline monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                self._check_deadlines()
                self._send_due_reminders()
                self._update_item_statuses()
                self._cleanup_old_items()
                self._save_state_if_needed()
                
                # Wait for next check
                self._stop_monitoring.wait(self.config.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in deadline monitoring loop: {e}")
                time.sleep(self.config.check_interval_seconds)
    
    def _check_deadlines(self):
        """Check all deadlines and update statuses."""
        now = datetime.now()
        
        for item in self.monitored_items.values():
            if not item.deadline:
                continue
            
            old_status = item.status
            item.update_status()
            
            # Detect newly overdue items
            if old_status != DeadlineStatus.OVERDUE and item.status == DeadlineStatus.OVERDUE:
                self.stats['overdue_items_detected'] += 1
                logger.warning(f"Item became overdue: {item.title}")
                
                # Send immediate overdue notification
                self._send_overdue_notification(item)
    
    def _send_due_reminders(self):
        """Send reminders for items that are due."""
        now = datetime.now()
        
        for item in self.monitored_items.values():
            if item.status in [DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED]:
                continue
            
            # Check if any reminder intervals are due
            for minutes_before in item.reminder_intervals:
                if item.should_send_reminder(minutes_before):
                    # Check cooldown
                    if (item.last_reminder_sent and 
                        (now - item.last_reminder_sent).total_seconds() < self.config.reminder_cooldown_minutes * 60):
                        continue
                    
                    # Check max reminders
                    if item.reminders_sent >= self.config.max_reminders_per_item:
                        continue
                    
                    self._send_reminder_notification(item, minutes_before)
                    break  # Only send one reminder per check cycle
    
    def _send_reminder_notification(self, item: DeadlineItem, minutes_before: int):
        """Send a reminder notification for an item."""
        if not self._notification_callback:
            return
        
        # Determine notification type and priority based on urgency
        if item.status == DeadlineStatus.IMMINENT:
            notification_type = NotificationType.DEADLINE_WARNING
            base_priority = NotificationPriority.URGENT
        elif item.status == DeadlineStatus.APPROACHING:
            notification_type = NotificationType.TASK_REMINDER
            base_priority = NotificationPriority.HIGH
        else:
            notification_type = NotificationType.TASK_REMINDER
            base_priority = item.priority
        
        # Create notification
        time_until = item.time_until_deadline()
        time_str = self._format_time_duration(time_until)
        
        notification = Notification(
            title=f"⏰ Deadline Reminder: {item.title}",
            message=f"Due in {time_str}. {item.description}" if item.description else f"Due in {time_str}",
            notification_type=notification_type,
            priority=base_priority,
            channels=[NotificationChannel.DESKTOP, NotificationChannel.IN_APP],
            source_task_id=item.source_task_id,
            source_event_id=item.source_event_id,
            tags=item.tags.copy()
        )
        
        # Add actions
        notification.add_action("view", "View Details", "callback", {"action": "view_deadline", "item_id": item.id})
        notification.add_action("snooze", "Snooze 1h", "callback", {"action": "snooze_deadline", "item_id": item.id, "minutes": 60})
        notification.add_action("complete", "Mark Complete", "callback", {"action": "complete_deadline", "item_id": item.id}, is_primary=True)
        
        # Use intelligent prioritizer to adjust priority
        priority_score = self.prioritizer.calculate_priority_score(notification)
        notification.priority = priority_score.adjusted_priority
        notification.channels = self.prioritizer.get_preferred_channels(notification)
        
        # Check if notification should be suppressed
        should_suppress, reason = self.prioritizer.should_suppress_notification(notification)
        if should_suppress:
            logger.info(f"Suppressed reminder for {item.title}: {reason}")
            return
        
        # Send notification
        try:
            self._notification_callback(notification)
            
            # Update item tracking
            item.reminders_sent += 1
            item.last_reminder_sent = datetime.now()
            item.record_interaction("reminder_sent", {
                "minutes_before": minutes_before,
                "notification_type": notification_type.value,
                "priority": notification.priority.value
            })
            
            self.stats['reminders_sent'] += 1
            logger.info(f"Sent reminder for {item.title} ({minutes_before} minutes before deadline)")
            
        except Exception as e:
            logger.error(f"Failed to send reminder for {item.title}: {e}")
    
    def _send_overdue_notification(self, item: DeadlineItem):
        """Send an overdue notification."""
        if not self._notification_callback:
            return
        
        overdue_time = datetime.now() - item.deadline
        overdue_str = self._format_time_duration(overdue_time)
        
        notification = Notification(
            title=f"🚨 OVERDUE: {item.title}",
            message=f"This item was due {overdue_str} ago and needs immediate attention.",
            notification_type=NotificationType.TASK_OVERDUE,
            priority=NotificationPriority.CRITICAL,
            channels=[NotificationChannel.DESKTOP, NotificationChannel.MOBILE_PUSH, NotificationChannel.IN_APP],
            source_task_id=item.source_task_id,
            source_event_id=item.source_event_id,
            tags=item.tags.copy()
        )
        
        # Add actions
        notification.add_action("complete", "Mark Complete", "callback", {"action": "complete_deadline", "item_id": item.id}, is_primary=True)
        notification.add_action("reschedule", "Reschedule", "callback", {"action": "reschedule_deadline", "item_id": item.id})
        notification.add_action("view", "View Details", "callback", {"action": "view_deadline", "item_id": item.id})
        
        try:
            self._notification_callback(notification)
            item.record_interaction("overdue_notification_sent")
            logger.warning(f"Sent overdue notification for {item.title}")
            
        except Exception as e:
            logger.error(f"Failed to send overdue notification for {item.title}: {e}")
    
    def _update_item_statuses(self):
        """Update statuses for all monitored items."""
        for item in self.monitored_items.values():
            item.update_status()
    
    def _cleanup_old_items(self):
        """Clean up completed and cancelled items."""
        now = datetime.now()
        items_to_remove = []
        
        for item_id, item in self.monitored_items.items():
            should_remove = False
            
            if item.status == DeadlineStatus.COMPLETED:
                days_since_completion = (now - item.created_at).days
                if days_since_completion > self.config.cleanup_completed_after_days:
                    should_remove = True
            
            elif item.status == DeadlineStatus.CANCELLED:
                days_since_cancellation = (now - item.created_at).days
                if days_since_cancellation > self.config.cleanup_cancelled_after_days:
                    should_remove = True
            
            if should_remove:
                items_to_remove.append(item_id)
        
        # Remove old items
        for item_id in items_to_remove:
            self.remove_deadline_item(item_id)
        
        if items_to_remove:
            logger.info(f"Cleaned up {len(items_to_remove)} old deadline items")
            self.stats['last_cleanup'] = now
    
    def _format_time_duration(self, time_delta: timedelta) -> str:
        """Format a time delta as a human-readable string."""
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
                return f"{hours}h {minutes}m"
            else:
                return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours > 0:
                return f"{days}d {hours}h"
            else:
                return f"{days} day{'s' if days != 1 else ''}"
    
    def _save_state_if_needed(self):
        """Save state if enough time has passed."""
        now = datetime.now()
        if (now - self._last_save).total_seconds() >= self.config.save_state_interval_minutes * 60:
            self._save_state()
            self._last_save = now
    
    def _save_state(self):
        """Save the current state to file."""
        try:
            os.makedirs(os.path.dirname(self.config.data_file), exist_ok=True)
            
            # Prepare data for serialization
            items_data = {}
            for item_id, item in self.monitored_items.items():
                items_data[item_id] = {
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'deadline': item.deadline.isoformat() if item.deadline else None,
                    'created_at': item.created_at.isoformat(),
                    'item_type': item.item_type,
                    'priority': item.priority.value,
                    'tags': item.tags,
                    'status': item.status.value,
                    'completion_percentage': item.completion_percentage,
                    'reminder_intervals': item.reminder_intervals,
                    'custom_reminder_rule': item.custom_reminder_rule,
                    'source_task_id': item.source_task_id,
                    'source_event_id': item.source_event_id,
                    'source_project_id': item.source_project_id,
                    'assigned_to': item.assigned_to,
                    'reminders_sent': item.reminders_sent,
                    'last_reminder_sent': item.last_reminder_sent.isoformat() if item.last_reminder_sent else None,
                    'user_interactions': item.user_interactions
                }
            
            data = {
                'monitored_items': items_data,
                'stats': {
                    **self.stats,
                    'last_cleanup': self.stats['last_cleanup'].isoformat()
                },
                'config': {
                    'check_interval_seconds': self.config.check_interval_seconds,
                    'approaching_threshold_hours': self.config.approaching_threshold_hours,
                    'imminent_threshold_minutes': self.config.imminent_threshold_minutes,
                    'max_reminders_per_item': self.config.max_reminders_per_item
                },
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.config.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved deadline monitor state to {self.config.data_file}")
            
        except Exception as e:
            logger.error(f"Failed to save deadline monitor state: {e}")
    
    def _load_state(self):
        """Load state from file."""
        try:
            if not os.path.exists(self.config.data_file):
                return
            
            with open(self.config.data_file, 'r') as f:
                data = json.load(f)
            
            # Load monitored items
            items_data = data.get('monitored_items', {})
            for item_id, item_data in items_data.items():
                item = DeadlineItem(
                    id=item_data['id'],
                    title=item_data['title'],
                    description=item_data.get('description', ''),
                    deadline=datetime.fromisoformat(item_data['deadline']) if item_data.get('deadline') else None,
                    created_at=datetime.fromisoformat(item_data.get('created_at', datetime.now().isoformat())),
                    item_type=item_data.get('item_type', 'task'),
                    priority=NotificationPriority(item_data.get('priority', 'medium')),
                    tags=item_data.get('tags', []),
                    status=DeadlineStatus(item_data.get('status', 'upcoming')),
                    completion_percentage=item_data.get('completion_percentage', 0.0),
                    reminder_intervals=item_data.get('reminder_intervals', [10080, 1440, 240, 60, 15]),
                    custom_reminder_rule=item_data.get('custom_reminder_rule'),
                    source_task_id=item_data.get('source_task_id'),
                    source_event_id=item_data.get('source_event_id'),
                    source_project_id=item_data.get('source_project_id'),
                    assigned_to=item_data.get('assigned_to'),
                    reminders_sent=item_data.get('reminders_sent', 0),
                    last_reminder_sent=datetime.fromisoformat(item_data['last_reminder_sent']) if item_data.get('last_reminder_sent') else None,
                    user_interactions=item_data.get('user_interactions', [])
                )
                
                self.monitored_items[item_id] = item
            
            # Load stats
            stats_data = data.get('stats', {})
            self.stats.update(stats_data)
            if 'last_cleanup' in stats_data:
                self.stats['last_cleanup'] = datetime.fromisoformat(stats_data['last_cleanup'])
            
            logger.info(f"Loaded {len(self.monitored_items)} deadline items from {self.config.data_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load deadline monitor state: {e}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        now = datetime.now()
        
        # Count items by status
        status_counts = {}
        for status in DeadlineStatus:
            status_counts[status.value] = len(self.get_items_by_status(status))
        
        # Count items by time until deadline
        upcoming_24h = len([item for item in self.monitored_items.values() 
                           if item.deadline and 0 < item.minutes_until_deadline() < 1440])
        upcoming_week = len([item for item in self.monitored_items.values() 
                            if item.deadline and 0 < item.minutes_until_deadline() < 10080])
        
        return {
            'total_monitored_items': len(self.monitored_items),
            'status_breakdown': status_counts,
            'upcoming_24h': upcoming_24h,
            'upcoming_week': upcoming_week,
            'monitoring_active': self._monitoring_thread and self._monitoring_thread.is_alive(),
            'total_reminders_sent': self.stats['reminders_sent'],
            'overdue_items_detected': self.stats['overdue_items_detected'],
            'completed_items': self.stats['completed_items'],
            'last_cleanup': self.stats['last_cleanup'].isoformat() if isinstance(self.stats['last_cleanup'], datetime) else self.stats['last_cleanup'],
            'config': {
                'check_interval_seconds': self.config.check_interval_seconds,
                'max_reminders_per_item': self.config.max_reminders_per_item,
                'approaching_threshold_hours': self.config.approaching_threshold_hours
            }
        }


# Global deadline monitor instance
_deadline_monitor = None


def get_deadline_monitor(config: DeadlineMonitorConfig = None) -> DeadlineMonitor:
    """Get a singleton instance of the deadline monitor."""
    global _deadline_monitor
    if _deadline_monitor is None:
        _deadline_monitor = DeadlineMonitor(config)
    return _deadline_monitor