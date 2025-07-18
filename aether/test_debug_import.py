#!/usr/bin/env python3

"""
Debug import issues.
"""

try:
    print("Importing calendar_types...")
    from core.integrations.calendar_types import CalendarEvent
    print("✓ CalendarEvent imported")
    
    print("Importing google_calendar module...")
    import core.integrations.google_calendar as gc_module
    print("✓ google_calendar module imported")
    
    print("Module contents:", dir(gc_module))
    
    print("Checking for GoogleCalendarIntegration...")
    if hasattr(gc_module, 'GoogleCalendarIntegration'):
        print("✓ GoogleCalendarIntegration found")
    else:
        print("✗ GoogleCalendarIntegration not found")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()