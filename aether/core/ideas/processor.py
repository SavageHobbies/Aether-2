"""
Idea capture and processing engine for Aether AI Companion.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ai import get_ai_provider
from core.memory import get_memory_manager, MemoryType
from core.database import get_database_manager
from shared.utils.logging import get_logger

from .types import (
    IdeaEntry, IdeaQuery, IdeaSearchResult, IdeaProcessingResult,
    IdeaExpansionResult, IdeaConnectionResult, IdeaStats,
    IdeaCategory, IdeaPriority, IdeaStatus
)
from .connections import get_idea_connection_engine
from .database_helpers import db_idea_to_entry, priority_to_score, score_to_priority, build_idea_filters

logger = get_logger(__name__)


class IdeaProcessor:
    """
    Processes ideas with automatic categorization, keyword extraction, and metadata generation.
    
    This system provides:
    - Rapid idea ingestion with automatic timestamping
    - NLP processing for categorization and keyword extraction
    - Metadata generation for source tracking and context
    - Idea expansion and connection suggestions
    """
    
    def __init__(self):
        """Initialize idea processor."""
        self.ai_provider = get_ai_provider()
        self.memory_manager = get_memory_manager()
        self.db_manager = get_database_manager()
        self.connection_engine = get_idea_connection_engine()
        
        # Processing configuration
        self.max_keywords = 10
        self.min_keyword_length = 3
        self.category_confidence_threshold = 0.6
        self.connection_similarity_threshold = 0.7
        
        # Category keywords for classification
        self.category_keywords = {
            IdeaCategory.BUSINESS: [
                "revenue", "profit", "market", "customer", "sales", "business model",
                "strategy", "competition", "growth", "monetization", "roi", "kpi"
            ],
            IdeaCategory.TECHNICAL: [
                "code", "algorithm", "database", "api", "framework", "architecture",
                "performance", "security", "deployment", "testing", "debugging", "optimization"
            ],
            IdeaCategory.CREATIVE: [
                "design", "art", "creative", "visual", "aesthetic", "brand", "logo",
                "color", "typography", "layout", "user experience", "interface"
            ],
            IdeaCategory.PRODUCTIVITY: [
                "efficiency", "workflow", "automation", "process", "tool", "time management",
                "organization", "productivity", "streamline", "optimize", "simplify"
            ],
            IdeaCategory.PRODUCT: [
                "feature", "product", "user", "functionality", "requirement", "specification",
                "prototype", "mvp", "roadmap", "release", "version", "enhancement"
            ],
            IdeaCategory.MARKETING: [
                "marketing", "promotion", "advertising", "campaign", "social media", "content",
                "seo", "brand", "audience", "engagement", "conversion", "analytics"
            ],
            IdeaCategory.RESEARCH: [
                "research", "study", "analysis", "data", "experiment", "hypothesis",
                "investigation", "survey", "findings", "methodology", "evidence"
            ]
        }
        
        # Add helper method references
        self._db_idea_to_entry = db_idea_to_entry
        self._priority_to_score = priority_to_score
        
        logger.info("Idea processor initialized")
    
    async def capture_idea(
        self,
        content: str,
        source: Optional[str] = None,
        context: Optional[str] = None,
        auto_process: bool = True
    ) -> IdeaEntry:
        """
        Capture a new idea with automatic timestamping.
        
        Args:
            content: The idea content
            source: Source of the idea (conversation_id, voice_input, etc.)
            context: Additional context about the idea
            auto_process: Whether to automatically process the idea
        
        Returns:
            IdeaEntry: The captured idea
        """
        try:
            # Create idea entry
            idea = IdeaEntry(
                id=str(uuid.uuid4()),
                content=content.strip(),
                source=source,
                context=context,
                status=IdeaStatus.CAPTURED
            )
            
            # Store in database
            await self._store_idea_in_db(idea)
            
            # Auto-process if requested
            if auto_process:
                processing_result = await self.process_idea(idea.id)
                if processing_result.success:
                    idea = processing_result.idea
            
            # Store in memory system for semantic search
            await self.memory_manager.store_memory(
                content=f"Idea: {idea.content}",
                memory_type=MemoryType.IDEA,
                metadata={
                    "idea_id": idea.id,
                    "category": idea.category.value,
                    "priority": idea.priority.value,
                    "source": source,
                    "keywords": idea.keywords,
                    "tags": idea.tags
                },
                importance_score=self._calculate_idea_importance(idea),
                tags=idea.tags + [idea.category.value, idea.priority.value],
                source=f"idea_{idea.id}"
            )
            
            logger.info(f"Captured idea {idea.id}: {content[:50]}...")
            return idea
            
        except Exception as e:
            logger.error(f"Error capturing idea: {e}")
            raise
    
    async def process_idea(self, idea_id: str) -> IdeaProcessingResult:
        """
        Process an idea with NLP analysis for categorization and keyword extraction.
        
        Args:
            idea_id: ID of the idea to process
        
        Returns:
            IdeaProcessingResult: Processing results
        """
        start_time = datetime.utcnow()
        
        try:
            # Get idea from database
            idea = await self._get_idea_by_id(idea_id)
            if not idea:
                return IdeaProcessingResult(
                    idea=IdeaEntry(),
                    processing_time_ms=0,
                    extracted_keywords=[],
                    suggested_categories=[],
                    success=False,
                    error_message=f"Idea {idea_id} not found"
                )
            
            # Update status
            idea.status = IdeaStatus.PROCESSING
            await self._update_idea_in_db(idea)
            
            # Extract keywords
            extracted_keywords = await self._extract_keywords(idea.content)
            
            # Categorize idea
            suggested_categories = await self._categorize_idea(idea.content, extracted_keywords)
            
            # Generate title if not provided
            generated_title = None
            if not idea.title:
                generated_title = await self._generate_title(idea.content)
                idea.title = generated_title
            
            # Generate tags
            suggested_tags = await self._generate_tags(idea.content, extracted_keywords)
            
            # Analyze context
            context_analysis = None
            if idea.context:
                context_analysis = await self._analyze_context(idea.content, idea.context)
            
            # Update idea with processing results
            idea.extracted_keywords = extracted_keywords
            idea.keywords = extracted_keywords[:self.max_keywords]
            idea.suggested_categories = [cat for cat, _ in suggested_categories]
            
            # Set primary category (highest confidence)
            if suggested_categories:
                primary_category, confidence = suggested_categories[0]
                if confidence >= self.category_confidence_threshold:
                    idea.category = primary_category
                    idea.confidence_score = confidence
            
            # Add suggested tags
            idea.tags.extend(suggested_tags)
            idea.tags = list(set(idea.tags))  # Remove duplicates
            
            # Update status and timestamps
            idea.status = IdeaStatus.CATEGORIZED
            idea.processed_at = datetime.utcnow()
            idea.updated_at = datetime.utcnow()
            
            # Save updated idea
            await self._update_idea_in_db(idea)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = IdeaProcessingResult(
                idea=idea,
                processing_time_ms=processing_time,
                extracted_keywords=extracted_keywords,
                suggested_categories=suggested_categories,
                generated_title=generated_title,
                suggested_tags=suggested_tags,
                context_analysis=context_analysis,
                success=True
            )
            
            logger.info(f"Processed idea {idea_id} in {processing_time:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error processing idea {idea_id}: {e}")
            return IdeaProcessingResult(
                idea=IdeaEntry(),
                processing_time_ms=0,
                extracted_keywords=[],
                suggested_categories=[],
                success=False,
                error_message=str(e)
            )
    
    async def search_ideas(self, query: IdeaQuery) -> List[IdeaSearchResult]:
        """
        Search ideas using various filters and semantic similarity.
        
        Args:
            query: Search query parameters
        
        Returns:
            List of matching ideas with relevance scores
        """
        try:
            results = []
            
            # Get ideas from database with basic filters
            ideas = await self._search_ideas_in_db(query)
            
            # If we have query text, use semantic search
            if query.query_text:
                # Search in memory system for semantic matching
                from core.memory import MemoryQuery
                memory_query = MemoryQuery(
                    query_text=query.query_text,
                    memory_types=[MemoryType.IDEA],
                    max_results=query.max_results * 2,
                    similarity_threshold=query.similarity_threshold
                )
                
                memory_results = await self.memory_manager.search_memories(memory_query)
                
                # Get idea IDs from memory results
                memory_idea_ids = set()
                memory_scores = {}
                for result in memory_results:
                    idea_id = result.memory.metadata.get("idea_id")
                    if idea_id:
                        memory_idea_ids.add(idea_id)
                        memory_scores[idea_id] = result.similarity_score
                
                # Filter ideas to include only those found in semantic search
                if memory_idea_ids:
                    ideas = [idea for idea in ideas if idea.id in memory_idea_ids]
            
            # Create search results with scoring
            for idea in ideas:
                similarity_score = memory_scores.get(idea.id, 0.0) if query.query_text else 1.0
                relevance_score = self._calculate_idea_relevance(idea, query, similarity_score)
                match_reasons = self._generate_match_reasons(idea, query)
                
                results.append(IdeaSearchResult(
                    idea=idea,
                    similarity_score=similarity_score,
                    relevance_score=relevance_score,
                    match_reasons=match_reasons
                ))
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Include related ideas if requested
            if query.include_related:
                results = await self._include_related_ideas(results, query.max_results)
            
            # Limit results
            results = results[:query.max_results]
            
            logger.info(f"Found {len(results)} ideas for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching ideas: {e}")
            return []
    
    async def expand_idea(self, idea_id: str) -> IdeaExpansionResult:
        """
        Expand an idea with AI-generated follow-up questions and suggestions.
        
        Args:
            idea_id: ID of the idea to expand
        
        Returns:
            IdeaExpansionResult: Expansion results
        """
        try:
            # Get idea from database
            idea = await self._get_idea_by_id(idea_id)
            if not idea:
                return IdeaExpansionResult(
                    original_idea=IdeaEntry(),
                    expanded_content="",
                    follow_up_questions=[],
                    related_concepts=[],
                    potential_challenges=[],
                    implementation_suggestions=[],
                    success=False,
                    error_message=f"Idea {idea_id} not found"
                )
            
            # Generate expansion using AI
            expansion_prompt = self._build_expansion_prompt(idea)
            expansion_response = await self.ai_provider.generate_response(
                user_input=expansion_prompt,
                context=f"Expanding idea: {idea.content}",
                metadata={"task": "idea_expansion", "category": idea.category.value}
            )
            
            # Parse expansion response
            expansion_data = self._parse_expansion_response(expansion_response)
            
            # Update idea status
            idea.status = IdeaStatus.EXPANDED
            idea.updated_at = datetime.utcnow()
            await self._update_idea_in_db(idea)
            
            result = IdeaExpansionResult(
                original_idea=idea,
                expanded_content=expansion_data.get("expanded_content", ""),
                follow_up_questions=expansion_data.get("follow_up_questions", []),
                related_concepts=expansion_data.get("related_concepts", []),
                potential_challenges=expansion_data.get("potential_challenges", []),
                implementation_suggestions=expansion_data.get("implementation_suggestions", []),
                success=True
            )
            
            logger.info(f"Expanded idea {idea_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error expanding idea {idea_id}: {e}")
            return IdeaExpansionResult(
                original_idea=IdeaEntry(),
                expanded_content="",
                follow_up_questions=[],
                related_concepts=[],
                potential_challenges=[],
                implementation_suggestions=[],
                success=False,
                error_message=str(e)
            )
    
    async def find_idea_connections(self, idea_id: str) -> IdeaConnectionResult:
        """
        Find connections between ideas using semantic similarity.
        
        Args:
            idea_id: ID of the idea to find connections for
        
        Returns:
            IdeaConnectionResult: Connection analysis results
        """
        try:
            # Get idea from database
            idea = await self._get_idea_by_id(idea_id)
            if not idea:
                return IdeaConnectionResult(
                    idea=IdeaEntry(),
                    connections=[],
                    connection_summary="Idea not found"
                )
            
            # Search for similar ideas
            query = IdeaQuery(
                query_text=idea.content,
                max_results=20,
                similarity_threshold=self.connection_similarity_threshold
            )
            
            similar_ideas = await self.search_ideas(query)
            
            # Filter out the original idea and build connections
            connections = []
            for result in similar_ideas:
                if result.idea.id != idea_id:
                    connection_type = self._determine_connection_type(idea, result.idea)
                    connections.append((
                        result.idea.id,
                        result.similarity_score,
                        connection_type
                    ))
            
            # Generate connection summary
            connection_summary = await self._generate_connection_summary(idea, connections)
            
            # Suggest merges and hierarchies
            suggested_merges = []
            suggested_hierarchies = []
            
            for conn_id, similarity, conn_type in connections:
                if similarity > 0.9 and conn_type == "duplicate":
                    suggested_merges.append(conn_id)
                elif conn_type in ["parent", "child"]:
                    if conn_type == "parent":
                        suggested_hierarchies.append((conn_id, idea_id))
                    else:
                        suggested_hierarchies.append((idea_id, conn_id))
            
            result = IdeaConnectionResult(
                idea=idea,
                connections=connections,
                connection_summary=connection_summary,
                suggested_merges=suggested_merges,
                suggested_hierarchies=suggested_hierarchies
            )
            
            logger.info(f"Found {len(connections)} connections for idea {idea_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error finding connections for idea {idea_id}: {e}")
            return IdeaConnectionResult(
                idea=IdeaEntry(),
                connections=[],
                connection_summary=f"Error: {str(e)}"
            )
    
    async def get_idea_stats(self) -> IdeaStats:
        """
        Get statistics about the idea system.
        
        Returns:
            IdeaStats: System statistics
        """
        try:
            # Get basic counts
            total_ideas = await self._count_ideas()
            ideas_by_category = await self._count_ideas_by_category()
            ideas_by_priority = await self._count_ideas_by_priority()
            ideas_by_status = await self._count_ideas_by_status()
            ideas_by_source = await self._count_ideas_by_source()
            
            # Get processing statistics
            avg_processing_time = await self._get_average_processing_time()
            
            # Get tag and keyword statistics
            most_active_tags = await self._get_most_active_tags()
            most_common_keywords = await self._get_most_common_keywords()
            
            # Get conversion rates
            conversion_rates = await self._get_conversion_rates()
            
            # Get recent activity
            recent_activity = await self._get_recent_activity()
            
            return IdeaStats(
                total_ideas=total_ideas,
                ideas_by_category=ideas_by_category,
                ideas_by_priority=ideas_by_priority,
                ideas_by_status=ideas_by_status,
                ideas_by_source=ideas_by_source,
                average_processing_time_ms=avg_processing_time,
                most_active_tags=most_active_tags,
                most_common_keywords=most_common_keywords,
                conversion_rates=conversion_rates,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Error getting idea stats: {e}")
            return IdeaStats(
                total_ideas=0,
                ideas_by_category={},
                ideas_by_priority={},
                ideas_by_status={},
                ideas_by_source={},
                average_processing_time_ms=0.0,
                most_active_tags=[],
                most_common_keywords=[],
                conversion_rates={},
                recent_activity=[]
            )
    
    # Private helper methods
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from idea content."""
        # Simple keyword extraction using regex and common patterns
        # In a production system, this could use more sophisticated NLP
        
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through", "during",
            "before", "after", "above", "below", "between", "among", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "must", "can",
            "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they"
        }
        
        # Extract words and phrases
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Filter out stop words and short words
        keywords = [
            word for word in words 
            if word not in stop_words and len(word) >= self.min_keyword_length
        ]
        
        # Count frequency and return most common
        from collections import Counter
        word_counts = Counter(keywords)
        
        # Also look for multi-word phrases
        phrases = re.findall(r'\b[a-zA-Z]+\s+[a-zA-Z]+\b', content.lower())
        phrase_keywords = [
            phrase for phrase in phrases
            if not any(stop_word in phrase.split() for stop_word in stop_words)
        ]
        
        # Combine and return top keywords
        all_keywords = list(word_counts.keys()) + phrase_keywords
        return all_keywords[:self.max_keywords]
    
    async def _categorize_idea(self, content: str, keywords: List[str]) -> List[Tuple[IdeaCategory, float]]:
        """Categorize idea based on content and keywords."""
        category_scores = {}
        content_lower = content.lower()
        
        # Score categories based on keyword matches
        for category, category_keywords in self.category_keywords.items():
            score = 0.0
            matches = 0
            
            for keyword in category_keywords:
                if keyword in content_lower:
                    score += 1.0
                    matches += 1
                
                # Check extracted keywords too
                for extracted_keyword in keywords:
                    if keyword in extracted_keyword or extracted_keyword in keyword:
                        score += 0.5
                        matches += 1
            
            # Normalize score
            if matches > 0:
                category_scores[category] = score / len(category_keywords)
        
        # Sort by score
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_categories[:3]  # Return top 3 categories
    
    async def _generate_title(self, content: str) -> str:
        """Generate a title for the idea."""
        # Simple title generation - take first sentence or first few words
        sentences = content.split('.')
        first_sentence = sentences[0].strip()
        
        if len(first_sentence) <= 50:
            return first_sentence
        
        # If first sentence is too long, take first few words
        words = first_sentence.split()
        return ' '.join(words[:8]) + ('...' if len(words) > 8 else '')
    
    async def _generate_tags(self, content: str, keywords: List[str]) -> List[str]:
        """Generate tags for the idea."""
        tags = []
        
        # Add some keywords as tags
        tags.extend(keywords[:5])
        
        # Add category-based tags
        content_lower = content.lower()
        if any(word in content_lower for word in ["app", "mobile", "software"]):
            tags.append("development")
        if any(word in content_lower for word in ["user", "customer", "client"]):
            tags.append("user-focused")
        if any(word in content_lower for word in ["improve", "better", "enhance"]):
            tags.append("improvement")
        if any(word in content_lower for word in ["new", "create", "build"]):
            tags.append("creation")
        
        return list(set(tags))  # Remove duplicates
    
    async def _analyze_context(self, content: str, context: str) -> str:
        """Analyze the context of an idea."""
        # Simple context analysis
        analysis_parts = []
        
        if "conversation" in context.lower():
            analysis_parts.append("Generated during conversation")
        if "meeting" in context.lower():
            analysis_parts.append("Originated from meeting discussion")
        if "brainstorm" in context.lower():
            analysis_parts.append("Part of brainstorming session")
        
        return "; ".join(analysis_parts) if analysis_parts else "General context"
    
    def _calculate_idea_importance(self, idea: IdeaEntry) -> float:
        """Calculate importance score for memory storage."""
        importance = 0.5  # Base importance
        
        # Increase for high priority
        if idea.priority == IdeaPriority.URGENT:
            importance += 0.3
        elif idea.priority == IdeaPriority.HIGH:
            importance += 0.2
        
        # Increase for business/technical categories
        if idea.category in [IdeaCategory.BUSINESS, IdeaCategory.TECHNICAL, IdeaCategory.PRODUCT]:
            importance += 0.2
        
        # Increase for longer, more detailed ideas
        if len(idea.content) > 100:
            importance += 0.1
        
        return min(1.0, importance)
    
    def _calculate_idea_relevance(self, idea: IdeaEntry, query: IdeaQuery, similarity_score: float) -> float:
        """Calculate relevance score for search results."""
        relevance = similarity_score * 0.6  # Base similarity
        
        # Add priority bonus
        priority_bonus = {
            IdeaPriority.URGENT: 0.3,
            IdeaPriority.HIGH: 0.2,
            IdeaPriority.MEDIUM: 0.1,
            IdeaPriority.LOW: 0.0
        }
        relevance += priority_bonus.get(idea.priority, 0.0)
        
        # Add recency bonus
        days_old = (datetime.utcnow() - idea.created_at).days
        recency_bonus = max(0, 0.1 - (days_old / 30) * 0.1)  # Decay over 30 days
        relevance += recency_bonus
        
        return min(1.0, relevance)
    
    def _generate_match_reasons(self, idea: IdeaEntry, query: IdeaQuery) -> List[str]:
        """Generate reasons why an idea matched the query."""
        reasons = []
        
        if query.categories and idea.category in query.categories:
            reasons.append(f"Category: {idea.category.value}")
        
        if query.priorities and idea.priority in query.priorities:
            reasons.append(f"Priority: {idea.priority.value}")
        
        if query.tags:
            matching_tags = set(query.tags) & set(idea.tags)
            if matching_tags:
                reasons.append(f"Tags: {', '.join(matching_tags)}")
        
        if query.keywords:
            matching_keywords = set(query.keywords) & set(idea.keywords)
            if matching_keywords:
                reasons.append(f"Keywords: {', '.join(matching_keywords)}")
        
        if query.query_text:
            reasons.append("Content similarity")
        
        return reasons
    
    def _build_expansion_prompt(self, idea: IdeaEntry) -> str:
        """Build prompt for idea expansion."""
        return f"""Please expand on this idea and provide detailed analysis:

Idea: {idea.content}
Category: {idea.category.value}
Keywords: {', '.join(idea.keywords)}

Please provide:
1. Expanded description of the idea
2. 3-5 follow-up questions to explore further
3. Related concepts and technologies
4. Potential challenges or obstacles
5. Implementation suggestions or next steps

Format your response clearly with sections."""
    
    def _parse_expansion_response(self, response: str) -> Dict[str, Any]:
        """Parse AI expansion response into structured data."""
        # Simple parsing - in production, this could be more sophisticated
        sections = {
            "expanded_content": "",
            "follow_up_questions": [],
            "related_concepts": [],
            "potential_challenges": [],
            "implementation_suggestions": []
        }
        
        current_section = "expanded_content"
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if "follow-up" in line.lower() or "questions" in line.lower():
                current_section = "follow_up_questions"
            elif "related" in line.lower() or "concepts" in line.lower():
                current_section = "related_concepts"
            elif "challenges" in line.lower() or "obstacles" in line.lower():
                current_section = "potential_challenges"
            elif "implementation" in line.lower() or "suggestions" in line.lower():
                current_section = "implementation_suggestions"
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')):
                # This is a list item
                clean_line = re.sub(r'^[\d\.\-\•\s]+', '', line)
                if current_section in ["follow_up_questions", "related_concepts", "potential_challenges", "implementation_suggestions"]:
                    sections[current_section].append(clean_line)
            else:
                # Regular content
                if current_section == "expanded_content":
                    sections[current_section] += line + " "
        
        return sections
    
    def _determine_connection_type(self, idea1: IdeaEntry, idea2: IdeaEntry) -> str:
        """Determine the type of connection between two ideas."""
        # Simple connection type determination
        if idea1.category == idea2.category:
            return "similar_category"
        
        # Check for hierarchical relationships
        if len(idea1.content) > len(idea2.content) * 2:
            return "parent"
        elif len(idea2.content) > len(idea1.content) * 2:
            return "child"
        
        # Check for complementary ideas
        if any(keyword in idea2.keywords for keyword in idea1.keywords):
            return "complementary"
        
        return "related"
    
    async def _generate_connection_summary(self, idea: IdeaEntry, connections: List[Tuple[str, float, str]]) -> str:
        """Generate a summary of idea connections."""
        if not connections:
            return "No significant connections found."
        
        connection_types = {}
        for _, _, conn_type in connections:
            connection_types[conn_type] = connection_types.get(conn_type, 0) + 1
        
        summary_parts = []
        for conn_type, count in connection_types.items():
            summary_parts.append(f"{count} {conn_type} connection{'s' if count > 1 else ''}")
        
        return f"Found {len(connections)} total connections: " + ", ".join(summary_parts)
    
    # Database interaction methods (placeholders)
    
    async def _store_idea_in_db(self, idea: IdeaEntry) -> None:
        """Store idea in database."""
        try:
            from core.database.models import Idea
            from sqlalchemy import select
            
            async with self.db_manager.get_async_session() as session:
                # Create database model
                db_idea = Idea(
                    id=idea.id,
                    content=idea.content,
                    source=idea.source or "unknown",
                    processed=idea.status != IdeaStatus.CAPTURED,
                    category=idea.category.value,
                    priority_score=self._priority_to_score(idea.priority),
                    extra_metadata={
                        "title": idea.title,
                        "keywords": idea.keywords,
                        "tags": idea.tags,
                        "context": idea.context,
                        "status": idea.status.value,
                        "priority": idea.priority.value,
                        "confidence_score": idea.confidence_score,
                        "extracted_keywords": idea.extracted_keywords,
                        "suggested_categories": [cat.value for cat in idea.suggested_categories],
                        "related_ideas": idea.related_ideas,
                        "parent_idea": idea.parent_idea,
                        "sub_ideas": idea.sub_ideas,
                        "converted_to_tasks": idea.converted_to_tasks,
                        "converted_to_events": idea.converted_to_events
                    }
                )
                
                session.add(db_idea)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error storing idea in database: {e}")
            raise
    
    async def _get_idea_by_id(self, idea_id: str) -> Optional[IdeaEntry]:
        """Get idea by ID from database."""
        try:
            from core.database.models import Idea
            from sqlalchemy import select
            
            async with self.db_manager.get_async_session() as session:
                stmt = select(Idea).where(Idea.id == idea_id)
                result = await session.execute(stmt)
                db_idea = result.scalar_one_or_none()
                
                if db_idea:
                    return self._db_idea_to_entry(db_idea)
                return None
                
        except Exception as e:
            logger.error(f"Error getting idea by ID: {e}")
            return None
    
    async def _update_idea_in_db(self, idea: IdeaEntry) -> None:
        """Update idea in database."""
        try:
            from core.database.models import Idea
            from sqlalchemy import select
            
            async with self.db_manager.get_async_session() as session:
                stmt = select(Idea).where(Idea.id == idea.id)
                result = await session.execute(stmt)
                db_idea = result.scalar_one_or_none()
                
                if db_idea:
                    # Update fields
                    db_idea.content = idea.content
                    db_idea.processed = idea.status != IdeaStatus.CAPTURED
                    db_idea.category = idea.category.value
                    db_idea.priority_score = self._priority_to_score(idea.priority)
                    db_idea.extra_metadata = {
                        "title": idea.title,
                        "keywords": idea.keywords,
                        "tags": idea.tags,
                        "context": idea.context,
                        "status": idea.status.value,
                        "priority": idea.priority.value,
                        "confidence_score": idea.confidence_score,
                        "extracted_keywords": idea.extracted_keywords,
                        "suggested_categories": [cat.value for cat in idea.suggested_categories],
                        "related_ideas": idea.related_ideas,
                        "parent_idea": idea.parent_idea,
                        "sub_ideas": idea.sub_ideas,
                        "converted_to_tasks": idea.converted_to_tasks,
                        "converted_to_events": idea.converted_to_events
                    }
                    
                    await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating idea in database: {e}")
            raise
    
    async def _search_ideas_in_db(self, query: IdeaQuery) -> List[IdeaEntry]:
        """Search ideas in database."""
        # Placeholder implementation
        return []
    
    async def _count_ideas(self) -> int:
        """Count total ideas."""
        return 0
    
    async def _count_ideas_by_category(self) -> Dict[IdeaCategory, int]:
        """Count ideas by category."""
        return {}
    
    async def _count_ideas_by_priority(self) -> Dict[IdeaPriority, int]:
        """Count ideas by priority."""
        return {}
    
    async def _count_ideas_by_status(self) -> Dict[IdeaStatus, int]:
        """Count ideas by status."""
        return {}
    
    async def _count_ideas_by_source(self) -> Dict[str, int]:
        """Count ideas by source."""
        return {}
    
    async def _get_average_processing_time(self) -> float:
        """Get average processing time."""
        return 0.0
    
    async def _get_most_active_tags(self) -> List[Tuple[str, int]]:
        """Get most active tags."""
        return []
    
    async def _get_most_common_keywords(self) -> List[Tuple[str, int]]:
        """Get most common keywords."""
        return []
    
    async def _get_conversion_rates(self) -> Dict[str, float]:
        """Get conversion rates."""
        return {}
    
    async def _get_recent_activity(self) -> List[Tuple[datetime, str, str]]:
        """Get recent activity."""
        return []
    
    async def _include_related_ideas(self, results: List[IdeaSearchResult], max_results: int) -> List[IdeaSearchResult]:
        """Include related ideas in search results."""
        # Placeholder implementation
        return results


# Global idea processor instance
_idea_processor: Optional[IdeaProcessor] = None


def get_idea_processor() -> IdeaProcessor:
    """
    Get global idea processor instance.
    
    Returns:
        IdeaProcessor instance
    """
    global _idea_processor
    if _idea_processor is None:
        _idea_processor = IdeaProcessor()
    return _idea_processor