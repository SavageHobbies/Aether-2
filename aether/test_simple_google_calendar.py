#!/usr/bin/env python3

"""
Test simple Google Calendar integration.
"""

import asyncio
from core.integrations.google_calendar_simple import GoogleCalendarIntegration
from core.integrations.calendar_types import CalendarSettings

async def test_simple_integration():
    """Test simple Google Calendar integration."""
    print("Testing simple Google Calendar integration...")
    
    # Create settings
    settings = CalendarSettings(
        client_id="test_client_id",
        client_secret="test_client_secret"
    )
    
    # Create integration
    integration = GoogleCalendarIntegration(settings)
    
    # Test auth URL generation
    auth_url = integration.get_auth_url("http://localhost:8000/callback")
    print(f"Auth URL: {auth_url}")
    
    # Test getting events
    events = await integration.get_events()
    print(f"Retrieved {len(events)} events:")
    for event in events:
        print(f"  - {event.title} at {event.start_time}")
    
    print("✓ Simple Google Calendar integration works")

if __name__ == "__main__":
    asyncio.run(test_simple_integration())