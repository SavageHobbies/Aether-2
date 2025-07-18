#!/usr/bin/env python3
"""
Test script for the idea-to-action conversion system.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from core.ideas import (
    IdeaProcessor, IdeaToActionConverter, ConversionType,
    IdeaCategory, IdeaPriority, TaskEntry, CalendarEvent, ProjectEntry,
    get_idea_processor, get_idea_converter
)
from core.ai import initialize_ai_provider
from core.database import initialize_database
from core.database.vector_store import initialize_vector_store
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_idea_to_task_conversion():
    """Test converting ideas to tasks."""
    print("\n=== Testing Idea to Task Conversion ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create test ideas for task conversion
    test_ideas_data = [
        {
            "content": "Build a customer analytics dashboard with real-time metrics, user segmentation, and automated reporting features",
            "category": IdeaCategory.TECHNICAL,
            "priority": IdeaPriority.HIGH
        },
        {
            "content": "Launch a marketing campaign for our new product targeting millennials through social media channels",
            "category": IdeaCategory.MARKETING,
            "priority": IdeaPriority.MEDIUM
        },
        {
            "content": "Organize team building workshop to improve collaboration and communication skills",
            "category": IdeaCategory.PRODUCTIVITY,
            "priority": IdeaPriority.LOW
        }
    ]
    
    for idea_data in test_ideas_data:
        # Create idea
        idea = await idea_processor.capture_idea(
            content=idea_data["content"],
            source="conversion_test"
        )
        
        # Manually set category and priority for testing
        idea.category = idea_data["category"]
        idea.priority = idea_data["priority"]
        
        print(f"\nConverting idea: {idea.content[:60]}...")
        print(f"Category: {idea.category.value}, Priority: {idea.priority.value}")
        
        # Convert to tasks
        result = await converter.convert_idea_to_task(idea)
        
        if result.success:
            print(f"✓ Converted to {len(result.tasks)} tasks in {result.processing_time_ms:.1f}ms")
            print(f"Confidence: {result.conversion_confidence:.2f}")
            
            for i, task in enumerate(result.tasks, 1):
                print(f"  Task {i}: {task.title}")
                print(f"    Description: {task.description[:50]}...")
                print(f"    Priority: {task.priority.value}")
                print(f"    Duration: {task.estimated_duration_minutes} minutes")
                if task.due_date:
                    print(f"    Due: {task.due_date.strftime('%Y-%m-%d')}")
                print(f"    Tags: {task.tags}")
            
            if result.suggestions:
                print(f"  Suggestions: {', '.join(result.suggestions)}")
        else:
            print(f"✗ Conversion failed: {result.error_message}")


async def test_idea_to_calendar_conversion():
    """Test converting ideas to calendar events."""
    print("\n=== Testing Idea to Calendar Event Conversion ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create test ideas for calendar conversion
    test_ideas_data = [
        {
            "content": "Conduct user research interviews to understand customer pain points and feature requests",
            "preferred_time": datetime.utcnow() + timedelta(days=2, hours=10),
            "duration": 120
        },
        {
            "content": "Present quarterly business results to stakeholders and board members",
            "preferred_time": datetime.utcnow() + timedelta(days=7, hours=14),
            "duration": 60
        },
        {
            "content": "Brainstorming session for new product features and improvements",
            "preferred_time": None,
            "duration": 90
        }
    ]
    
    for idea_data in test_ideas_data:
        # Create idea
        idea = await idea_processor.capture_idea(
            content=idea_data["content"],
            source="calendar_test"
        )
        
        print(f"\nConverting idea: {idea.content[:60]}...")
        
        # Convert to calendar event
        result = await converter.convert_idea_to_calendar_event(
            idea,
            preferred_time=idea_data["preferred_time"],
            duration_minutes=idea_data["duration"]
        )
        
        if result.success and result.calendar_events:
            event = result.calendar_events[0]
            print(f"✓ Converted to calendar event in {result.processing_time_ms:.1f}ms")
            print(f"Confidence: {result.conversion_confidence:.2f}")
            print(f"  Title: {event.title}")
            print(f"  Description: {event.description[:50]}...")
            print(f"  Start: {event.start_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"  End: {event.end_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Duration: {(event.end_time - event.start_time).total_seconds() / 60:.0f} minutes")
            print(f"  Tags: {event.tags}")
            
            if result.suggestions:
                print(f"  Suggestions: {', '.join(result.suggestions)}")
        else:
            print(f"✗ Conversion failed: {result.error_message}")


async def test_ideas_to_project_conversion():
    """Test converting multiple ideas to a project."""
    print("\n=== Testing Ideas to Project Conversion ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create related ideas for project conversion
    related_ideas_content = [
        "Design user interface mockups for the new mobile application",
        "Implement user authentication and authorization system",
        "Create database schema for user data and application content",
        "Develop REST API endpoints for mobile app communication",
        "Set up automated testing framework for quality assurance",
        "Plan deployment strategy and CI/CD pipeline setup"
    ]
    
    ideas = []
    for content in related_ideas_content:
        idea = await idea_processor.capture_idea(content, source="project_test")
        ideas.append(idea)
    
    print(f"Converting {len(ideas)} related ideas to project...")
    
    # Convert to project
    result = await converter.convert_ideas_to_project(
        ideas,
        project_name="Mobile App Development Project",
        project_description="Complete development of new mobile application with backend services"
    )
    
    if result.success and result.projects:
        project = result.projects[0]
        print(f"✓ Converted to project with {len(result.tasks)} tasks in {result.processing_time_ms:.1f}ms")
        print(f"Confidence: {result.conversion_confidence:.2f}")
        print(f"  Project: {project.name}")
        print(f"  Description: {project.description}")
        print(f"  Status: {project.status}")
        print(f"  Priority: {project.priority.value}")
        print(f"  Source Ideas: {len(project.source_idea_ids)}")
        print(f"  Tasks: {len(project.task_ids)}")
        print(f"  Tags: {project.tags}")
        
        print(f"\n  Project Tasks:")
        for i, task in enumerate(result.tasks, 1):
            print(f"    {i}. {task.title}")
            print(f"       Duration: {task.estimated_duration_minutes} min, Priority: {task.priority.value}")
        
        if result.suggestions:
            print(f"\n  Suggestions: {', '.join(result.suggestions)}")
    else:
        print(f"✗ Project conversion failed: {result.error_message}")


async def test_batch_conversion():
    """Test batch conversion of multiple ideas."""
    print("\n=== Testing Batch Conversion ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create multiple ideas for batch conversion
    batch_ideas_content = [
        "Schedule weekly team standup meetings to improve communication",
        "Review and update company security policies and procedures",
        "Organize customer feedback session for product improvement",
        "Plan quarterly business review presentation for executives",
        "Set up automated backup system for critical business data"
    ]
    
    ideas = []
    for content in batch_ideas_content:
        idea = await idea_processor.capture_idea(content, source="batch_test")
        ideas.append(idea)
    
    print(f"Batch converting {len(ideas)} ideas to tasks...")
    
    # Batch convert to tasks
    batch_result = await converter.batch_convert_ideas(
        ideas,
        ConversionType.TASK,
        conversion_options={"custom_instructions": "Focus on actionable steps and clear deadlines"}
    )
    
    print(f"\nBatch Conversion Results:")
    print(f"  Total Ideas: {batch_result.total_ideas}")
    print(f"  Successful: {batch_result.successful_conversions}")
    print(f"  Failed: {batch_result.failed_conversions}")
    print(f"  Processing Time: {batch_result.processing_time_ms:.1f}ms")
    print(f"  Summary: {batch_result.summary}")
    
    # Show details for successful conversions
    successful_results = [r for r in batch_result.conversion_results if r.success]
    print(f"\nSuccessful Conversions ({len(successful_results)}):")
    for i, result in enumerate(successful_results, 1):
        print(f"  {i}. {result.source_idea.content[:50]}...")
        print(f"     → {len(result.tasks)} tasks created")
        if result.tasks:
            print(f"     → First task: {result.tasks[0].title}")
    
    # Show failed conversions
    failed_results = [r for r in batch_result.conversion_results if not r.success]
    if failed_results:
        print(f"\nFailed Conversions ({len(failed_results)}):")
        for i, result in enumerate(failed_results, 1):
            print(f"  {i}. {result.source_idea.content[:50]}...")
            print(f"     → Error: {result.error_message}")


async def test_conversion_suggestions():
    """Test conversion suggestion generation."""
    print("\n=== Testing Conversion Suggestions ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create ideas for suggestion testing
    test_ideas = [
        "Implement machine learning model for customer behavior prediction",
        "Organize company retreat for team building and strategic planning",
        "Launch new product line targeting enterprise customers"
    ]
    
    for content in test_ideas:
        idea = await idea_processor.capture_idea(content, source="suggestion_test")
        
        print(f"\nGenerating suggestions for: {idea.content[:60]}...")
        
        suggestions = await converter.get_conversion_suggestions(idea)
        
        for category, items in suggestions.items():
            if items:
                print(f"  {category.replace('_', ' ').title()}:")
                for item in items[:3]:  # Show top 3 suggestions
                    print(f"    • {item}")


async def test_project_linking():
    """Test linking ideas to existing projects."""
    print("\n=== Testing Project Linking ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create a project first
    project_ideas = [
        "Create project management dashboard",
        "Implement task tracking system"
    ]
    
    ideas = []
    for content in project_ideas:
        idea = await idea_processor.capture_idea(content, source="linking_test")
        ideas.append(idea)
    
    # Convert to project
    project_result = await converter.convert_ideas_to_project(ideas, project_name="Dashboard Project")
    
    if project_result.success and project_result.projects:
        project = project_result.projects[0]
        print(f"Created project: {project.name}")
        
        # Create a new idea to link to the project
        new_idea = await idea_processor.capture_idea(
            "Add real-time notifications to dashboard",
            source="linking_test"
        )
        
        print(f"Linking new idea: {new_idea.content}")
        
        # Link to existing project
        linked = await converter.link_idea_to_existing_project(new_idea, project.id)
        
        if linked:
            print("✓ Successfully linked idea to project")
        else:
            print("✗ Failed to link idea to project")
    else:
        print("✗ Failed to create initial project for linking test")


async def test_conversion_performance():
    """Test performance of conversion operations."""
    print("\n=== Testing Conversion Performance ===")
    
    idea_processor = get_idea_processor()
    converter = get_idea_converter()
    
    # Create ideas for performance testing
    performance_ideas = []
    for i in range(10):
        idea = await idea_processor.capture_idea(
            f"Performance test idea {i+1}: Implement feature for improved user experience and system efficiency",
            source=f"perf_test_{i}"
        )
        performance_ideas.append(idea)
    
    print(f"Created {len(performance_ideas)} ideas for performance testing")
    
    # Test single conversion performance
    start_time = datetime.utcnow()
    result = await converter.convert_idea_to_task(performance_ideas[0])
    single_time = (datetime.utcnow() - start_time).total_seconds()
    
    print(f"Single task conversion: {single_time:.3f}s")
    
    # Test batch conversion performance
    start_time = datetime.utcnow()
    batch_result = await converter.batch_convert_ideas(
        performance_ideas[:5],
        ConversionType.TASK
    )
    batch_time = (datetime.utcnow() - start_time).total_seconds()
    
    print(f"Batch conversion (5 ideas): {batch_time:.3f}s")
    print(f"Average per idea: {batch_time/5:.3f}s")
    
    # Test project conversion performance
    start_time = datetime.utcnow()
    project_result = await converter.convert_ideas_to_project(performance_ideas[:3])
    project_time = (datetime.utcnow() - start_time).total_seconds()
    
    print(f"Project conversion (3 ideas): {project_time:.3f}s")


async def main():
    """Run all idea-to-action conversion tests."""
    print("Starting Idea-to-Action Conversion System Tests")
    print("=" * 60)
    
    try:
        # Initialize systems
        print("Initializing systems...")
        initialize_ai_provider("simple")  # Use simple provider for testing
        db_manager = initialize_database("sqlite:///test_idea_conversion.db")
        await db_manager.create_tables_async()
        initialize_vector_store("simple")
        print("✓ Systems initialized")
        
        # Run tests
        await test_idea_to_task_conversion()
        await test_idea_to_calendar_conversion()
        await test_ideas_to_project_conversion()
        await test_batch_conversion()
        await test_conversion_suggestions()
        await test_project_linking()
        await test_conversion_performance()
        
        print("\n" + "=" * 60)
        print("Idea-to-Action Conversion System Tests Completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n✗ Tests failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())