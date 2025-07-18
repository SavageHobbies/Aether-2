#!/usr/bin/env python3
"""
Test script for the idea connection and suggestion system.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from core.ideas import (
    IdeaProcessor, IdeaConnectionEngine, 
    IdeaCategory, IdeaPriority, IdeaQuery,
    get_idea_processor, get_idea_connection_engine
)
from core.ai import initialize_ai_provider
from core.database import initialize_database
from core.database.vector_store import initialize_vector_store
from shared.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_semantic_connections():
    """Test semantic connection finding between ideas."""
    print("\n=== Testing Semantic Connections ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create related ideas
    related_ideas_data = [
        "Build a customer analytics dashboard with real-time metrics and KPI tracking",
        "Create a business intelligence platform for data visualization and reporting",
        "Develop a mobile app for expense tracking with receipt scanning capabilities",
        "Design a productivity dashboard that shows team performance and project status",
        "Implement automated reporting system for sales and marketing metrics"
    ]
    
    captured_ideas = []
    for content in related_ideas_data:
        idea = await idea_processor.capture_idea(content, source="connection_test")
        captured_ideas.append(idea)
    
    # Test connections for the first idea
    if captured_ideas:
        test_idea = captured_ideas[0]
        print(f"Finding connections for: {test_idea.content}")
        
        connections = await connection_engine.find_semantic_connections(
            test_idea, 
            captured_ideas[1:],  # Exclude the test idea itself
            similarity_threshold=0.5
        )
        
        print(f"\nFound {len(connections)} semantic connections:")
        for connected_idea, similarity, connection_type in connections:
            print(f"  • {connection_type} (similarity: {similarity:.3f})")
            print(f"    {connected_idea.content[:60]}...")
    
    return captured_ideas


async def test_proactive_suggestions():
    """Test proactive suggestion generation."""
    print("\n=== Testing Proactive Suggestions ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create an idea to generate suggestions for
    idea = await idea_processor.capture_idea(
        content="Create an AI-powered personal assistant that integrates with calendar, email, and task management tools",
        source="user_input",
        context="User wants to improve personal productivity"
    )
    
    print(f"Generating suggestions for: {idea.content}")
    
    # Test with user context
    user_context = {
        "preferences": {
            "work_style": "agile",
            "team_size": "small",
            "industry": "technology"
        },
        "history": [
            "Previously worked on mobile apps",
            "Experience with API integrations",
            "Interest in machine learning"
        ]
    }
    
    suggestions = await connection_engine.generate_proactive_suggestions(idea, user_context)
    
    print(f"\nGenerated suggestions:")
    for category, items in suggestions.items():
        if items:
            print(f"\n{category.replace('_', ' ').title()}:")
            for item in items[:3]:  # Show top 3 items per category
                print(f"  • {item}")


async def test_follow_up_questions():
    """Test follow-up question generation."""
    print("\n=== Testing Follow-up Questions ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create an idea for question generation
    idea = await idea_processor.capture_idea(
        content="Develop a blockchain-based supply chain tracking system for food safety",
        source="brainstorming"
    )
    
    print(f"Generating questions for: {idea.content}")
    
    # Test different depth levels
    for depth in [1, 2, 3]:
        print(f"\nDepth Level {depth} Questions:")
        questions = await connection_engine.generate_follow_up_questions(idea, depth)
        
        for i, question_data in enumerate(questions[:4], 1):  # Show top 4 questions
            print(f"  {i}. [{question_data['type']}] {question_data['question']}")
            print(f"     Priority: {question_data['priority']:.2f}")


async def test_idea_clustering():
    """Test idea clustering functionality."""
    print("\n=== Testing Idea Clustering ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create diverse ideas for clustering
    clustering_ideas_data = [
        # Business cluster
        "Increase revenue through new customer acquisition strategies",
        "Develop pricing strategy for premium product tier",
        "Create customer loyalty program with rewards system",
        
        # Technical cluster
        "Optimize database performance using indexing strategies",
        "Implement caching layer for improved API response times",
        "Migrate legacy system to cloud-based architecture",
        
        # Product cluster
        "Design user-friendly mobile interface for elderly users",
        "Add dark mode feature to improve user experience",
        "Implement accessibility features for visually impaired users",
        
        # Mixed ideas
        "Research market trends in artificial intelligence",
        "Create automated testing framework for quality assurance"
    ]
    
    captured_ideas = []
    for content in clustering_ideas_data:
        idea = await idea_processor.capture_idea(content, source="clustering_test")
        captured_ideas.append(idea)
    
    print(f"Clustering {len(captured_ideas)} ideas...")
    
    clusters = await connection_engine.create_idea_clusters(
        captured_ideas,
        cluster_threshold=0.6
    )
    
    print(f"\nFound {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i}: {cluster['cluster_summary']}")
        print(f"  Size: {cluster['size']} ideas")
        print(f"  Category: {cluster['dominant_category'].value if cluster['dominant_category'] else 'Mixed'}")
        print(f"  Keywords: {', '.join(cluster['common_keywords'])}")
        print("  Ideas:")
        for idea in cluster['ideas']:
            print(f"    • {idea.content[:50]}...")


async def test_merge_suggestions():
    """Test idea merge suggestions."""
    print("\n=== Testing Merge Suggestions ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create very similar ideas that should be merged
    similar_ideas_data = [
        "Create a mobile app for tracking daily expenses and budgeting",
        "Build a smartphone application for personal expense management and budget tracking",
        "Develop expense tracking mobile app with budget management features",
        "Design a completely different productivity tool for time management"  # This shouldn't merge
    ]
    
    captured_ideas = []
    for content in similar_ideas_data:
        idea = await idea_processor.capture_idea(content, source="merge_test")
        captured_ideas.append(idea)
    
    print(f"Analyzing {len(captured_ideas)} ideas for merge opportunities...")
    
    merge_suggestions = await connection_engine.suggest_idea_merges(
        captured_ideas,
        merge_threshold=0.7
    )
    
    print(f"\nFound {len(merge_suggestions)} merge suggestions:")
    for i, suggestion in enumerate(merge_suggestions, 1):
        print(f"\nMerge Suggestion {i}:")
        print(f"  Confidence: {suggestion['merge_confidence']:.3f}")
        print(f"  Similarity: {suggestion['similarity_score']:.3f}")
        print(f"  Primary: {suggestion['primary_idea'].content[:50]}...")
        print(f"  Secondary: {suggestion['secondary_idea'].content[:50]}...")
        print(f"  Merged: {suggestion['suggested_merged_content'][:80]}...")
        
        if suggestion['merge_benefits']:
            print(f"  Benefits: {', '.join(suggestion['merge_benefits'])}")
        
        if suggestion['potential_issues']:
            print(f"  Issues: {', '.join(suggestion['potential_issues'])}")


async def test_idea_hierarchy():
    """Test idea hierarchy building."""
    print("\n=== Testing Idea Hierarchy ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create hierarchical ideas
    hierarchical_ideas_data = [
        # Parent ideas
        "Build a comprehensive e-commerce platform",
        "Create a customer management system",
        
        # Child ideas
        "Implement shopping cart functionality for e-commerce site",
        "Add payment processing to online store",
        "Design product catalog with search and filtering",
        "Build customer profile management interface",
        "Create customer support ticket system",
        
        # Orphaned idea
        "Research quantum computing applications"
    ]
    
    captured_ideas = []
    for content in hierarchical_ideas_data:
        idea = await idea_processor.capture_idea(content, source="hierarchy_test")
        captured_ideas.append(idea)
    
    print(f"Building hierarchy for {len(captured_ideas)} ideas...")
    
    hierarchy = await connection_engine.build_idea_hierarchy(captured_ideas)
    
    print(f"\nIdea Hierarchy:")
    print(f"  Root ideas: {len(hierarchy['root_ideas'])}")
    for root in hierarchy['root_ideas']:
        print(f"    • {root.content[:50]}...")
    
    print(f"  Parent-child relationships: {len(hierarchy['parent_child_relationships'])}")
    for parent, child, strength in hierarchy['parent_child_relationships']:
        print(f"    • {parent.content[:30]}... → {child.content[:30]}... (strength: {strength:.2f})")
    
    print(f"  Sibling groups: {len(hierarchy['sibling_groups'])}")
    for group in hierarchy['sibling_groups']:
        print(f"    • {len(group['children'])} siblings under parent")
    
    print(f"  Orphaned ideas: {len(hierarchy['orphaned_ideas'])}")
    for orphan in hierarchy['orphaned_ideas']:
        print(f"    • {orphan.content[:50]}...")


async def test_evolution_path():
    """Test idea evolution path generation."""
    print("\n=== Testing Evolution Path ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create an idea for evolution path
    idea = await idea_processor.capture_idea(
        content="Create a SaaS platform for small business inventory management with real-time tracking and analytics",
        source="business_plan"
    )
    
    print(f"Generating evolution path for: {idea.content}")
    
    evolution_path = await connection_engine.generate_idea_evolution_path(
        idea,
        target_outcome="Launch MVP within 6 months with 100 beta customers"
    )
    
    print(f"\nEvolution Path:")
    print(f"  Current Stage: {evolution_path['current_stage']}")
    
    if evolution_path['next_steps']:
        print(f"  Next Steps ({len(evolution_path['next_steps'])}):")
        for step in evolution_path['next_steps'][:5]:
            print(f"    • {step}")
    
    if evolution_path['milestones']:
        print(f"  Milestones ({len(evolution_path['milestones'])}):")
        for milestone in evolution_path['milestones'][:3]:
            print(f"    • {milestone}")
    
    if evolution_path['decision_points']:
        print(f"  Decision Points ({len(evolution_path['decision_points'])}):")
        for decision in evolution_path['decision_points'][:3]:
            print(f"    • {decision}")
    
    if evolution_path['timeline_estimate']:
        timeline = evolution_path['timeline_estimate']
        print(f"  Timeline: {timeline['estimated_weeks']} weeks")
        for phase in timeline['phases']:
            print(f"    • {phase['name']}: {phase['weeks']:.1f} weeks")


async def test_connection_performance():
    """Test performance of connection algorithms."""
    print("\n=== Testing Connection Performance ===")
    
    idea_processor = get_idea_processor()
    connection_engine = get_idea_connection_engine()
    
    # Create a larger set of ideas for performance testing
    performance_ideas = []
    idea_templates = [
        "Build a {} application for {} management",
        "Create a {} system for {} tracking",
        "Develop {} software for {} optimization",
        "Design {} platform for {} analytics",
        "Implement {} solution for {} automation"
    ]
    
    domains = ["mobile", "web", "desktop", "cloud", "AI-powered"]
    areas = ["customer", "inventory", "project", "financial", "employee", "data", "content", "workflow"]
    
    print("Creating test ideas...")
    for i, template in enumerate(idea_templates):
        for j, domain in enumerate(domains):
            for k, area in enumerate(areas[:3]):  # Limit to avoid too many ideas
                content = template.format(domain, area)
                idea = await idea_processor.capture_idea(content, source=f"perf_test_{i}_{j}_{k}")
                performance_ideas.append(idea)
    
    print(f"Created {len(performance_ideas)} ideas for performance testing")
    
    # Test semantic connection performance
    start_time = datetime.utcnow()
    test_idea = performance_ideas[0]
    connections = await connection_engine.find_semantic_connections(
        test_idea,
        performance_ideas[1:10],  # Test with 10 ideas
        similarity_threshold=0.5
    )
    connection_time = (datetime.utcnow() - start_time).total_seconds()
    
    print(f"Semantic connection analysis: {connection_time:.3f}s for 10 ideas")
    print(f"Found {len(connections)} connections")
    
    # Test clustering performance
    start_time = datetime.utcnow()
    clusters = await connection_engine.create_idea_clusters(
        performance_ideas[:15],  # Test with 15 ideas
        cluster_threshold=0.6
    )
    clustering_time = (datetime.utcnow() - start_time).total_seconds()
    
    print(f"Clustering analysis: {clustering_time:.3f}s for 15 ideas")
    print(f"Created {len(clusters)} clusters")


async def main():
    """Run all idea connection and suggestion system tests."""
    print("Starting Idea Connection and Suggestion System Tests")
    print("=" * 60)
    
    try:
        # Initialize systems
        print("Initializing systems...")
        initialize_ai_provider("simple")  # Use simple provider for testing
        db_manager = initialize_database("sqlite:///test_idea_connections.db")
        await db_manager.create_tables_async()
        initialize_vector_store("simple")
        print("✓ Systems initialized")
        
        # Run tests
        await test_semantic_connections()
        await test_proactive_suggestions()
        await test_follow_up_questions()
        await test_idea_clustering()
        await test_merge_suggestions()
        await test_idea_hierarchy()
        await test_evolution_path()
        await test_connection_performance()
        
        print("\n" + "=" * 60)
        print("Idea Connection and Suggestion System Tests Completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n✗ Tests failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())