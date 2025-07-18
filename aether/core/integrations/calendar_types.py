"""
Calendar integration types and data structures.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import uuid


class CalendarEventType(Enum):
    """Types of calendar events."""
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    DEADLINE = "deadline"
    APPOINTMENT = "appointment"
    PERSONAL = "personal"
    WORK = "work"
    OTHER = "other"


class CalendarEventStatus(Enum):
    """Status of calendar events."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class CalendarConflictType(Enum):
    """Types of calendar conflicts."""
    OVERLAP = "overlap"
    DOUBLE_BOOKING = "double_booking"
    SCHEDULING_CONFLICT = "scheduling_conflict"
    RESOURCE_CONFLICT = "resource_conflict"


class CalendarSyncStatus(Enum):
    """Status of calendar synchronization."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CONFLICT = "conflict"
    UNAUTHORIZED = "unauthorized"


@dataclass
class CalendarAttendee:
    """Calendar event attendee."""
    email: str
    name: Optional[str] = None
    response_status: str = "needsAction"  # needsAction, declined, tentative, accepted
    optional: bool = False
    organizer: bool = False


@dataclass
class CalendarEvent:
    """A calendar event."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    
    # Timing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    all_day: bool = False
    timezone: str = "UTC"
    
    # Location and details
    location: Optional[str] = None
    event_type: CalendarEventType = CalendarEventType.OTHER
    status: CalendarEventStatus = CalendarEventStatus.CONFIRMED
    
    # Attendees and organization
    attendees: List[CalendarAttendee] = field(default_factory=list)
    organizer_email: Optional[str] = None
    
    # Recurrence
    recurring: bool = False
    recurrence_rule: Optional[str] = None  # RRULE format
    
    # Integration metadata
    google_event_id: Optional[str] = None
    calendar_id: str = "primary"
    source: str = "aether"  # aether, google, manual
    
    # Aether-specific metadata
    task_id: Optional[str] = None
    conversation_id: Optional[str] = None
    idea_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    synced_at: Optional[datetime] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.end_time is None:
            # Default to 1 hour duration
            self.end_time = self.start_time + timedelta(hours=1)
    
    @property
    def duration_minutes(self) -> int:
        """Get event duration in minutes."""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 60
    
    def overlaps_with(self, other: 'CalendarEvent') -> bool:
        """Check if this event overlaps with another event."""
        if self.all_day or other.all_day:
            # For all-day events, check date overlap
            self_date = self.start_time.date()
            other_date = other.start_time.date()
            return self_date == other_date
        
        # Check time overlap
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)
    
    def to_google_event(self) -> Dict[str, Any]:
        """Convert to Google Calendar API event format."""
        event = {
            'summary': self.title,
            'description': self.description,
            'location': self.location,
            'status': self.status.value,
        }
        
        if self.all_day:
            event['start'] = {'date': self.start_time.date().isoformat()}
            event['end'] = {'date': self.end_time.date().isoformat()}
        else:
            event['start'] = {
                'dateTime': self.start_time.isoformat(),
                'timeZone': self.timezone
            }
            event['end'] = {
                'dateTime': self.end_time.isoformat(),
                'timeZone': self.timezone
            }
        
        if self.attendees:
            event['attendees'] = [
                {
                    'email': attendee.email,
                    'displayName': attendee.name,
                    'responseStatus': attendee.response_status,
                    'optional': attendee.optional
                }
                for attendee in self.attendees
            ]
        
        if self.recurring and self.recurrence_rule:
            event['recurrence'] = [self.recurrence_rule]
        
        return event
    
    @classmethod
    def from_google_event(cls, google_event: Dict[str, Any], calendar_id: str = "primary") -> 'CalendarEvent':
        """Create CalendarEvent from Google Calendar API event."""
        # Parse start and end times
        start_data = google_event.get('start', {})
        end_data = google_event.get('end', {})
        
        if 'date' in start_data:
            # All-day event
            start_time = datetime.fromisoformat(start_data['date']).replace(hour=0, minute=0)
            end_time = datetime.fromisoformat(end_data['date']).replace(hour=23, minute=59)
            all_day = True
            timezone = "UTC"
        else:
            # Timed event
            start_time = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
            all_day = False
            timezone = start_data.get('timeZone', 'UTC')
        
        # Parse attendees
        attendees = []
        for attendee_data in google_event.get('attendees', []):
            attendees.append(CalendarAttendee(
                email=attendee_data['email'],
                name=attendee_data.get('displayName'),
                response_status=attendee_data.get('responseStatus', 'needsAction'),
                optional=attendee_data.get('optional', False),
                organizer=attendee_data.get('organizer', False)
            ))
        
        # Determine event type from title/description
        title = google_event.get('summary', '').lower()
        event_type = CalendarEventType.OTHER
        if any(word in title for word in ['meeting', 'call', 'conference']):
            event_type = CalendarEventType.MEETING
        elif any(word in title for word in ['task', 'todo', 'work']):
            event_type = CalendarEventType.TASK
        elif any(word in title for word in ['reminder', 'remind']):
            event_type = CalendarEventType.REMINDER
        elif any(word in title for word in ['deadline', 'due']):
            event_type = CalendarEventType.DEADLINE
        
        return cls(
            id=str(uuid.uuid4()),
            google_event_id=google_event['id'],
            title=google_event.get('summary', ''),
            description=google_event.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            timezone=timezone,
            location=google_event.get('location'),
            event_type=event_type,
            status=CalendarEventStatus(google_event.get('status', 'confirmed')),
            attendees=attendees,
            organizer_email=google_event.get('organizer', {}).get('email'),
            recurring=bool(google_event.get('recurrence')),
            recurrence_rule=google_event.get('recurrence', [None])[0],
            calendar_id=calendar_id,
            source="google",
            created_at=datetime.fromisoformat(google_event['created'].replace('Z', '+00:00')) if 'created' in google_event else datetime.utcnow(),
            updated_at=datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00')) if 'updated' in google_event else datetime.utcnow(),
            synced_at=datetime.utcnow()
        )


