"""
Idea connection and suggestion system for Aether AI Companion.
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter

from core.ai import get_ai_provider
from core.memory import get_memory_manager, MemoryQuery, MemoryType
from shared.utils.logging import get_logger

from .types import (
    IdeaEntry, IdeaCategory, IdeaPriority, IdeaStatus,
    IdeaConnectionResult, IdeaExpansionResult
)

logger = get_logger(__name__)


class IdeaConnectionEngine:
    """
    Advanced idea connection and suggestion system.
    
    This system provides:
    - Semantic similarity matching between ideas and existing content
    - Proactive connection suggestion algorithms
    - AI-generated follow-up questions and expansions
    - Relationship mapping and clustering
    """
    
    def __init__(self):
        """Initialize idea connection engine."""
        self.ai_provider = get_ai_provider()
        self.memory_manager = get_memory_manager()
        
        # Connection thresholds
        self.strong_connection_threshold = 0.85
        self.moderate_connection_threshold = 0.70
        self.weak_connection_threshold = 0.55
        
        # Suggestion parameters
        self.max_suggestions_per_idea = 5
        self.max_follow_up_questions = 8
        self.connection_decay_days = 30
        
        logger.info("Idea connection engine initialized")
    
    async def find_semantic_connections(
        self,
        idea: IdeaEntry,
        existing_ideas: List[IdeaEntry],
        similarity_threshold: float = 0.6
    ) -> List[Tuple[IdeaEntry, float, str]]:
        """
        Find semantic connections between an idea and existing ideas.
        
        Args:
            idea: The idea to find connections for
            existing_ideas: List of existing ideas to compare against
            similarity_threshold: Minimum similarity threshold
        
        Returns:
            List of (connected_idea, similarity_score, connection_type) tuples
        """
        try:
            connections = []
            
            # Use memory system for semantic search
            memory_query = MemoryQuery(
                query_text=idea.content,
                memory_types=[MemoryType.IDEA],
                max_results=50,
                similarity_threshold=similarity_threshold
            )
            
            memory_results = await self.memory_manager.search_memories(memory_query)
            
            # Process memory results to find connections
            for result in memory_results:
                idea_id = result.memory.metadata.get("idea_id")
                if idea_id and idea_id != idea.id:
                    # Find the corresponding idea
                    connected_idea = next(
                        (existing_idea for existing_idea in existing_ideas if existing_idea.id == idea_id),
                        None
                    )
                    
                    if connected_idea:
                        connection_type = self._determine_connection_type(
                            idea, connected_idea, result.similarity_score
                        )
                        connections.append((connected_idea, result.similarity_score, connection_type))
            
            # Sort by similarity score
            connections.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Found {len(connections)} semantic connections for idea {idea.id}")
            return connections
            
        except Exception as e:
            logger.error(f"Error finding semantic connections: {e}")
            return []
    
    async def generate_proactive_suggestions(
        self,
        idea: IdeaEntry,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """
        Generate proactive suggestions for an idea.
        
        Args:
            idea: The idea to generate suggestions for
            user_context: Optional user context (preferences, history, etc.)
        
        Returns:
            Dictionary with different types of suggestions
        """
        try:
            suggestions = {
                "related_topics": [],
                "implementation_steps": [],
                "potential_challenges": [],
                "resource_recommendations": [],
                "collaboration_opportunities": [],
                "market_insights": [],
                "technical_considerations": []
            }
            
            # Generate AI-powered suggestions
            suggestion_prompt = self._build_suggestion_prompt(idea, user_context)
            ai_response = await self.ai_provider.generate_response(
                user_input=suggestion_prompt,
                context=f"Generating suggestions for {idea.category.value} idea",
                metadata={"task": "proactive_suggestions", "idea_id": idea.id}
            )
            
            # Parse AI response into structured suggestions
            parsed_suggestions = self._parse_suggestion_response(ai_response)
            suggestions.update(parsed_suggestions)
            
            # Add category-specific suggestions
            category_suggestions = await self._generate_category_specific_suggestions(idea)
            for key, values in category_suggestions.items():
                suggestions[key].extend(values)
            
            # Add context-aware suggestions
            if user_context:
                context_suggestions = await self._generate_context_aware_suggestions(idea, user_context)
                for key, values in context_suggestions.items():
                    suggestions[key].extend(values)
            
            # Remove duplicates and limit suggestions
            for key in suggestions:
                suggestions[key] = list(set(suggestions[key]))[:self.max_suggestions_per_idea]
            
            logger.info(f"Generated proactive suggestions for idea {idea.id}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestions: {e}")
            return {}
    
    async def generate_follow_up_questions(
        self,
        idea: IdeaEntry,
        depth_level: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered follow-up questions for idea expansion.
        
        Args:
            idea: The idea to generate questions for
            depth_level: Depth of questioning (1=basic, 2=detailed, 3=expert)
        
        Returns:
            List of question dictionaries with metadata
        """
        try:
            questions = []
            
            # Generate questions based on depth level
            question_prompts = self._build_question_prompts(idea, depth_level)
            
            for prompt_type, prompt in question_prompts.items():
                ai_response = await self.ai_provider.generate_response(
                    user_input=prompt,
                    context=f"Generating {prompt_type} questions for idea",
                    metadata={"task": "follow_up_questions", "type": prompt_type}
                )
                
                # Parse questions from response
                parsed_questions = self._parse_questions_response(ai_response, prompt_type)
                questions.extend(parsed_questions)
            
            # Add category-specific questions
            category_questions = self._generate_category_questions(idea, depth_level)
            questions.extend(category_questions)
            
            # Sort by relevance and limit
            questions = self._rank_questions(questions, idea)[:self.max_follow_up_questions]
            
            logger.info(f"Generated {len(questions)} follow-up questions for idea {idea.id}")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return []
    
    async def create_idea_clusters(
        self,
        ideas: List[IdeaEntry],
        cluster_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Create clusters of related ideas using semantic similarity.
        
        Args:
            ideas: List of ideas to cluster
            cluster_threshold: Minimum similarity for clustering
        
        Returns:
            List of cluster dictionaries
        """
        try:
            if len(ideas) < 2:
                return []
            
            # Calculate similarity matrix
            similarity_matrix = await self._calculate_similarity_matrix(ideas)
            
            # Perform clustering
            clusters = self._perform_clustering(ideas, similarity_matrix, cluster_threshold)
            
            # Enhance clusters with metadata
            enhanced_clusters = []
            for cluster in clusters:
                enhanced_cluster = await self._enhance_cluster(cluster)
                enhanced_clusters.append(enhanced_cluster)
            
            logger.info(f"Created {len(enhanced_clusters)} idea clusters")
            return enhanced_clusters
            
        except Exception as e:
            logger.error(f"Error creating idea clusters: {e}")
            return []
    
    async def suggest_idea_merges(
        self,
        ideas: List[IdeaEntry],
        merge_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Suggest ideas that could be merged due to high similarity.
        
        Args:
            ideas: List of ideas to analyze
            merge_threshold: Minimum similarity for merge suggestion
        
        Returns:
            List of merge suggestion dictionaries
        """
        try:
            merge_suggestions = []
            
            # Find highly similar idea pairs
            for i, idea1 in enumerate(ideas):
                for j, idea2 in enumerate(ideas[i+1:], i+1):
                    # Calculate semantic similarity
                    similarity = await self._calculate_idea_similarity(idea1, idea2)
                    
                    if similarity >= merge_threshold:
                        merge_suggestion = {
                            "primary_idea": idea1,
                            "secondary_idea": idea2,
                            "similarity_score": similarity,
                            "merge_confidence": self._calculate_merge_confidence(idea1, idea2, similarity),
                            "suggested_merged_content": await self._generate_merged_content(idea1, idea2),
                            "merge_benefits": self._identify_merge_benefits(idea1, idea2),
                            "potential_issues": self._identify_merge_issues(idea1, idea2)
                        }
                        merge_suggestions.append(merge_suggestion)
            
            # Sort by confidence
            merge_suggestions.sort(key=lambda x: x["merge_confidence"], reverse=True)
            
            logger.info(f"Found {len(merge_suggestions)} merge suggestions")
            return merge_suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting idea merges: {e}")
            return []
    
    async def build_idea_hierarchy(
        self,
        ideas: List[IdeaEntry]
    ) -> Dict[str, Any]:
        """
        Build a hierarchical structure of ideas based on relationships.
        
        Args:
            ideas: List of ideas to organize
        
        Returns:
            Hierarchical structure dictionary
        """
        try:
            hierarchy = {
                "root_ideas": [],
                "parent_child_relationships": [],
                "sibling_groups": [],
                "orphaned_ideas": []
            }
            
            # Analyze relationships between ideas
            relationships = await self._analyze_idea_relationships(ideas)
            
            # Build parent-child relationships
            parent_child_pairs = []
            for idea1, idea2, relationship_type, strength in relationships:
                if relationship_type == "parent_child" and strength > 0.7:
                    parent_child_pairs.append((idea1, idea2, strength))
            
            # Identify root ideas (ideas with no parents)
            all_children = set(pair[1].id for pair in parent_child_pairs)
            root_ideas = [idea for idea in ideas if idea.id not in all_children]
            
            # Build hierarchy structure
            hierarchy["root_ideas"] = root_ideas
            hierarchy["parent_child_relationships"] = parent_child_pairs
            
            # Find sibling groups (ideas with same parent)
            parent_children = defaultdict(list)
            for parent, child, _ in parent_child_pairs:
                parent_children[parent.id].append(child)
            
            hierarchy["sibling_groups"] = [
                {"parent": parent_id, "children": children}
                for parent_id, children in parent_children.items()
                if len(children) > 1
            ]
            
            # Identify orphaned ideas
            connected_ideas = set()
            for parent, child, _ in parent_child_pairs:
                connected_ideas.add(parent.id)
                connected_ideas.add(child.id)
            
            hierarchy["orphaned_ideas"] = [
                idea for idea in ideas if idea.id not in connected_ideas
            ]
            
            logger.info(f"Built idea hierarchy with {len(root_ideas)} root ideas")
            return hierarchy
            
        except Exception as e:
            logger.error(f"Error building idea hierarchy: {e}")
            return {}
    
    async def generate_idea_evolution_path(
        self,
        idea: IdeaEntry,
        target_outcome: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an evolution path for an idea from concept to implementation.
        
        Args:
            idea: The idea to create evolution path for
            target_outcome: Optional target outcome description
        
        Returns:
            Evolution path dictionary
        """
        try:
            evolution_path = {
                "current_stage": self._determine_idea_stage(idea),
                "next_steps": [],
                "milestones": [],
                "decision_points": [],
                "resource_requirements": [],
                "timeline_estimate": None,
                "success_metrics": []
            }
            
            # Generate evolution steps using AI
            evolution_prompt = self._build_evolution_prompt(idea, target_outcome)
            ai_response = await self.ai_provider.generate_response(
                user_input=evolution_prompt,
                context=f"Creating evolution path for {idea.category.value} idea",
                metadata={"task": "idea_evolution", "idea_id": idea.id}
            )
            
            # Parse evolution response
            parsed_evolution = self._parse_evolution_response(ai_response)
            evolution_path.update(parsed_evolution)
            
            # Add category-specific evolution steps
            category_steps = self._get_category_evolution_steps(idea)
            evolution_path["next_steps"].extend(category_steps)
            
            # Generate timeline estimate
            evolution_path["timeline_estimate"] = self._estimate_evolution_timeline(
                idea, evolution_path["next_steps"]
            )
            
            logger.info(f"Generated evolution path for idea {idea.id}")
            return evolution_path
            
        except Exception as e:
            logger.error(f"Error generating idea evolution path: {e}")
            return {}
    
    # Private helper methods
    
    def _determine_connection_type(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry,
        similarity_score: float
    ) -> str:
        """Determine the type of connection between two ideas."""
        if similarity_score >= self.strong_connection_threshold:
            if idea1.category == idea2.category:
                return "duplicate_candidate"
            else:
                return "strong_semantic"
        elif similarity_score >= self.moderate_connection_threshold:
            if idea1.category == idea2.category:
                return "category_related"
            else:
                return "cross_category"
        elif similarity_score >= self.weak_connection_threshold:
            return "loosely_related"
        else:
            return "weak_connection"
    
    def _build_suggestion_prompt(
        self,
        idea: IdeaEntry,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for generating proactive suggestions."""
        context_info = ""
        if user_context:
            context_info = f"\nUser Context: {user_context.get('preferences', '')}"
        
        return f"""Analyze this idea and provide comprehensive suggestions:

Idea: {idea.content}
Category: {idea.category.value}
Priority: {idea.priority.value}
Keywords: {', '.join(idea.keywords)}{context_info}

Please provide suggestions in these areas:
1. Related topics and concepts to explore
2. Implementation steps and approach
3. Potential challenges and obstacles
4. Resource recommendations (tools, technologies, people)
5. Collaboration opportunities
6. Market insights and opportunities
7. Technical considerations and requirements

Format your response with clear sections and bullet points."""
    
    def _parse_suggestion_response(self, response: str) -> Dict[str, List[str]]:
        """Parse AI suggestion response into structured data."""
        suggestions = {
            "related_topics": [],
            "implementation_steps": [],
            "potential_challenges": [],
            "resource_recommendations": [],
            "collaboration_opportunities": [],
            "market_insights": [],
            "technical_considerations": []
        }
        
        current_section = None
        lines = response.split('\n')
        
        section_mapping = {
            "related": "related_topics",
            "implementation": "implementation_steps",
            "challenges": "potential_challenges",
            "obstacles": "potential_challenges",
            "resources": "resource_recommendations",
            "collaboration": "collaboration_opportunities",
            "market": "market_insights",
            "technical": "technical_considerations"
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            line_lower = line.lower()
            for keyword, section in section_mapping.items():
                if keyword in line_lower and (":" in line or line.endswith(":")):
                    current_section = section
                    break
            
            # Extract bullet points
            if line.startswith(('•', '-', '*')) or line[0:2] in ['1.', '2.', '3.', '4.', '5.']:
                if current_section:
                    clean_line = line.lstrip('•-*123456789. ')
                    if clean_line:
                        suggestions[current_section].append(clean_line)
        
        return suggestions
    
    def _build_question_prompts(
        self,
        idea: IdeaEntry,
        depth_level: int
    ) -> Dict[str, str]:
        """Build prompts for different types of questions."""
        base_info = f"Idea: {idea.content}\nCategory: {idea.category.value}"
        
        prompts = {}
        
        if depth_level >= 1:
            prompts["clarification"] = f"""{base_info}

Generate 3-4 clarification questions to better understand this idea:
- What specific aspects need more detail?
- What assumptions should be validated?
- What scope boundaries should be defined?"""
        
        if depth_level >= 2:
            prompts["exploration"] = f"""{base_info}

Generate 3-4 exploration questions to expand this idea:
- What related opportunities exist?
- What alternative approaches could work?
- What broader implications should be considered?"""
        
        if depth_level >= 3:
            prompts["implementation"] = f"""{base_info}

Generate 3-4 implementation-focused questions:
- What technical challenges need solving?
- What resources and timeline are required?
- What success metrics should be defined?
- What risks need mitigation?"""
        
        return prompts
    
    def _parse_questions_response(self, response: str, question_type: str) -> List[Dict[str, Any]]:
        """Parse AI question response into structured data."""
        questions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and ('?' in line):
                # Clean up the question
                clean_question = line.lstrip('•-*123456789. ')
                if clean_question:
                    questions.append({
                        "question": clean_question,
                        "type": question_type,
                        "priority": self._calculate_question_priority(clean_question, question_type)
                    })
        
        return questions
    
    def _generate_category_questions(
        self,
        idea: IdeaEntry,
        depth_level: int
    ) -> List[Dict[str, Any]]:
        """Generate category-specific questions."""
        questions = []
        
        category_questions = {
            IdeaCategory.BUSINESS: [
                "What is the target market for this idea?",
                "What revenue model would work best?",
                "Who are the main competitors?",
                "What's the go-to-market strategy?"
            ],
            IdeaCategory.TECHNICAL: [
                "What technologies are required?",
                "What are the scalability considerations?",
                "What security requirements exist?",
                "What integration challenges might arise?"
            ],
            IdeaCategory.PRODUCT: [
                "Who is the target user?",
                "What problem does this solve?",
                "What features are must-haves vs nice-to-haves?",
                "How will success be measured?"
            ]
        }
        
        if idea.category in category_questions:
            for question in category_questions[idea.category][:depth_level + 1]:
                questions.append({
                    "question": question,
                    "type": "category_specific",
                    "priority": 0.8
                })
        
        return questions
    
    def _rank_questions(
        self,
        questions: List[Dict[str, Any]],
        idea: IdeaEntry
    ) -> List[Dict[str, Any]]:
        """Rank questions by relevance and priority."""
        # Sort by priority score
        questions.sort(key=lambda q: q.get("priority", 0.5), reverse=True)
        return questions
    
    def _calculate_question_priority(self, question: str, question_type: str) -> float:
        """Calculate priority score for a question."""
        priority = 0.5  # Base priority
        
        # Boost for implementation questions
        if question_type == "implementation":
            priority += 0.2
        
        # Boost for questions with key terms
        key_terms = ["how", "what", "why", "when", "where", "who"]
        if any(term in question.lower() for term in key_terms):
            priority += 0.1
        
        # Boost for specific questions
        if any(term in question.lower() for term in ["specific", "exactly", "precisely"]):
            priority += 0.1
        
        return min(1.0, priority)
    
    async def _generate_category_specific_suggestions(
        self,
        idea: IdeaEntry
    ) -> Dict[str, List[str]]:
        """Generate category-specific suggestions."""
        suggestions = defaultdict(list)
        
        if idea.category == IdeaCategory.BUSINESS:
            suggestions["market_insights"].extend([
                "Conduct market research and competitive analysis",
                "Identify target customer segments",
                "Develop business model canvas"
            ])
            suggestions["resource_recommendations"].extend([
                "Business plan template",
                "Market research tools",
                "Financial modeling software"
            ])
        
        elif idea.category == IdeaCategory.TECHNICAL:
            suggestions["technical_considerations"].extend([
                "Define technical architecture",
                "Choose appropriate technology stack",
                "Plan for scalability and performance"
            ])
            suggestions["resource_recommendations"].extend([
                "Development frameworks",
                "Cloud infrastructure",
                "Testing tools"
            ])
        
        elif idea.category == IdeaCategory.PRODUCT:
            suggestions["implementation_steps"].extend([
                "Create user personas",
                "Design user journey maps",
                "Build minimum viable product (MVP)"
            ])
            suggestions["collaboration_opportunities"].extend([
                "UX/UI designers",
                "Product managers",
                "User research specialists"
            ])
        
        return dict(suggestions)
    
    async def _generate_context_aware_suggestions(
        self,
        idea: IdeaEntry,
        user_context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate suggestions based on user context."""
        suggestions = defaultdict(list)
        
        # Add suggestions based on user preferences
        preferences = user_context.get("preferences", {})
        if "agile" in str(preferences).lower():
            suggestions["implementation_steps"].append("Use agile development methodology")
        
        if "remote" in str(preferences).lower():
            suggestions["collaboration_opportunities"].append("Remote team collaboration tools")
        
        # Add suggestions based on user history
        history = user_context.get("history", [])
        if any("startup" in str(item).lower() for item in history):
            suggestions["resource_recommendations"].append("Startup accelerator programs")
        
        return dict(suggestions)
    
    async def _calculate_similarity_matrix(
        self,
        ideas: List[IdeaEntry]
    ) -> List[List[float]]:
        """Calculate similarity matrix for ideas."""
        n = len(ideas)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = await self._calculate_idea_similarity(ideas[i], ideas[j])
                matrix[i][j] = similarity
                matrix[j][i] = similarity
        
        return matrix
    
    async def _calculate_idea_similarity(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry
    ) -> float:
        """Calculate semantic similarity between two ideas."""
        try:
            # Use memory system to calculate similarity
            memory_query = MemoryQuery(
                query_text=idea1.content,
                memory_types=[MemoryType.IDEA],
                max_results=1,
                similarity_threshold=0.0
            )
            
            # This is a simplified approach - in production, you'd want more sophisticated similarity calculation
            # For now, we'll use keyword overlap and category matching
            
            # Keyword similarity
            keywords1 = set(idea1.keywords)
            keywords2 = set(idea2.keywords)
            keyword_similarity = len(keywords1 & keywords2) / max(len(keywords1 | keywords2), 1)
            
            # Category similarity
            category_similarity = 1.0 if idea1.category == idea2.category else 0.3
            
            # Content length similarity
            len1, len2 = len(idea1.content), len(idea2.content)
            length_similarity = 1.0 - abs(len1 - len2) / max(len1, len2)
            
            # Combined similarity
            similarity = (keyword_similarity * 0.5 + category_similarity * 0.3 + length_similarity * 0.2)
            
            return min(1.0, similarity)
            
        except Exception as e:
            logger.error(f"Error calculating idea similarity: {e}")
            return 0.0
    
    def _perform_clustering(
        self,
        ideas: List[IdeaEntry],
        similarity_matrix: List[List[float]],
        threshold: float
    ) -> List[List[IdeaEntry]]:
        """Perform clustering based on similarity matrix."""
        n = len(ideas)
        clusters = []
        visited = [False] * n
        
        for i in range(n):
            if not visited[i]:
                cluster = [ideas[i]]
                visited[i] = True
                
                # Find all similar ideas
                for j in range(i + 1, n):
                    if not visited[j] and similarity_matrix[i][j] >= threshold:
                        cluster.append(ideas[j])
                        visited[j] = True
                
                if len(cluster) > 1:  # Only include clusters with multiple ideas
                    clusters.append(cluster)
        
        return clusters
    
    async def _enhance_cluster(self, cluster: List[IdeaEntry]) -> Dict[str, Any]:
        """Enhance cluster with metadata and analysis."""
        # Calculate cluster statistics
        categories = Counter(idea.category for idea in cluster)
        priorities = Counter(idea.priority for idea in cluster)
        
        # Generate cluster summary
        all_content = " ".join(idea.content for idea in cluster)
        cluster_keywords = []
        for idea in cluster:
            cluster_keywords.extend(idea.keywords)
        
        common_keywords = [word for word, count in Counter(cluster_keywords).most_common(5)]
        
        return {
            "ideas": cluster,
            "size": len(cluster),
            "dominant_category": categories.most_common(1)[0][0] if categories else None,
            "dominant_priority": priorities.most_common(1)[0][0] if priorities else None,
            "common_keywords": common_keywords,
            "cluster_summary": f"Cluster of {len(cluster)} {categories.most_common(1)[0][0].value if categories else 'mixed'} ideas",
            "created_at": datetime.utcnow()
        }
    
    def _calculate_merge_confidence(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry,
        similarity: float
    ) -> float:
        """Calculate confidence score for merge suggestion."""
        confidence = similarity * 0.6  # Base similarity
        
        # Same category bonus
        if idea1.category == idea2.category:
            confidence += 0.2
        
        # Same priority bonus
        if idea1.priority == idea2.priority:
            confidence += 0.1
        
        # Recent ideas bonus
        days_diff = abs((idea1.created_at - idea2.created_at).days)
        if days_diff <= 7:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def _generate_merged_content(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry
    ) -> str:
        """Generate merged content for two similar ideas."""
        merge_prompt = f"""Merge these two similar ideas into a single, comprehensive idea:

Idea 1: {idea1.content}
Idea 2: {idea2.content}

Create a merged version that:
- Combines the best aspects of both ideas
- Eliminates redundancy
- Maintains clarity and focus
- Preserves important details from both"""
        
        try:
            merged_content = await self.ai_provider.generate_response(
                user_input=merge_prompt,
                context="Merging similar ideas",
                metadata={"task": "idea_merge"}
            )
            return merged_content
        except Exception as e:
            logger.error(f"Error generating merged content: {e}")
            return f"Combined idea: {idea1.content} + {idea2.content}"
    
    def _identify_merge_benefits(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry
    ) -> List[str]:
        """Identify benefits of merging two ideas."""
        benefits = [
            "Eliminates duplicate effort",
            "Combines complementary aspects",
            "Reduces idea fragmentation"
        ]
        
        if idea1.category == idea2.category:
            benefits.append("Consolidates category focus")
        
        if len(set(idea1.keywords) & set(idea2.keywords)) > 2:
            benefits.append("Leverages common themes")
        
        return benefits
    
    def _identify_merge_issues(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry
    ) -> List[str]:
        """Identify potential issues with merging two ideas."""
        issues = []
        
        if idea1.priority != idea2.priority:
            issues.append("Different priority levels")
        
        if idea1.category != idea2.category:
            issues.append("Different categories")
        
        if abs(len(idea1.content) - len(idea2.content)) > 100:
            issues.append("Significantly different detail levels")
        
        return issues
    
    async def _analyze_idea_relationships(
        self,
        ideas: List[IdeaEntry]
    ) -> List[Tuple[IdeaEntry, IdeaEntry, str, float]]:
        """Analyze relationships between ideas."""
        relationships = []
        
        for i, idea1 in enumerate(ideas):
            for j, idea2 in enumerate(ideas[i+1:], i+1):
                similarity = await self._calculate_idea_similarity(idea1, idea2)
                
                if similarity > 0.5:
                    relationship_type = self._determine_relationship_type(idea1, idea2, similarity)
                    relationships.append((idea1, idea2, relationship_type, similarity))
        
        return relationships
    
    def _determine_relationship_type(
        self,
        idea1: IdeaEntry,
        idea2: IdeaEntry,
        similarity: float
    ) -> str:
        """Determine the type of relationship between two ideas."""
        if similarity > 0.9:
            return "duplicate"
        elif similarity > 0.8:
            return "very_similar"
        elif len(idea1.content) > len(idea2.content) * 1.5:
            return "parent_child"
        elif len(idea2.content) > len(idea1.content) * 1.5:
            return "child_parent"
        elif idea1.category == idea2.category:
            return "sibling"
        else:
            return "related"
    
    def _determine_idea_stage(self, idea: IdeaEntry) -> str:
        """Determine the current stage of an idea."""
        if idea.status == IdeaStatus.CAPTURED:
            return "concept"
        elif idea.status == IdeaStatus.PROCESSING:
            return "analysis"
        elif idea.status == IdeaStatus.CATEGORIZED:
            return "categorized"
        elif idea.status == IdeaStatus.EXPANDED:
            return "detailed"
        elif idea.status == IdeaStatus.CONVERTED:
            return "implementation"
        else:
            return "unknown"
    
    def _build_evolution_prompt(
        self,
        idea: IdeaEntry,
        target_outcome: Optional[str] = None
    ) -> str:
        """Build prompt for idea evolution path."""
        target_info = f"\nTarget Outcome: {target_outcome}" if target_outcome else ""
        
        return f"""Create an evolution path for this idea from concept to implementation:

Idea: {idea.content}
Category: {idea.category.value}
Current Stage: {self._determine_idea_stage(idea)}{target_info}

Please provide:
1. Next immediate steps (3-5 actions)
2. Key milestones and checkpoints
3. Critical decision points
4. Resource requirements at each stage
5. Success metrics and validation criteria
6. Estimated timeline

Format with clear sections and actionable items."""
    
    def _parse_evolution_response(self, response: str) -> Dict[str, Any]:
        """Parse AI evolution response into structured data."""
        evolution = {
            "next_steps": [],
            "milestones": [],
            "decision_points": [],
            "resource_requirements": [],
            "success_metrics": []
        }
        
        current_section = None
        lines = response.split('\n')
        
        section_mapping = {
            "steps": "next_steps",
            "milestones": "milestones",
            "decision": "decision_points",
            "resources": "resource_requirements",
            "metrics": "success_metrics",
            "success": "success_metrics"
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            line_lower = line.lower()
            for keyword, section in section_mapping.items():
                if keyword in line_lower and (":" in line or line.endswith(":")):
                    current_section = section
                    break
            
            # Extract items
            if line.startswith(('•', '-', '*')) or line[0:2] in ['1.', '2.', '3.', '4.', '5.']:
                if current_section:
                    clean_line = line.lstrip('•-*123456789. ')
                    if clean_line:
                        evolution[current_section].append(clean_line)
        
        return evolution
    
    def _get_category_evolution_steps(self, idea: IdeaEntry) -> List[str]:
        """Get category-specific evolution steps."""
        steps = []
        
        if idea.category == IdeaCategory.BUSINESS:
            steps.extend([
                "Validate market demand",
                "Develop business model",
                "Create financial projections"
            ])
        elif idea.category == IdeaCategory.TECHNICAL:
            steps.extend([
                "Define technical requirements",
                "Choose technology stack",
                "Create proof of concept"
            ])
        elif idea.category == IdeaCategory.PRODUCT:
            steps.extend([
                "Define user requirements",
                "Create wireframes/mockups",
                "Build MVP"
            ])
        
        return steps
    
    def _estimate_evolution_timeline(
        self,
        idea: IdeaEntry,
        steps: List[str]
    ) -> Dict[str, Any]:
        """Estimate timeline for idea evolution."""
        # Simple timeline estimation based on category and complexity
        base_weeks = {
            IdeaCategory.BUSINESS: 8,
            IdeaCategory.TECHNICAL: 12,
            IdeaCategory.PRODUCT: 10,
            IdeaCategory.CREATIVE: 6,
            IdeaCategory.RESEARCH: 16
        }
        
        estimated_weeks = base_weeks.get(idea.category, 8)
        
        # Adjust based on number of steps
        if len(steps) > 10:
            estimated_weeks += 4
        elif len(steps) < 5:
            estimated_weeks -= 2
        
        return {
            "estimated_weeks": max(2, estimated_weeks),
            "phases": [
                {"name": "Planning", "weeks": estimated_weeks * 0.2},
                {"name": "Development", "weeks": estimated_weeks * 0.6},
                {"name": "Testing", "weeks": estimated_weeks * 0.2}
            ]
        }


# Global connection engine instance
_connection_engine: Optional[IdeaConnectionEngine] = None


def get_idea_connection_engine() -> IdeaConnectionEngine:
    """
    Get global idea connection engine instance.
    
    Returns:
        IdeaConnectionEngine instance
    """
    global _connection_engine
    if _connection_engine is None:
        _connection_engine = IdeaConnectionEngine()
    return _connection_engine