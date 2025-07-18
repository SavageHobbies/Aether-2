#!/usr/bin/env python3

"""
Test individual imports from google_calendar.py
"""

try:
    print("Testing asyncio...")
    import asyncio
    print("✓ asyncio")
    
    print("Testing json...")
    import json
    print("✓ json")
    
    print("Testing logging...")
    import logging
    print("✓ logging")
    
    print("Testing datetime...")
    from datetime import datetime, timedelta
    print("✓ datetime")
    
    print("Testing typing...")
    from typing import Any, Dict, List, Optional, Tuple
    print("✓ typing")
    
    print("Testing urllib.parse...")
    from urllib.parse import urlencode, parse_qs
    print("✓ urllib.parse")
    
    print("Testing aiohttp...")
    import aiohttp
    print("✓ aiohttp")
    
    print("Testing sqlalchemy...")
    from sqlalchemy.ext.asyncio import AsyncSession
    print("✓ sqlalchemy")
    
    print("Testing shared.utils.logging...")
    from shared.utils.logging import get_logger
    print("✓ shared.utils.logging")
    
    print("Testing core.database...")
    from core.database import get_database_manager
    print("✓ core.database")
    
    print("Testing core.tasks.types...")
    from core.tasks.types import TaskEntry
    print("✓ core.tasks.types")
    
    print("Testing calendar_types imports...")
    from core.integrations.calendar_types import CalendarEvent
    print("✓ CalendarEvent")
    
    from core.integrations.calendar_types import CalendarConflict
    print("✓ CalendarConflict")
    
    from core.integrations.calendar_types import CalendarSyncResult
    print("✓ CalendarSyncResult")
    
    from core.integrations.calendar_types import CalendarSettings
    print("✓ CalendarSettings")
    
    from core.integrations.calendar_types import CalendarEventType
    print("✓ CalendarEventType")
    
    from core.integrations.calendar_types import CalendarConflictType
    print("✓ CalendarConflictType")
    
    from core.integrations.calendar_types import CalendarSyncStatus
    print("✓ CalendarSyncStatus")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()