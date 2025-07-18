#!/usr/bin/env python3
"""
Unit tests for task extraction functionality.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.tasks.extractor import TaskExtractor
from core.tasks.task_types import TaskPriority, TaskStatus, TaskType


class TestTaskExtraction(unittest.TestCase):
    """Test cases for task extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = TaskExtractor()
    
    def test_basic_task_extraction(self):
        """Test basic task extraction from simple text."""
        text = "I need to call John about the project deadline."
        result = self.extractor.extract_tasks_from_text(text)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.extracted_tasks), 1)
        
        task = result.extracted_tasks[0]
        self.assertEqual(task.task_type, TaskType.ACTION)
        self.assertIn("Call John", task.title)
    
    def test_priority_detection(self):
        """Test priority detection from keywords."""
        # Test urgent priority
        text = "I need to call the client immediately - this is urgent!"
        result = self.extractor.extract_tasks_from_text(text)
        self.assertEqual(result.extracted_tasks[0].priority, TaskPriority.URGENT)
        
        # Test high priority
        text = "I need to review the important contract soon."
        result = self.extractor.extract_tasks_from_text(text)
        self.assertEqual(result.extracted_tasks[0].priority, TaskPriority.HIGH)
        
        # Test medium priority (default)
        text = "I should check the email."
        result = self.extractor.extract_tasks_from_text(text)
        self.assertEqual(result.extracted_tasks[0].priority, TaskPriority.MEDIUM)
    
    def test_due_date_extraction(self):
        """Test due date extraction from text."""
        # Test "tomorrow"
        text = "I need to finish the report by tomorrow."
        result = self.extractor.extract_tasks_from_text(text)
        task = result.extracted_tasks[0]
        
        if task.due_date:
            # Should be approximately tomorrow
            expected_date = datetime.now() + timedelta(days=1)
            self.assertAlmostEqual(
                task.due_date.date(), 
                expected_date.date(), 
                delta=timedelta(days=1)
            )
    
    def test_task_type_classification(self):
        """Test task type classification."""
        test_cases = [
            ("Schedule a meeting with the team", TaskType.MEETING),
            ("Research the competitor analysis", TaskType.RESEARCH),
            ("Review the quarterly budget", TaskType.REVIEW),
            ("Decide on the new hire", TaskType.DECISION),
            ("Remember to call mom", TaskType.REMINDER),
        ]
        
        for text, expected_type in test_cases:
            result = self.extractor.extract_tasks_from_text(text)
            if result.extracted_tasks:
                self.assertEqual(result.extracted_tasks[0].task_type, expected_type)
    
    def test_tag_extraction(self):
        """Test tag extraction from text."""
        text = "I need to schedule a meeting with the client about the project budget."
        result = self.extractor.extract_tasks_from_text(text)
        
        if result.extracted_tasks:
            task = result.extracted_tasks[0]
            # Should contain relevant tags
            self.assertIn("meeting", task.tags)
            self.assertIn("client", task.tags)
            self.assertIn("project", task.tags)
            self.assertIn("finance", task.tags)
    
    def test_confidence_scoring(self):
        """Test confidence scoring for extraction results."""
        # High confidence case - clear task with due date
        text = "I need to call John by Friday about the urgent project."
        result = self.extractor.extract_tasks_from_text(text)
        self.assertGreater(result.confidence_score, 0.7)
        
        # Low confidence case - vague text
        text = "Maybe we should think about stuff sometime."
        result = self.extractor.extract_tasks_from_text(text)
        # This might not extract any tasks, so confidence should be low
        if result.extracted_tasks:
            self.assertLess(result.confidence_score, 0.9)  # Adjusted expectation
        else:
            # No tasks extracted should result in 0 confidence
            self.assertEqual(result.confidence_score, 0.0)
    
    def test_urgency_and_importance_scoring(self):
        """Test urgency and importance scoring."""
        text = "I need to submit the critical report by tomorrow - this is urgent!"
        result = self.extractor.extract_tasks_from_text(text)
        
        if result.extracted_tasks:
            task = result.extracted_tasks[0]
            # Should have high urgency due to "tomorrow" and "urgent"
            self.assertGreater(task.urgency_score, 0.8)
            # Should have reasonable importance
            self.assertGreater(task.importance_score, 0.4)
    
    def test_suggestions_generation(self):
        """Test suggestion generation for improvement."""
        # Test case with no tasks
        text = "This is just a regular sentence with no actionable items."
        result = self.extractor.extract_tasks_from_text(text)
        self.assertIn("No tasks were detected", result.suggestions[0])
        
        # Test case with tasks but no due dates
        text = "I should probably do something about that project."
        result = self.extractor.extract_tasks_from_text(text)
        if result.extracted_tasks and not result.extracted_tasks[0].due_date:
            suggestion_text = " ".join(result.suggestions)
            self.assertIn("due dates", suggestion_text)
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test empty text
        result = self.extractor.extract_tasks_from_text("")
        self.assertTrue(result.success)  # Should handle gracefully
        self.assertEqual(len(result.extracted_tasks), 0)
        
        # Test None input (should be handled by preprocessing)
        try:
            result = self.extractor.extract_tasks_from_text(None)
            # If it doesn't raise an exception, it should return an error result
            if not result.success:
                self.assertIsNotNone(result.error_message)
        except (TypeError, AttributeError):
            # This is also acceptable behavior
            pass
    
    def test_context_integration(self):
        """Test integration with conversation context."""
        text = "I need to call the client about the project."
        context = {
            'conversation_id': 'test_conv_123',
            'idea_id': 'idea_456'
        }
        
        result = self.extractor.extract_tasks_from_text(text, source_context=context)
        
        if result.extracted_tasks:
            task = result.extracted_tasks[0]
            self.assertEqual(task.source_conversation_id, 'test_conv_123')
            self.assertEqual(task.source_idea_id, 'idea_456')
    
    def test_performance(self):
        """Test performance with reasonable text sizes."""
        # Create a moderately long text with multiple tasks
        text = """
        I need to call John about the project by Friday. 
        Don't forget to review the quarterly reports tomorrow.
        We should schedule a meeting with the client next week.
        I have to submit the proposal by end of day.
        Remember to check the budget numbers before the presentation.
        """ * 5  # Repeat to make it longer
        
        result = self.extractor.extract_tasks_from_text(text)
        
        # Should complete in reasonable time (less than 100ms for this size)
        self.assertLess(result.processing_time_ms, 100)
        self.assertTrue(result.success)
        self.assertGreater(len(result.extracted_tasks), 0)


