"""
Simple Google Calendar integration for testing.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from shared.utils.logging import get_logger
from .calendar_types import CalendarEvent, CalendarSettings

logger = get_logger(__name__)


class GoogleCalendarIntegration:
    """Simple Google Calendar integration."""
    
    def __init__(self, settings: Optional[CalendarSettings] = None):
        """Initialize Google Calendar integration."""
        self.settings = settings or CalendarSettings()
        logger.info("Google Calendar integration initialized")
    
    def get_auth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL."""
        return f"https://accounts.google.com/o/oauth2/v2/auth?client_id={self.settings.client_id}&redirect_uri={redirect_uri}"
    
    async def get_events(self, calendar_id: str = "primary") -> List[CalendarEvent]:
        """Get events from Google Calendar (mock implementation)."""
        # Mock implementation for testing
        return [
            CalendarEvent(
                title="Mock Event 1",
                start_time=datetime.utcnow() + timedelta(hours=1)
            ),
            CalendarEvent(
                title="Mock Event 2", 
                start_time=datetime.utcnow() + timedelta(hours=2)
            )
        ]


def get_google_calendar_integration(settings: Optional[CalendarSettings] = None) -> GoogleCalendarIntegration:
    """Get Google Calendar integration instance."""
    return GoogleCalendarIntegration(settings)