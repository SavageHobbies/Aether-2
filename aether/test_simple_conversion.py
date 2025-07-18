#!/usr/bin/env python3
"""
Simple test for idea conversion system.
"""

import asyncio
import sys
from core.ideas import get_idea_processor, get_idea_converter, ConversionType
from core.ai import initialize_ai_provider
from core.database import initialize_database
from core.database.vector_store import initialize_vector_store

async def main():
    print("Starting Simple Conversion Test")
    
    try:
        # Initialize systems
        print("Initializing systems...")
        initialize_ai_provider("simple")
        db_manager = initialize_database("sqlite:///test_simple_conversion.db")
        await db_manager.create_tables_async()
        initialize_vector_store("simple")
        print("✓ Systems initialized")
        
        # Test basic conversion
        print("\nTesting basic conversion...")
        idea_processor = get_idea_processor()
        converter = get_idea_converter()
        
        # Create a simple idea
        idea = await idea_processor.capture_idea(
            "Create a simple task management system",
            source="test"
        )
        print(f"✓ Created idea: {idea.content}")
        
        # Convert to task
        result = await converter.convert_idea_to_task(idea)
        print(f"✓ Conversion result: success={result.success}")
        
        if result.success:
            print(f"✓ Created {len(result.tasks)} tasks")
            for task in result.tasks:
                print(f"  - {task.title}")
        else:
            print(f"✗ Error: {result.error_message}")
        
        print("\nSimple Conversion Test Completed Successfully")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())