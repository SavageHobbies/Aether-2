#!/usr/bin/env python3
"""
Direct test of task extraction without going through __init__.py
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import directly from the module file
import importlib.util
spec = importlib.util.spec_from_file_location("extractor", "core/tasks/extractor.py")
extractor_module = importlib.util.module_from_spec(spec)

# We need to import types first
types_spec = importlib.util.spec_from_file_location("types", "core/tasks/types.py")
types_module = importlib.util.module_from_spec(types_spec)
sys.modules["types"] = types_module
types_spec.loader.exec_module(types_module)

# Now import extractor
sys.modules["extractor"] = extractor_module
spec.loader.exec_module(extractor_module)

TaskExtractor = extractor_module.TaskExtractor


def test_basic_extraction():
    """Test basic task extraction."""
    print("=== Testing Basic Task Extraction ===")
    
    extractor = TaskExtractor()
    
    test_texts = [
        "I need to call John about the project deadline by Friday.",
        "Don't forget to review the quarterly reports tomorrow.",
        "We should schedule a meeting with the client next week.",
        "I have to submit the proposal by end of day."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        result = extractor.extract_tasks_from_text(text)
        
        print(f"Success: {result.success}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Tasks found: {len(result.extracted_tasks)}")
        
        for j, task in enumerate(result.extracted_tasks):
            print(f"  Task {j+1}:")
            print(f"    Title: {task.title}")
            print(f"    Type: {task.task_type.value}")
            print(f"    Priority: {task.priority.value}")
            print(f"    Due Date: {task.due_date}")
            print(f"    Tags: {task.tags}")


if __name__ == "__main__":
    test_basic_extraction()