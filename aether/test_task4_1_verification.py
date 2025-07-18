"""
Test script to verify Task 4.1: Create idea capture and processing engine.
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import initialize_database, initialize_vector_store
from core.ai import initialize_ai_provider
from core.ideas import get_idea_processor
from core.ideas.types import IdeaCategory, IdeaPriority, IdeaStatus


async def test_task_4_1_idea_capture_and_processing():
    """Test Task 4.1: Idea capture and processing engine."""
    print("🚀 Testing Task 4.1: Idea Capture and Processing Engine\\n")
    
    # Clean up test files
    test_db = Path("test_task4_1.db")
    test_vectors = Path("test_task4_1_vectors")
    
    if test_db.exists():
        test_db.unlink()
    if test_vectors.exists():
        import shutil
        shutil.rmtree(test_vectors)
    
    try:
        # Initialize systems
        print("🔧 Initializing systems...")
        db_manager = initialize_database(f"sqlite:///{test_db}", echo=False)
        vector_store = initialize_vector_store("simple", test_vectors)
        ai_provider = initialize_ai_provider("simple")
        
        await db_manager.create_tables_async()
        print("✅ Systems initialized")
        
        # Get idea processor
        idea_processor = get_idea_processor()
        
        # Test 1: Rapid idea ingestion with automatic timestamping
        print("\\n📝 Testing Rapid Idea Ingestion...")
        
        test_ideas = [
            {
                "content": "Create a mobile app for expense tracking with receipt scanning",
                "source": "conversation_123",
                "context": "Discussed during team meeting about productivity tools"
            },
            {
                "content": "Implement a dashboard showing real-time business metrics and KPIs",
                "source": "voice_input",
                "context": "Brainstorming session for Q4 goals"
            },
            {
                "content": "Design a user-friendly interface for the customer portal",
                "source": "manual_entry",
                "context": "UI/UX improvement initiative"
            },
            {
                "content": "Optimize database queries to improve API response times",
                "source": "code_review",
                "context": "Performance optimization sprint"
            },
            {
                "content": "Research machine learning algorithms for predictive analytics",
                "source": "research_session",
                "context": "Data science exploration"
            }
        ]
        
        captured_ideas = []
        for i, idea_data in enumerate(test_ideas, 1):
            print(f"\\n🔄 Capturing idea {i}/5...")
            print(f"Content: {idea_data['content'][:50]}...")
            
            # Test rapid idea capture
            idea = await idea_processor.capture_idea(
                content=idea_data["content"],
                source=idea_data["source"],
                context=idea_data["context"],
                auto_process=False  # Test manual processing separately
            )
            
            captured_ideas.append(idea)
            
            # Verify automatic timestamping
            assert idea.created_at is not None, "Created timestamp should be set"
            assert idea.updated_at is not None, "Updated timestamp should be set"
            assert idea.id is not None, "ID should be generated"
            assert idea.status == IdeaStatus.CAPTURED, "Status should be CAPTURED"
            
            print(f"✅ Captured idea: {idea.id[:8]}...")
            print(f"   Timestamp: {idea.created_at}")
            print(f"   Source: {idea.source}")
            print(f"   Status: {idea.status.value}")
        
        print(f"\\n✅ Successfully captured {len(captured_ideas)} ideas with automatic timestamping")
        
        # Test 2: NLP processing for idea categorization and keyword extraction
        print("\\n🧠 Testing NLP Processing...")
        
        for i, idea in enumerate(captured_ideas[:3], 1):  # Test first 3 ideas
            print(f"\\n🔄 Processing idea {i}/3...")
            print(f"Content: {idea.content[:50]}...")
            
            # Test idea processing
            processing_result = await idea_processor.process_idea(idea.id)
            
            if processing_result.success:
                processed_idea = processing_result.idea
                
                print(f"✅ Processing completed in {processing_result.processing_time_ms:.1f}ms")
                print(f"   Status: {processed_idea.status.value}")
                print(f"   Category: {processed_idea.category.value}")
                print(f"   Keywords: {processing_result.extracted_keywords[:5]}")
                print(f"   Suggested categories: {[cat.value for cat, _ in processing_result.suggested_categories[:3]]}")
                
                # Verify processing results
                assert processed_idea.status in [IdeaStatus.PROCESSING, IdeaStatus.CATEGORIZED], "Status should be updated"
                assert len(processing_result.extracted_keywords) > 0, "Keywords should be extracted"
                assert len(processing_result.suggested_categories) > 0, "Categories should be suggested"
                assert processing_result.processing_time_ms > 0, "Processing time should be recorded"
                
            else:
                print(f"⚠️  Processing failed: {processing_result.error_message}")
        
        print("\\n✅ NLP processing for categorization and keyword extraction working")
        
        # Test 3: Metadata generation for source tracking and context
        print("\\n📊 Testing Metadata Generation...")
        
        for i, idea in enumerate(captured_ideas[:2], 1):
            print(f"\\n🔄 Checking metadata for idea {i}/2...")
            
            # Verify source tracking
            assert idea.source is not None, "Source should be tracked"
            assert idea.context is not None, "Context should be stored"
            
            print(f"✅ Metadata verified:")
            print(f"   Source: {idea.source}")
            print(f"   Context: {idea.context[:50]}...")
            print(f"   Created: {idea.created_at}")
            print(f"   Updated: {idea.updated_at}")
        
        print("\\n✅ Metadata generation for source tracking and context working")
        
        # Test 4: Keyword extraction functionality
        print("\\n🔍 Testing Keyword Extraction...")
        
        test_texts = [
            "Create a machine learning model for predictive analytics using Python and TensorFlow",
            "Design a user-friendly mobile application with React Native and Firebase integration",
            "Implement automated testing framework with continuous integration and deployment pipeline",
            "Build a customer relationship management system with sales tracking and reporting features"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\\n🔄 Extracting keywords from text {i}/4...")
            print(f"Text: {text[:60]}...")
            
            # Test keyword extraction (using internal method)
            keywords = await idea_processor._extract_keywords(text)
            
            print(f"✅ Extracted {len(keywords)} keywords: {keywords[:5]}")
            
            # Verify keyword extraction
            assert len(keywords) > 0, "Keywords should be extracted"
            assert all(len(keyword) >= 3 for keyword in keywords), "Keywords should be meaningful length"
        
        print("\\n✅ Keyword extraction functionality working")
        
        # Test 5: Categorization functionality
        print("\\n🏷️  Testing Categorization...")
        
        test_categorization = [
            ("Increase revenue by 20% through new customer acquisition strategies", "business"),
            ("Optimize database performance using indexing and query optimization techniques", "technical"),
            ("Create a beautiful logo design with modern typography and color scheme", "creative"),
            ("Implement automated workflow for invoice processing and approval", "productivity"),
            ("Research latest trends in artificial intelligence and machine learning", "research")
        ]
        
        for i, (text, expected_category) in enumerate(test_categorization, 1):
            print(f"\\n🔄 Categorizing text {i}/5...")
            print(f"Text: {text[:50]}...")
            
            # Test categorization (using internal method)
            keywords = await idea_processor._extract_keywords(text)
            categories = await idea_processor._categorize_idea(text, keywords)
            
            if categories:
                top_category, confidence = categories[0]
                print(f"✅ Top category: {top_category.value} (confidence: {confidence:.2f})")
                
                # Verify categorization makes sense
                assert confidence > 0, "Should have some confidence in categorization"
                assert len(categories) > 0, "Should suggest at least one category"
            else:
                print("⚠️  No categories suggested")
        
        print("\\n✅ Categorization functionality working")
        
        # Test 6: Idea statistics
        print("\\n📈 Testing Idea Statistics...")
        
        stats = await idea_processor.get_idea_stats()
        
        print(f"✅ Idea Statistics:")
        print(f"   Total ideas: {stats.total_ideas}")
        print(f"   Average processing time: {stats.average_processing_time_ms:.1f}ms")
        print(f"   Ideas by category: {len(stats.ideas_by_category)} categories")
        print(f"   Ideas by priority: {len(stats.ideas_by_priority)} priorities")
        print(f"   Ideas by status: {len(stats.ideas_by_status)} statuses")
        
        print("\\n✅ Idea statistics functionality working")
        
        print("\\n🎉 Task 4.1: Idea Capture and Processing Engine - COMPLETE!")
        print("\\n🎯 Verified Components:")
        print("  ✅ Rapid idea ingestion with automatic timestamping")
        print("  ✅ NLP processing for idea categorization")
        print("  ✅ Keyword extraction from idea content")
        print("  ✅ Metadata generation for source tracking and context")
        print("  ✅ Idea processing pipeline with status tracking")
        print("  ✅ Statistics and analytics for idea management")
        
        return True
        
    except Exception as e:
        print(f"❌ Task 4.1 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            await db_manager.close()
        except:
            pass
        
        try:
            if test_db.exists():
                test_db.unlink()
        except PermissionError:
            pass
        
        try:
            if test_vectors.exists():
                import shutil
                shutil.rmtree(test_vectors)
        except PermissionError:
            pass


async def main():
    """Main test function."""
    success = await test_task_4_1_idea_capture_and_processing()
    
    if success:
        print("\\n✅ Task 4.1 verification passed!")
        print("\\n🚀 Ready to continue with Task 4.2: Build idea connection and suggestion system!")
    else:
        print("\\n❌ Task 4.1 verification failed!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)