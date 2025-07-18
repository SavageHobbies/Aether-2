"""Google Calendar integration for Aether AI Companion."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class GoogleCalendarIntegration:
    """
    Google Calendar integration for Aether AI Companion.
    
    Provides OAuth 2.0 authentication and calendar synchronization.
    """
    
    def __init__(self, settings=None):
        """Initialize Google Calendar integration."""
        self.settings = settings or {}
        
        # Google Calendar API endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.calendar_api_base = "https://www.googleapis.com/calendar/v3"
        
        # OAuth scopes
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
        
        logger.info("Google Calendar integration initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    def get_auth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Get Google OAuth authorization URL.
        
        Args:
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for security
        
        Returns:
            Authorization URL
        """
        client_id = getattr(self.settings, 'client_id', None) if self.settings else None
        params = {
            'client_id': client_id or 'test_client_id',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        if state:
            params['state'] = state
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Get list of user's calendars (mock implementation).
        
        Returns:
            List of calendar data
        """
        # Mock implementation for testing
        return [
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
    
    async def get_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 250
    ) -> List[Dict[str, Any]]:
        """
        Get events from Google Calendar (mock implementation).
        
        Args:
            calendar_id: Calendar ID to fetch from
            time_min: Minimum time for events
            time_max: Maximum time for events
            max_results: Maximum number of events to fetch
        
        Returns:
            List of event dictionaries
        """
        # Mock implementation for testing
        base_time = datetime.now()
        return [
            {
                'id': 'event_1',
                'summary': 'Team Meeting',
                'start': {'dateTime': (base_time + timedelta(hours=1)).isoformat()},
                'end': {'dateTime': (base_time + timedelta(hours=2)).isoformat()},
                'status': 'confirmed'
            },
            {
                'id': 'event_2',
                'summary': 'Project Review',
                'start': {'dateTime': (base_time + timedelta(hours=3)).isoformat()},
                'end': {'dateTime': (base_time + timedelta(hours=4)).isoformat()},
                'status': 'confirmed'
            }
        ]
    
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an event in Google Calendar (mock implementation).
        
        Args:
            event_data: Event data to create
        
        Returns:
            Created event data
        """
        # Mock implementation for testing
        event_data['id'] = f"created_event_{datetime.now().timestamp()}"
        logger.info(f"Created event: {event_data.get('summary', 'Untitled')}")
        return event_data
    
    async def create_event_from_task(self, task) -> Optional[Dict[str, Any]]:
        """
        Create a calendar event from a task.
        
        Args:
            task: Task object to convert to calendar event
        
        Returns:
            Created event data or None if creation failed
        """
        try:
            # Determine event timing
            start_time = getattr(task, 'due_date', None) or (datetime.now() + timedelta(hours=1))
            duration_minutes = getattr(task, 'estimated_duration_minutes', None) or 60
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Create event data
            event_data = {
                'summary': getattr(task, 'title', 'Task'),
                'description': f"Task: {getattr(task, 'description', '')}\\n\\nCreated from Aether AI Companion",
                'start': {'dateTime': start_time.isoformat()},
                'end': {'dateTime': end_time.isoformat()},
                'source': 'aether'
            }
            
            # Create event
            created_event = await self.create_event(event_data)
            logger.info(f"Created calendar event from task: {getattr(task, 'title', 'Unknown task')}")
            return created_event
            
        except Exception as e:
            logger.error(f"Failed to create calendar event from task: {e}")
            return None
    
    async def sync_events(self, calendar_id: str = "primary") -> Dict[str, Any]:
        """
        Synchronize events (mock implementation).
        
        Args:
            calendar_id: Calendar ID to sync
        
        Returns:
            Sync result data
        """
        # Mock implementation for testing
        return {
            'status': 'success',
            'calendar_id': calendar_id,
            'events_synced': 2,
            'events_created': 1,
            'events_updated': 1,
            'events_deleted': 0,
            'conflicts_detected': 0,
            'errors': []
        }


def get_google_calendar_integration(settings=None):
    """
    Get Google Calendar integration instance.
    
    Args:
        settings: Optional calendar settings
    
    Returns:
        GoogleCalendarIntegration instance
    """
    return GoogleCalendarIntegration(settings)


if __name__ == "__main__":
    print("GoogleCalendarIntegration defined:", "GoogleCalendarIntegration" in globals())
    integration = GoogleCalendarIntegration()
    print("Integration created successfully")