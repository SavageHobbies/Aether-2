#!/usr/bin/env python3

"""
Test direct import of google_calendar.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.getcwd())

try:
    print("Testing direct import...")
    
    # Try importing the module directly
    import core.integrations.google_calendar as gc
    print(f"Module imported: {gc}")
    print(f"Module file: {gc.__file__}")
    print(f"Module contents: {dir(gc)}")
    
    # Try to access the class
    if hasattr(gc, 'GoogleCalendarIntegration'):
        print("✓ GoogleCalendarIntegration found")
        integration = gc.GoogleCalendarIntegration()
        print("✓ Integration created")
    else:
        print("✗ GoogleCalendarIntegration not found")
        
        # Try to execute the file content manually
        print("Trying to execute file content...")
        with open('core/integrations/google_calendar.py', 'r') as f:
            content = f.read()
        
        # Create a new namespace and execute the content
        namespace = {}
        exec(content, namespace)
        print(f"Executed namespace: {list(namespace.keys())}")
        
        if 'GoogleCalendarIntegration' in namespace:
            print("✓ GoogleCalendarIntegration found in executed namespace")
        else:
            print("✗ GoogleCalendarIntegration not found in executed namespace")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()