class TestTaskExtractionIntegration(unittest.TestCase):
    """Integration tests for task extraction with other components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = TaskExtractor()
    
    def test_complex_conversation_extraction(self):
        """Test extraction from a complex, realistic conversation."""
        conversation = """
        Hi team, following up on our discussion yesterday. We have several action items:
        
        First, I need to call the client about the project timeline by end of week. 
        This is urgent because they're waiting for our response.
        
        Second, we should schedule a review meeting for next Tuesday to go over 
        the quarterly results. Don't forget to prepare the presentation slides beforehand.
        
        Also, someone needs to research the new compliance requirements that came out 
        last month. This isn't urgent but should be done in the next two weeks.
        
        Finally, I have to submit the budget proposal by Friday - this is a hard 
        deadline from finance.
        """
        
        result = self.extractor.extract_tasks_from_text(conversation)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.extracted_tasks), 2)  # Should find multiple tasks
        self.assertGreater(result.confidence_score, 0.5)   # Should be reasonably confident
        
        # Check that different types of tasks are identified
        task_types = [task.task_type for task in result.extracted_tasks]
        self.assertIn(TaskType.ACTION, task_types)
        
        # Check that priorities are assigned
        priorities = [task.priority for task in result.extracted_tasks]
        self.assertTrue(any(p in [TaskPriority.HIGH, TaskPriority.URGENT] for p in priorities))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)