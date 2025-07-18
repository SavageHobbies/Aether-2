#!/usr/bin/env python3
"""
Test script for the idea processing system.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from core.ideas import IdeaProcessor, IdeaCategory, IdeaPriority, IdeaQuery
from core.ai import initialize_ai_provider
from core.database import initialize_database
from core.database.vector_store import initialize_vector_store
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_idea_capture():
    """Test basic idea capture functionality."""
    print("\n=== Testing Idea Capture ===")
    
    idea_processor = IdeaProcessor()
    
    # Test capturing different types of ideas
    test_ideas = [
        {
            "content": "Create a mobile app for expense tracking with receipt scanning and automatic categorization",
            "source": "brainstorming_session",
            "context": "Team meeting discussion about productivity tools"
        },
        {
            "content": "Implement a dashboard showing real-time business metrics including revenue, customer acquisition, and churn rate",
            "source": "conversation_001",
            "context": "Client requested better visibility into business performance"
        },
        {
            "content": "Design a new logo with modern typography and clean aesthetic that reflects our brand values",
            "source": "design_review",
            "context": "Rebranding initiative for Q2"
        },
        {
            "content": "Optimize database queries to improve API response times by implementing caching and indexing strategies",
            "source": "performance_review",
            "context": "System performance analysis revealed bottlenecks"
        },
        {
            "content": "Research machine learning algorithms for predictive analytics to forecast customer behavior patterns",
            "source": "research_proposal",
            "context": "Data science team initiative"
        }
    ]
    
    captured_ideas = []
    for idea_data in test_ideas:
        try:
            idea = await idea_processor.capture_idea(**idea_data)
            captured_ideas.append(idea)
            print(f"✓ Captured {idea.category.value} idea: {idea.content[:50]}...")
            print(f"  ID: {idea.id}")
            print(f"  Keywords: {idea.keywords[:5]}")
            print(f"  Tags: {idea.tags}")
            print(f"  Confidence: {idea.confidence_score:.2f}")
        except Exception as e:
            print(f"✗ Failed to capture idea: {e}")
    
    print(f"Successfully captured {len(captured_ideas)} ideas")
    return captured_ideas


async def test_idea_processing():
    """Test idea processing functionality."""
    print("\n=== Testing Idea Processing ===")
    
    idea_processor = IdeaProcessor()
    
    # Capture an idea without auto-processing
    idea = await idea_processor.capture_idea(
        content="Build an AI-powered chatbot for customer support with natural language understanding and integration with existing CRM systems",
        source="feature_request",
        context="Customer service team needs automation",
        auto_process=False
    )
    
    print(f"Original idea: {idea.content}")
    print(f"Status: {idea.status.value}")
    print(f"Category: {idea.category.value}")
    
    # Process the idea
    processing_result = await idea_processor.process_idea(idea.id)
    
    if processing_result.success:
        processed_idea = processing_result.idea
        print(f"\n✓ Idea processed successfully in {processing_result.processing_time_ms:.1f}ms")
        print(f"Status: {processed_idea.status.value}")
        print(f"Category: {processed_idea.category.value}")
        print(f"Generated title: {processing_result.generated_title}")
        print(f"Extracted keywords: {processing_result.extracted_keywords}")
        print(f"Suggested categories: {[(cat.value, conf) for cat, conf in processing_result.suggested_categories]}")
        print(f"Suggested tags: {processing_result.suggested_tags}")
        if processing_result.context_analysis:
            print(f"Context analysis: {processing_result.context_analysis}")
    else:
        print(f"✗ Processing failed: {processing_result.error_message}")


async def test_idea_search():
    """Test idea search functionality."""
    print("\n=== Testing Idea Search ===")
    
    idea_processor = IdeaProcessor()
    
    # Test different search queries
    test_queries = [
        {
            "query": IdeaQuery(query_text="mobile app development"),
            "description": "Text-based search"
        },
        {
            "query": IdeaQuery(categories=[IdeaCategory.BUSINESS, IdeaCategory.TECHNICAL]),
            "description": "Category filter search"
        },
        {
            "query": IdeaQuery(priorities=[IdeaPriority.HIGH, IdeaPriority.URGENT]),
            "description": "Priority filter search"
        },
        {
            "query": IdeaQuery(
                query_text="dashboard analytics",
                categories=[IdeaCategory.BUSINESS],
                max_results=3
            ),
            "description": "Combined text and category search"
        },
        {
            "query": IdeaQuery(tags=["development", "automation"]),
            "description": "Tag-based search"
        }
    ]
    
    for query_data in test_queries:
        try:
            results = await idea_processor.search_ideas(query_data["query"])
            
            print(f"\n{query_data['description']}:")
            print(f"Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result.idea.category.value}] {result.idea.content[:60]}...")
                print(f"     Similarity: {result.similarity_score:.3f}, Relevance: {result.relevance_score:.3f}")
                if result.match_reasons:
                    print(f"     Reasons: {', '.join(result.match_reasons)}")
            
        except Exception as e:
            print(f"✗ Search failed: {e}")


async def test_idea_expansion():
    """Test idea expansion functionality."""
    print("\n=== Testing Idea Expansion ===")
    
    idea_processor = IdeaProcessor()
    
    # Capture an idea to expand
    idea = await idea_processor.capture_idea(
        content="Create a productivity dashboard that integrates with multiple tools and shows personalized insights",
        source="user_feedback"
    )
    
    print(f"Original idea: {idea.content}")
    
    # Expand the idea
    expansion_result = await idea_processor.expand_idea(idea.id)
    
    if expansion_result.success:
        print(f"\n✓ Idea expanded successfully")
        print(f"Expanded content: {expansion_result.expanded_content[:200]}...")
        
        print(f"\nFollow-up questions ({len(expansion_result.follow_up_questions)}):")
        for i, question in enumerate(expansion_result.follow_up_questions, 1):
            print(f"  {i}. {question}")
        
        print(f"\nRelated concepts ({len(expansion_result.related_concepts)}):")
        for concept in expansion_result.related_concepts:
            print(f"  - {concept}")
        
        print(f"\nPotential challenges ({len(expansion_result.potential_challenges)}):")
        for challenge in expansion_result.potential_challenges:
            print(f"  - {challenge}")
        
        print(f"\nImplementation suggestions ({len(expansion_result.implementation_suggestions)}):")
        for suggestion in expansion_result.implementation_suggestions:
            print(f"  - {suggestion}")
    else:
        print(f"✗ Expansion failed: {expansion_result.error_message}")


async def test_idea_connections():
    """Test idea connection functionality."""
    print("\n=== Testing Idea Connections ===")
    
    idea_processor = IdeaProcessor()
    
    # Capture related ideas
    related_ideas = [
        "Build a customer analytics dashboard with real-time metrics",
        "Create mobile app for field sales team with offline capabilities",
        "Implement business intelligence reporting system",
        "Design user-friendly dashboard for executive team"
    ]
    
    captured_ideas = []
    for content in related_ideas:
        idea = await idea_processor.capture_idea(content, source="connection_test")
        captured_ideas.append(idea)
    
    # Test connections for the first idea
    if captured_ideas:
        test_idea = captured_ideas[0]
        print(f"Finding connections for: {test_idea.content}")
        
        connection_result = await idea_processor.find_idea_connections(test_idea.id)
        
        print(f"\nConnection summary: {connection_result.connection_summary}")
        
        print(f"\nConnections found ({len(connection_result.connections)}):")
        for idea_id, similarity, conn_type in connection_result.connections:
            print(f"  - {conn_type} connection (similarity: {similarity:.3f})")
        
        if connection_result.suggested_merges:
            print(f"\nSuggested merges: {len(connection_result.suggested_merges)} ideas")
        
        if connection_result.suggested_hierarchies:
            print(f"Suggested hierarchies: {len(connection_result.suggested_hierarchies)} relationships")


async def test_idea_statistics():
    """Test idea statistics functionality."""
    print("\n=== Testing Idea Statistics ===")
    
    idea_processor = IdeaProcessor()
    
    try:
        stats = await idea_processor.get_idea_stats()
        
        print(f"Total ideas: {stats.total_ideas}")
        print(f"Average processing time: {stats.average_processing_time_ms:.1f}ms")
        
        print("\nIdeas by category:")
        for category, count in stats.ideas_by_category.items():
            print(f"  {category.value}: {count}")
        
        print("\nIdeas by priority:")
        for priority, count in stats.ideas_by_priority.items():
            print(f"  {priority.value}: {count}")
        
        print("\nIdeas by status:")
        for status, count in stats.ideas_by_status.items():
            print(f"  {status.value}: {count}")
        
        if stats.ideas_by_source:
            print("\nIdeas by source:")
            for source, count in stats.ideas_by_source.items():
                print(f"  {source}: {count}")
        
        if stats.most_active_tags:
            print(f"\nMost active tags:")
            for tag, count in stats.most_active_tags[:5]:
                print(f"  {tag}: {count}")
        
        if stats.most_common_keywords:
            print(f"\nMost common keywords:")
            for keyword, count in stats.most_common_keywords[:5]:
                print(f"  {keyword}: {count}")
        
        if stats.conversion_rates:
            print(f"\nConversion rates:")
            for conversion_type, rate in stats.conversion_rates.items():
                print(f"  {conversion_type}: {rate:.1%}")
        
    except Exception as e:
        print(f"✗ Failed to get statistics: {e}")


async def test_keyword_extraction():
    """Test keyword extraction functionality."""
    print("\n=== Testing Keyword Extraction ===")
    
    idea_processor = IdeaProcessor()
    
    test_texts = [
        "Create a machine learning model for predictive analytics using Python and TensorFlow",
        "Design a user-friendly mobile application with React Native and Firebase integration",
        "Implement automated testing framework with continuous integration and deployment pipeline",
        "Build a customer relationship management system with sales tracking and reporting features"
    ]
    
    for text in test_texts:
        keywords = await idea_processor._extract_keywords(text)
        print(f"\nText: {text}")
        print(f"Keywords: {keywords}")


async def test_categorization():
    """Test idea categorization functionality."""
    print("\n=== Testing Idea Categorization ===")
    
    idea_processor = IdeaProcessor()
    
    test_ideas = [
        "Increase revenue by 20% through new customer acquisition strategies",
        "Optimize database performance using indexing and query optimization techniques",
        "Create a beautiful logo design with modern typography and color scheme",
        "Implement automated workflow for invoice processing and approval",
        "Research latest trends in artificial intelligence and machine learning"
    ]
    
    for content in test_ideas:
        keywords = await idea_processor._extract_keywords(content)
        categories = await idea_processor._categorize_idea(content, keywords)
        
        print(f"\nIdea: {content}")
        print(f"Top categories: {[(cat.value, f'{conf:.2f}') for cat, conf in categories[:3]]}")


async def main():
    """Run all idea system tests."""
    print("Starting Idea Processing System Tests")
    print("=" * 50)
    
    try:
        # Initialize systems
        print("Initializing systems...")
        initialize_ai_provider("simple")  # Use simple provider for testing
        db_manager = initialize_database("sqlite:///test_ideas.db")
        await db_manager.create_tables_async()
        initialize_vector_store("simple")
        print("✓ Systems initialized")
        
        # Run tests
        captured_ideas = await test_idea_capture()
        await test_idea_processing()
        await test_keyword_extraction()
        await test_categorization()
        await test_idea_search()
        await test_idea_expansion()
        await test_idea_connections()
        await test_idea_statistics()
        
        print("\n" + "=" * 50)
        print("Idea Processing System Tests Completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n✗ Tests failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())