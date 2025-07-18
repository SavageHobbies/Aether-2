#!/usr/bin/env python3
"""
Minimal test for converter imports.
"""

try:
    print("Testing enum import...")
    from enum import Enum
    
    print("Testing dataclass import...")
    from dataclasses import dataclass, field
    
    print("Testing datetime import...")
    from datetime import datetime, timedelta
    
    print("Testing typing import...")
    from typing import Any, Dict, List, Optional, Union
    
    print("Testing uuid import...")
    import uuid
    
    print("Testing logging import...")
    import logging
    
    print("Testing AI provider import...")
    from core.ai import get_ai_provider
    
    print("Testing logger import...")
    from shared.utils.logging import get_logger
    
    print("Testing types import...")
    # This is where the circular import might happen
    import sys
    import importlib.util
    
    # Load types module directly
    spec = importlib.util.spec_from_file_location("types", "core/ideas/types.py")
    types_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(types_module)
    
    IdeaEntry = types_module.IdeaEntry
    IdeaCategory = types_module.IdeaCategory
    IdeaPriority = types_module.IdeaPriority
    
    print("All imports successful!")
    
    # Now test the enum definition
    class ConversionType(Enum):
        TASK = "task"
        CALENDAR_EVENT = "calendar_event"
        PROJECT = "project"
    
    print("ConversionType enum created:", ConversionType.TASK)
    
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()