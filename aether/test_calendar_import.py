#!/usr/bin/env python3

"""
Simple test to isolate calendar import issues.
"""

try:
    print("Testing calendar_types import...")
    from core.integrations.calendar_types import CalendarEvent, CalendarSettings
    print("✓ calendar_types imported successfully")
    
    print("Testing google_calendar import...")
    from core.integrations.google_calendar import GoogleCalendarIntegration
    print("✓ google_calendar imported successfully")
    
    print("Testing integration __init__ import...")
    from core.integrations import GoogleCalendarIntegration as GCI
    print("✓ integrations __init__ imported successfully")
    
    print("All imports successful!")
    
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()