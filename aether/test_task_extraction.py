#!/usr/bin/env python3
"""
Test script for task identification and extraction system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from core.tasks.extractor import TaskExtractor
from core.tasks.task_types import TaskPriority, TaskStatus, TaskType


def test_basic_task_extraction():
    """Test basic task extraction functionality."""
    print("=== Testing Basic Task Extraction ===")
    
    extractor = TaskExtractor()
    
    # Test cases with different types of task expressions
    test_texts = [
        "I need to call John about the project deadline by Friday.",
        "Don't forget to review the quarterly reports tomorrow.",
        "We should schedule a meeting with the client next week.",
        "I have to submit the proposal by end of day.",
        "Let's research the new marketing strategies for Q2.",
        "Remember to check the budget numbers before the presentation.",
        "I will create a presentation for the board meeting.",
        "We need to decide on the vendor selection by Monday."
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
            print(f"    Priority Score: {task.priority_score:.2f}")
            print(f"    Tags: {task.tags}")
        
        if result.suggestions:
            print(f"  Suggestions: {result.suggestions}")


def test_priority_detection():
    """Test priority detection in task extraction."""
    print("\n=== Testing Priority Detection ===")
    
    extractor = TaskExtractor()
    
    priority_tests = [
        ("This is urgent - I need to call the client immediately!", TaskPriority.URGENT),
        ("Important: Review the contract by tomorrow.", TaskPriority.HIGH),
        ("I should probably check the email sometime.", TaskPriority.MEDIUM),
        ("Maybe we could consider updating the website eventually.", TaskPriority.LOW),
        ("ASAP: Fix the critical bug in production!", TaskPriority.URGENT),
        ("We need to plan the next sprint.", TaskPriority.MEDIUM)
    ]
    
    for text, expected_priority in priority_tests:
        print(f"\nText: {text}")
        result = extractor.extract_tasks_from_text(text)
        
        if result.extracted_tasks:
            actual_priority = result.extracted_tasks[0].priority
            print(f"Expected: {expected_priority.value}, Got: {actual_priority.value}")
            print(f"Match: {'✓' if actual_priority == expected_priority else '✗'}")
        else:
            print("No tasks extracted")


def test_due_date_extraction():
    """Test due date extraction from text."""
    print("\n=== Testing Due Date Extraction ===")
    
    extractor = TaskExtractor()
    
    date_tests = [
        "I need to finish the report by tomorrow.",
        "Call the client in 3 days.",
        "Schedule the meeting for next week.",
        "Submit the proposal by Friday.",
        "Review the documents today.",
        "Prepare the presentation in 2 weeks."
    ]
    
    for text in date_tests:
        print(f"\nText: {text}")
        result = extractor.extract_tasks_from_text(text)
        
        if result.extracted_tasks:
            task = result.extracted_tasks[0]
            if task.due_date:
                days_from_now = (task.due_date - datetime.now()).days
                print(f"Due date: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
                print(f"Days from now: {days_from_now}")
            else:
                print("No due date extracted")
        else:
            print("No tasks extracted")


def test_task_type_classification():
    """Test task type classification."""
    print("\n=== Testing Task Type Classification ===")
    
    extractor = TaskExtractor()
    
    type_tests = [
        ("Schedule a meeting with the team", TaskType.MEETING),
        ("Research the competitor analysis", TaskType.RESEARCH),
        ("Review the quarterly budget", TaskType.REVIEW),
        ("Decide on the new hire", TaskType.DECISION),
        ("Submit the report by deadline", TaskType.DEADLINE),
        ("Remember to call mom", TaskType.REMINDER),
        ("Create a new project plan", TaskType.ACTION)
    ]
    
    for text, expected_type in type_tests:
        print(f"\nText: {text}")
        result = extractor.extract_tasks_from_text(text)
        
        if result.extracted_tasks:
            actual_type = result.extracted_tasks[0].task_type
            print(f"Expected: {expected_type.value}, Got: {actual_type.value}")
            print(f"Match: {'✓' if actual_type == expected_type else '✗'}")
        else:
            print("No tasks extracted")


def test_complex_conversation():
    """Test extraction from a complex conversation."""
    print("\n=== Testing Complex Conversation ===")
    
    extractor = TaskExtractor()
    
    conversation = """
    Hi team, I wanted to follow up on our discussion yesterday. We have several action items:
    
    First, I need to call the client about the project timeline by end of week. This is urgent 
    because they're waiting for our response.
    
    Second, we should schedule a review meeting for next Tuesday to go over the quarterly results.
    Don't forget to prepare the presentation slides beforehand.
    
    Also, someone needs to research the new compliance requirements that came out last month.
    This isn't urgent but should be done in the next two weeks.
    
    Finally, I have to submit the budget proposal by Friday - this is a hard deadline from finance.
    
    Let me know if you have any questions!
    """
    
    print("Conversation text:")
    print(conversation)
    print("\n" + "="*50)
    
    result = extractor.extract_tasks_from_text(
        conversation,
        conversation_id="test_conv_001",
        source_context={"meeting_id": "weekly_standup"}
    )
    
    print(f"Extraction successful: {result.success}")
    print(f"Overall confidence: {result.confidence_score:.2f}")
    print(f"Processing time: {result.processing_time_ms:.1f}ms")
    print(f"Total tasks found: {len(result.extracted_tasks)}")
    
    for i, task in enumerate(result.extracted_tasks, 1):
        print(f"\nTask {i}:")
        print(f"  Title: {task.title}")
        print(f"  Description: {task.description}")
        print(f"  Type: {task.task_type.value}")
        print(f"  Priority: {task.priority.value}")
        print(f"  Due Date: {task.due_date}")
        print(f"  Urgency Score: {task.urgency_score:.2f}")
        print(f"  Importance Score: {task.importance_score:.2f}")
        print(f"  Tags: {task.tags}")
        print(f"  Source: {task.source_conversation_id}")
    
    if result.suggestions:
        print(f"\nSuggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")


def test_dependency_analysis():
    """Test task dependency analysis."""
    print("\n=== Testing Dependency Analysis ===")
    
    extractor = TaskExtractor()
    
    # Create some related tasks
    text = """
    I need to create the project proposal first, then we can review it with the team.
    After the review, we should present it to the client and get their approval.
    """
    
    result = extractor.extract_tasks_from_text(text)
    
    if result.extracted_tasks:
        print(f"Found {len(result.extracted_tasks)} tasks:")
        for i, task in enumerate(result.extracted_tasks):
            print(f"  {i+1}. {task.title}")
        
        # Analyze dependencies
        dependencies = extractor.analyze_task_dependencies(result.extracted_tasks)
        
        print(f"\nFound {len(dependencies)} potential dependencies:")
        for dep in dependencies:
            print(f"  - {dep.description}")
            print(f"    Type: {dep.dependency_type.value}")


def test_performance():
    """Test performance with larger text."""
    print("\n=== Testing Performance ===")
    
    extractor = TaskExtractor()
    
    # Create a longer text with multiple tasks
    long_text = """
    This is a comprehensive project update with multiple action items and deadlines.
    
    First, I need to complete the market research analysis by next Friday. This is critical
    for our Q2 planning session.
    
    Second, we should schedule individual one-on-ones with each team member this week.
    Don't forget to prepare the performance review templates beforehand.
    
    Third, I have to review and approve the budget allocations by Wednesday. The finance
    team is waiting for our input on the quarterly projections.
    
    Fourth, we need to decide on the new vendor selection by end of month. This decision
    will impact our operational costs significantly.
    
    Fifth, someone should research the latest industry trends and prepare a summary report.
    This isn't urgent but would be valuable for strategic planning.
    
    Sixth, I will create a comprehensive project timeline and share it with stakeholders.
    This needs to be done before the board meeting next week.
    
    Seventh, we must submit the compliance documentation by the regulatory deadline.
    This is non-negotiable and has legal implications.
    
    Finally, let's organize a team building event for next month to boost morale.
    """ * 3  # Repeat 3 times to make it longer
    
    print(f"Text length: {len(long_text)} characters")
    print(f"Word count: {len(long_text.split())} words")
    
    result = extractor.extract_tasks_from_text(long_text)
    
    print(f"\nResults:")
    print(f"  Success: {result.success}")
    print(f"  Tasks found: {len(result.extracted_tasks)}")
    print(f"  Processing time: {result.processing_time_ms:.1f}ms")
    print(f"  Confidence: {result.confidence_score:.2f}")
    
    # Show task distribution by type and priority
    type_counts = {}
    priority_counts = {}
    
    for task in result.extracted_tasks:
        type_counts[task.task_type.value] = type_counts.get(task.task_type.value, 0) + 1
        priority_counts[task.priority.value] = priority_counts.get(task.priority.value, 0) + 1
    
    print(f"\nTask types: {type_counts}")
    print(f"Priorities: {priority_counts}")


def main():
    """Run all tests."""
    print("Starting Task Extraction System Tests")
    print("=" * 60)
    
    try:
        test_basic_task_extraction()
        test_priority_detection()
        test_due_date_extraction()
        test_task_type_classification()
        test_complex_conversation()
        test_dependency_analysis()
        test_performance()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())