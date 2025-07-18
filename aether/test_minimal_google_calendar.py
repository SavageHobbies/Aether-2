#!/usr/bin/env python3

"""
Test minimal Google Calendar class definition.
"""

from core.integrations.calendar_types import CalendarSettings
from core.tasks import TaskEntry

class GoogleCalendarIntegration:
    """Minimal Google Calendar integration."""
    
    def __init__(self, settings=None):
        self.settings = settings or CalendarSettings()
        print("GoogleCalendarIntegration initialized")

# Test the class
if __name__ == "__main__":
    integration = GoogleCalendarIntegration()
    print("✓ GoogleCalendarIntegration created successfully")