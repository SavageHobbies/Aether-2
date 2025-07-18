"""
Notification and reminder types and data structures.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field


class NotificationType(Enum):
    """Types of notifications."""
    TASK_REMINDER = "task_reminder"
    DEADLINE_WARNING = "deadline_warning"
    MEETING_REMINDER = "meeting_reminder"
    CALENDAR_CONFLICT = "calendar_conflict"
    TASK_OVERDUE = "task_overdue"
    PROJECT_UPDATE = "project_update"
    SYSTEM_ALERT = "system_alert"
    IDEA_SUGGESTION = "idea_suggestion"
    PROGRESS_UPDATE = "progress_update"
    ASSIGNMENT_NOTIFICATION = "assignment_notification"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Channels for delivering notifications."""
    DESKTOP = "desktop"
    MOBILE_PUSH = "mobile_push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    SYSTEM_TRAY = "system_tray"
    WEBHOOK = "webhook"
    SLACK = "slack"


class ReminderInterval(Enum):
    """Predefined reminder intervals."""
    MINUTES_5 = "5_minutes"
    MINUTES_15 = "15_minutes"
    MINUTES_30 = "30_minutes"
    HOUR_1 = "1_hour"
    HOURS_2 = "2_hours"
    HOURS_4 = "4_hours"
    HOURS_8 = "8_hours"
    DAY_1 = "1_day"
    DAYS_2 = "2_days"
    WEEK_1 = "1_week"
    CUSTOM = "custom"


class NotificationStatus(Enum):
    """Status of notifications."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DISMISSED = "dismissed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NotificationAction:
    """Represents an action that can be taken from a notification."""
    id: str
    label: str
    action_type: str  # "url", "callback", "dismiss", "snooze"
    action_data: Dict[str, Any] = field(default_factory=dict)
    is_primary: bool = False


@dataclass
class Notification:
    """Represents a notification to be sent to the user."""
    id: Optional[str] = None
    title: str = ""
    message: str = ""
    
    # Classification
    notification_type: NotificationType = NotificationType.SYSTEM_ALERT
    priority: NotificationPriority = NotificationPriority.MEDIUM
    
    # Delivery
    channels: List[NotificationChannel] = field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Content
    icon: Optional[str] = None
    image_url: Optional[str] = None
    sound: Optional[str] = None
    actions: List[NotificationAction] = field(default_factory=list)
    
    # Context
    source_task_id: Optional[str] = None
    source_event_id: Optional[str] = None
    source_conversation_id: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    # Status tracking
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        if not self.channels:
            self.channels = [NotificationChannel.IN_APP]
        
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
    
    def is_expired(self) -> bool:
        """Check if the notification has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def should_send_now(self) -> bool:
        """Check if the notification should be sent now."""
        if self.is_expired():
            return False
        
        if self.scheduled_time:
            return datetime.utcnow() >= self.scheduled_time
        
        return True
    
    def add_action(self, action_id: str, label: str, action_type: str, action_data: Dict[str, Any] = None, is_primary: bool = False):
        """Add an action to the notification."""
        action = NotificationAction(
            id=action_id,
            label=label,
            action_type=action_type,
            action_data=action_data or {},
            is_primary=is_primary
        )
        self.actions.append(action)


@dataclass
class ReminderRule:
    """Defines when and how to send reminders."""
    id: Optional[str] = None
    name: str = ""
    
    # Trigger conditions
    applies_to_types: List[str] = field(default_factory=list)  # task types, event types
    applies_to_priorities: List[NotificationPriority] = field(default_factory=list)
    applies_to_tags: List[str] = field(default_factory=list)
    
    # Timing
    intervals: List[ReminderInterval] = field(default_factory=list)
    custom_intervals_minutes: List[int] = field(default_factory=list)
    
    # Delivery preferences
    preferred_channels: List[NotificationChannel] = field(default_factory=list)
    quiet_hours_start: Optional[int] = None  # Hour of day (0-23)
    quiet_hours_end: Optional[int] = None    # Hour of day (0-23)
    weekend_enabled: bool = True
    
    # Content customization
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    
    # Conditions
    enabled: bool = True
    max_reminders: int = 3  # Maximum number of reminders per item
    
    def __post_init__(self):
        """Initialize default values."""
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
        
        if not self.preferred_channels:
            self.preferred_channels = [NotificationChannel.DESKTOP, NotificationChannel.IN_APP]
        
        if not self.intervals:
            self.intervals = [ReminderInterval.HOUR_1, ReminderInterval.DAY_1]
    
    def should_remind_for_item(self, item_type: str, priority: NotificationPriority, tags: List[str]) -> bool:
        """Check if this rule should create reminders for the given item."""
        if not self.enabled:
            return False
        
        # Check type filter
        if self.applies_to_types and item_type not in self.applies_to_types:
            return False
        
        # Check priority filter
        if self.applies_to_priorities and priority not in self.applies_to_priorities:
            return False
        
        # Check tags filter
        if self.applies_to_tags and not any(tag in tags for tag in self.applies_to_tags):
            return False
        
        return True
    
    def is_quiet_time(self, check_time: datetime = None) -> bool:
        """Check if the current time is within quiet hours."""
        if not check_time:
            check_time = datetime.now()
        
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False
        
        current_hour = check_time.hour
        
        # Handle quiet hours that span midnight
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_hour <= self.quiet_hours_end
        else:
            return current_hour >= self.quiet_hours_start or current_hour <= self.quiet_hours_end
    
    def get_reminder_times(self, due_time: datetime) -> List[datetime]:
        """Calculate when reminders should be sent for an item due at the given time."""
        reminder_times = []
        
        # Process standard intervals
        for interval in self.intervals:
            minutes_before = self._interval_to_minutes(interval)
            if minutes_before:
                reminder_time = due_time - timedelta(minutes=minutes_before)
                if reminder_time > datetime.utcnow():  # Only future reminders
                    reminder_times.append(reminder_time)
        
        # Process custom intervals
        for minutes in self.custom_intervals_minutes:
            reminder_time = due_time - timedelta(minutes=minutes)
            if reminder_time > datetime.utcnow():
                reminder_times.append(reminder_time)
        
        # Sort by time and limit to max_reminders
        reminder_times.sort()
        return reminder_times[:self.max_reminders]
    
    def _interval_to_minutes(self, interval: ReminderInterval) -> Optional[int]:
        """Convert reminder interval to minutes."""
        interval_map = {
            ReminderInterval.MINUTES_5: 5,
            ReminderInterval.MINUTES_15: 15,
            ReminderInterval.MINUTES_30: 30,
            ReminderInterval.HOUR_1: 60,
            ReminderInterval.HOURS_2: 120,
            ReminderInterval.HOURS_4: 240,
            ReminderInterval.HOURS_8: 480,
            ReminderInterval.DAY_1: 1440,
            ReminderInterval.DAYS_2: 2880,
            ReminderInterval.WEEK_1: 10080
        }
        return interval_map.get(interval)


