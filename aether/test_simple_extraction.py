#!/usr/bin/env python3
"""
Simple test of task extraction functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.tasks.extractor import TaskExtractor


def test_simple_extraction():
    """Test basic task extraction."""
    print("=== Simple Task Extraction Test ===")
    
    extractor = TaskExtractor()
    
    # Test simple task extraction
    text = "I need to call John about the project deadline by Friday."
    result = extractor.extract_tasks_from_text(text)
    
    print(f"Text: {text}")
    print(f"Success: {result.success}")
    print(f"Tasks found: {len(result.extracted_tasks)}")
    
    if result.extracted_tasks:
        task = result.extracted_tasks[0]
        print(f"Task title: {task.title}")
        print(f"Task type: {task.task_type.value}")
        print(f"Priority: {task.priority.value}")
        print(f"Due date: {task.due_date}")
        print(f"Tags: {task.tags}")
        print(f"Urgency score: {task.urgency_score}")
        print(f"Importance score: {task.importance_score}")
    
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Processing time: {result.processing_time_ms:.1f}ms")
    
    if result.suggestions:
        print("Suggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")


if __name__ == "__main__":
    test_simple_extraction()