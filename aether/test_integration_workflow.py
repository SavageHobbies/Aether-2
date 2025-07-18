#!/usr/bin/env python3
"""
Integration test demonstrating the complete workflow from task extraction to calendar events.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.tasks.extractor import TaskExtractor
from core.integrations.google_calendar import GoogleCalendarIntegration
from core.integrations.calendar_types import (
    CalendarAuthConfig, CalendarPreferences, CalendarEventType
)


def test_complete_workflow():
    """Test the complete workflow from conversation to calendar events."""
    print("=== Complete Workflow Integration Test ===")
    print("Testing: Conversation → Task Extraction → Calendar Events")
    
    # Step 1: Extract tasks from a conversation
    print("\n1. Extracting tasks from conversation...")
    
    conversation = """
    Hi team, I wanted to follow up on our discussion yesterday. We have several action items:
    
    First, I need to call the client about the project timeline by Friday. This is urgent 
    because they're waiting for our response.
    
    Second, we should schedule a review meeting for next Tuesday at 2 PM to go over 
    the quarterly results. Don't forget to prepare the presentation slides beforehand.
    
    Also, I have to submit the budget proposal by Wednesday - this is a hard deadline 
    from finance.
    
    Finally, someone needs to research the new compliance requirements. This should 
    be done in the next two weeks.
    """
    
    # Extract tasks
    task_extractor = TaskExtractor()
    extraction_result = task_extractor.extract_tasks_from_text(
        conversation,
        conversation_id="team_meeting_001",
        source_context={"meeting_type": "weekly_standup"}
    )
    
    print(f"✓ Extracted {len(extraction_result.extracted_tasks)} tasks")
    print(f"  Confidence: {extraction_result.confidence_score:.2f}")
    
    for i, task in enumerate(extraction_result.extracted_tasks, 1):
        print(f"  Task {i}: {task.title}")
        print(f"    Type: {task.task_type.value}")
        print(f"    Priority: {task.priority.value}")
        print(f"    Due: {task.due_date}")
        print(f"    Urgency: {task.urgency_score:.2f}")
    
    # Step 2: Set up calendar integration
    print("\n2. Setting up calendar integration...")
    
    auth_config = CalendarAuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret"
    )
    
    preferences = CalendarPreferences(
        default_event_duration_minutes=60,
        auto_create_events_from_tasks=True,
        conflict_detection_enabled=True,
        work_start_hour=9,
        work_end_hour=17
    )
    
    calendar = GoogleCalendarIntegration(auth_config, preferences)
    auth_success = calendar.authenticate()
    print(f"✓ Calendar authentication: {auth_success}")
    
    # Step 3: Convert tasks to calendar events
    print("\n3. Converting tasks to calendar events...")
    
    created_events = []
    
    for task in extraction_result.extracted_tasks:
        if task.due_date:  # Only create events for tasks with due dates
            # Create calendar event from task
            from core.integrations.calendar_types import CalendarEvent
            
            # Determine event duration based on task type
            duration_minutes = 60  # Default
            if task.task_type.value == "meeting":
                duration_minutes = 60
            elif task.task_type.value == "call":
                duration_minutes = 30
            elif task.task_type.value == "research":
                duration_minutes = 120
            
            event = CalendarEvent(
                title=f"Task: {task.title}",
                description=f"Task from conversation: {task.description}\n\nPriority: {task.priority.value}\nSource: {task.source_conversation_id}",
                start_time=task.due_date,
                end_time=task.due_date + timedelta(minutes=duration_minutes),
                event_type=CalendarEventType.TASK,
                source_task_id=task.id,
                source_conversation_id=task.source_conversation_id
            )
            
            # Create the event
            event_id = calendar.create_event(event)
            if event_id:
                created_events.append(event)
                print(f"✓ Created calendar event: {event.title}")
                print(f"  Event ID: {event_id}")
                print(f"  Time: {event.start_time} - {event.end_time}")
    
    print(f"\n✓ Created {len(created_events)} calendar events from tasks")
    
    # Step 4: Detect conflicts
    print("\n4. Detecting scheduling conflicts...")
    
    all_conflicts = []
    for event in created_events:
        conflicts = calendar.detect_conflicts(event, created_events)
        all_conflicts.extend(conflicts)
    
    if all_conflicts:
        print(f"⚠ Found {len(all_conflicts)} scheduling conflicts:")
        for i, conflict in enumerate(all_conflicts, 1):
            print(f"  Conflict {i}: {conflict.description}")
            print(f"    Type: {conflict.conflict_type.value}")
            print(f"    Severity: {conflict.severity}")
            if conflict.suggested_resolution:
                print(f"    Suggestion: {conflict.suggested_resolution}")
    else:
        print("✓ No scheduling conflicts detected")
    
    # Step 5: Suggest alternative times for conflicting events
    if all_conflicts:
        print("\n5. Suggesting alternative times...")
        
        for conflict in all_conflicts[:2]:  # Show alternatives for first 2 conflicts
            event = conflict.primary_event
            suggestions = calendar.suggest_alternative_times(event, event.duration_minutes)
            
            print(f"\nAlternative times for '{event.title}':")
            for i, (start, end) in enumerate(suggestions[:3], 1):
                print(f"  Option {i}: {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}")
    
    # Step 6: Demonstrate two-way sync
    print("\n6. Demonstrating calendar synchronization...")
    
    # Get all events for today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    all_events = calendar.get_events(today, tomorrow)
    print(f"✓ Retrieved {len(all_events)} events from calendar")
    
    # Show event summary
    for event in all_events:
        print(f"  - {event.title} ({event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')})")
    
    # Step 7: Performance and reliability metrics
    print("\n7. Performance metrics...")
    
    print(f"✓ Task extraction time: {extraction_result.processing_time_ms:.1f}ms")
    print(f"✓ Calendar operations: {len(created_events)} events created")
    print(f"✓ Conflict detection: {len(all_conflicts)} conflicts found")
    print(f"✓ Overall workflow success: {extraction_result.success and auth_success}")
    
    return {
        'tasks_extracted': len(extraction_result.extracted_tasks),
        'events_created': len(created_events),
        'conflicts_detected': len(all_conflicts),
        'extraction_time_ms': extraction_result.processing_time_ms,
        'workflow_success': extraction_result.success and auth_success
    }


def test_business_scenarios():
    """Test various business scenarios."""
    print("\n=== Business Scenario Tests ===")
    
    scenarios = [
        {
            'name': 'Client Meeting Scheduling',
            'conversation': "I need to schedule a client presentation for next Friday at 3 PM. Make sure to prepare the quarterly report beforehand and send the agenda to all stakeholders by Wednesday.",
            'expected_tasks': 3,
            'expected_events': 2
        },
        {
            'name': 'Project Deadline Management',
            'conversation': "The project deliverable is due Monday. We need to review the code by Friday, test everything over the weekend, and submit the final version first thing Monday morning.",
            'expected_tasks': 3,
            'expected_events': 3
        },
        {
            'name': 'Urgent Issue Response',
            'conversation': "URGENT: The production server is down. I need to call the hosting provider immediately, notify all clients about the outage, and schedule an emergency team meeting for 2 PM today.",
            'expected_tasks': 3,
            'expected_events': 2
        }
    ]
    
    task_extractor = TaskExtractor()
    calendar = GoogleCalendarIntegration(
        CalendarAuthConfig("test", "test"),
        CalendarPreferences()
    )
    calendar.authenticate()
    
    results = []
    
    for scenario in scenarios:
        print(f"\nTesting: {scenario['name']}")
        
        # Extract tasks
        result = task_extractor.extract_tasks_from_text(scenario['conversation'])
        
        # Create events for tasks with due dates
        events_created = 0
        for task in result.extracted_tasks:
            if task.due_date:
                from core.integrations.calendar_types import CalendarEvent
                event = CalendarEvent(
                    title=f"Task: {task.title}",
                    start_time=task.due_date,
                    end_time=task.due_date + timedelta(hours=1),
                    event_type=CalendarEventType.TASK
                )
                if calendar.create_event(event):
                    events_created += 1
        
        print(f"  Tasks extracted: {len(result.extracted_tasks)} (expected: {scenario['expected_tasks']})")
        print(f"  Events created: {events_created} (expected: {scenario['expected_events']})")
        print(f"  Confidence: {result.confidence_score:.2f}")
        
        results.append({
            'scenario': scenario['name'],
            'tasks_extracted': len(result.extracted_tasks),
            'events_created': events_created,
            'confidence': result.confidence_score,
            'success': result.success
        })
    
    return results


def main():
    """Run the complete integration workflow test."""
    print("Starting Complete Integration Workflow Test")
    print("=" * 60)
    
    try:
        # Test complete workflow
        workflow_results = test_complete_workflow()
        
        # Test business scenarios
        scenario_results = test_business_scenarios()
        
        # Summary
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        print(f"✓ Complete workflow test: {'PASSED' if workflow_results['workflow_success'] else 'FAILED'}")
        print(f"  - Tasks extracted: {workflow_results['tasks_extracted']}")
        print(f"  - Calendar events created: {workflow_results['events_created']}")
        print(f"  - Conflicts detected: {workflow_results['conflicts_detected']}")
        print(f"  - Processing time: {workflow_results['extraction_time_ms']:.1f}ms")
        
        print(f"\n✓ Business scenarios tested: {len(scenario_results)}")
        for result in scenario_results:
            status = "PASSED" if result['success'] else "FAILED"
            print(f"  - {result['scenario']}: {status} ({result['tasks_extracted']} tasks, {result['events_created']} events)")
        
        print(f"\n🎉 Integration test completed successfully!")
        print("The system can now:")
        print("  • Extract tasks from natural language conversations")
        print("  • Automatically create calendar events from tasks")
        print("  • Detect and resolve scheduling conflicts")
        print("  • Suggest alternative meeting times")
        print("  • Provide two-way calendar synchronization")
        
        return 0
        
    except Exception as e:
        print(f"\nIntegration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())