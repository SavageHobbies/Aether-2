#!/usr/bin/env python3

"""
Simple test for calendar integration.
"""

import asyncio
from datetime import datetime, timedelta

# Test basic imports
from core.integrations.calendar_types import CalendarEvent, CalendarSettings

async def test_basic_functionality():
    """Test basic calendar functionality."""
    print("Testing basic calendar functionality...")
    
    # Test CalendarEvent creation
    event = CalendarEvent(
        title="Test Meeting",
        description="This is a test meeting",
        start_time=datetime.utcnow() + timedelta(hours=1)
    )
    
    print(f"Created event: {event.title}")
    print(f"Start time: {event.start_time}")
    print(f"Duration: {event.duration_minutes} minutes")
    
    # Test CalendarSettings
    settings = CalendarSettings(
        client_id="test_client_id",
        sync_interval_minutes=30
    )
    
    print(f"Settings client ID: {settings.client_id}")
    print(f"Sync interval: {settings.sync_interval_minutes} minutes")
    
    print("✓ Basic calendar functionality works")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())