@dataclass
class NotificationPreferences:
    """User preferences for notifications."""
    # Global settings
    notifications_enabled: bool = True
    quiet_hours_enabled: bool = True
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8     # 8 AM
    weekend_notifications: bool = True
    
    # Channel preferences
    desktop_notifications: bool = True
    mobile_push_notifications: bool = True
    email_notifications: bool = False
    sms_notifications: bool = False
    
    # Priority filtering
    minimum_priority: NotificationPriority = NotificationPriority.MEDIUM
    urgent_override_quiet_hours: bool = True
    critical_override_quiet_hours: bool = True
    
    # Reminder settings
    default_reminder_intervals: List[ReminderInterval] = field(default_factory=lambda: [
        ReminderInterval.HOUR_1, ReminderInterval.DAY_1
    ])
    max_reminders_per_item: int = 3
    snooze_duration_minutes: int = 15
    
    # Content preferences
    show_notification_previews: bool = True
    group_similar_notifications: bool = True
    auto_dismiss_after_minutes: int = 60
    
    # Sound and visual
    notification_sound: Optional[str] = "default"
    visual_indicators: bool = True
    badge_count: bool = True
    
    def should_send_notification(self, notification: Notification) -> bool:
        """Check if a notification should be sent based on user preferences."""
        if not self.notifications_enabled:
            return False
        
        # Check minimum priority
        priority_levels = {
            NotificationPriority.LOW: 1,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.HIGH: 3,
            NotificationPriority.URGENT: 4,
            NotificationPriority.CRITICAL: 5
        }
        
        if priority_levels.get(notification.priority, 0) < priority_levels.get(self.minimum_priority, 0):
            return False
        
        # Check quiet hours
        if self.quiet_hours_enabled and self._is_quiet_time():
            # Allow urgent/critical to override quiet hours
            if notification.priority == NotificationPriority.URGENT and self.urgent_override_quiet_hours:
                return True
            if notification.priority == NotificationPriority.CRITICAL and self.critical_override_quiet_hours:
                return True
            return False
        
        # Check weekend notifications
        if not self.weekend_notifications and datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        return True
    
    def _is_quiet_time(self) -> bool:
        """Check if current time is within quiet hours."""
        current_hour = datetime.now().hour
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_hour <= self.quiet_hours_end
        else:
            return current_hour >= self.quiet_hours_start or current_hour <= self.quiet_hours_end


@dataclass
class NotificationStats:
    """Statistics about notification delivery and engagement."""
    total_sent: int = 0
    total_delivered: int = 0
    total_read: int = 0
    total_dismissed: int = 0
    total_failed: int = 0
    
    # By channel
    desktop_sent: int = 0
    mobile_sent: int = 0
    email_sent: int = 0
    
    # By type
    task_reminders: int = 0
    meeting_reminders: int = 0
    deadline_warnings: int = 0
    
    # Engagement metrics
    average_read_time_seconds: float = 0.0
    click_through_rate: float = 0.0
    
    # Time periods
    last_24_hours: int = 0
    last_week: int = 0
    last_month: int = 0
    
    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate percentage."""
        if self.total_sent == 0:
            return 0.0
        return (self.total_delivered / self.total_sent) * 100
    
    @property
    def read_rate(self) -> float:
        """Calculate read rate percentage."""
        if self.total_delivered == 0:
            return 0.0
        return (self.total_read / self.total_delivered) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_sent == 0:
            return 0.0
        return (self.total_failed / self.total_sent) * 100


@dataclass
class NotificationTemplate:
    """Template for generating notifications."""
    id: str
    name: str
    notification_type: NotificationType
    
    # Template content
    title_template: str
    message_template: str
    
    # Default settings
    default_priority: NotificationPriority = NotificationPriority.MEDIUM
    default_channels: List[NotificationChannel] = field(default_factory=list)
    default_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Variables that can be used in templates
    supported_variables: List[str] = field(default_factory=list)
    
    def render(self, variables: Dict[str, Any]) -> Notification:
        """Render the template with the given variables to create a notification."""
        # Simple template rendering (could be enhanced with a proper template engine)
        title = self.title_template
        message = self.message_template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=self.notification_type,
            priority=self.default_priority,
            channels=self.default_channels.copy()
        )
        
        # Add default actions
        for action_data in self.default_actions:
            notification.add_action(**action_data)
        
        return notification