@dataclass
class CalendarConflict:
    """A calendar scheduling conflict."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: CalendarConflictType = CalendarConflictType.OVERLAP
    
    # Conflicting events
    event1: CalendarEvent = None
    event2: CalendarEvent = None
    
    # Conflict details
    overlap_start: Optional[datetime] = None
    overlap_end: Optional[datetime] = None
    overlap_duration_minutes: int = 0
    
    # Resolution
    resolved: bool = False
    resolution_action: Optional[str] = None  # reschedule, cancel, ignore
    resolved_at: Optional[datetime] = None
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)
    severity: str = "medium"  # low, medium, high, critical
    
    def __post_init__(self):
        """Calculate overlap details."""
        if self.event1 and self.event2 and self.event1.overlaps_with(self.event2):
            self.overlap_start = max(self.event1.start_time, self.event2.start_time)
            self.overlap_end = min(self.event1.end_time, self.event2.end_time)
            if self.overlap_start and self.overlap_end:
                self.overlap_duration_minutes = int((self.overlap_end - self.overlap_start).total_seconds() / 60)
    
    @property
    def description(self) -> str:
        """Get human-readable conflict description."""
        if self.conflict_type == CalendarConflictType.OVERLAP:
            return f"Events '{self.event1.title}' and '{self.event2.title}' overlap for {self.overlap_duration_minutes} minutes"
        elif self.conflict_type == CalendarConflictType.DOUBLE_BOOKING:
            return f"Double booking detected: '{self.event1.title}' and '{self.event2.title}'"
        else:
            return f"Scheduling conflict between '{self.event1.title}' and '{self.event2.title}'"


@dataclass
class CalendarSyncResult:
    """Result of calendar synchronization operation."""
    status: CalendarSyncStatus = CalendarSyncStatus.SUCCESS
    
    # Sync statistics
    events_synced: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    
    # Conflicts and errors
    conflicts_detected: List[CalendarConflict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Timing
    sync_started_at: datetime = field(default_factory=datetime.utcnow)
    sync_completed_at: Optional[datetime] = None
    sync_duration_seconds: float = 0.0
    
    # Metadata
    calendar_id: str = "primary"
    sync_direction: str = "bidirectional"  # to_google, from_google, bidirectional
    
    def mark_completed(self):
        """Mark sync as completed and calculate duration."""
        self.sync_completed_at = datetime.utcnow()
        self.sync_duration_seconds = (self.sync_completed_at - self.sync_started_at).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of sync operation."""
        total_operations = self.events_created + self.events_updated + self.events_deleted
        if total_operations == 0:
            return 1.0
        
        failed_operations = len(self.errors)
        return max(0.0, (total_operations - failed_operations) / total_operations)
    
    @property
    def summary(self) -> str:
        """Get human-readable sync summary."""
        return (f"Sync {self.status.value}: {self.events_synced} events processed, "
                f"{self.events_created} created, {self.events_updated} updated, "
                f"{self.events_deleted} deleted, {len(self.conflicts_detected)} conflicts, "
                f"{len(self.errors)} errors")


@dataclass
class CalendarSettings:
    """Calendar integration settings."""
    # Authentication
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    
    # Sync settings
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = 15
    sync_direction: str = "bidirectional"
    
    # Calendar selection
    primary_calendar_id: str = "primary"
    synced_calendars: List[str] = field(default_factory=lambda: ["primary"])
    
    # Conflict resolution
    auto_resolve_conflicts: bool = False
    conflict_resolution_strategy: str = "prompt"  # prompt, reschedule, ignore
    
    # Event creation
    default_event_duration_minutes: int = 60
    default_reminder_minutes: int = 15
    create_events_from_tasks: bool = True
    create_events_from_conversations: bool = True
    
    # Privacy and filtering
    sync_private_events: bool = True
    event_title_filter: List[str] = field(default_factory=list)
    
    # Metadata
    last_sync_at: Optional[datetime] = None
    sync_enabled: bool = True