"""
Prompt management and engineering for Aether AI Companion.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Template for AI prompts with variable substitution."""
    
    def __init__(self, name: str, template: str, variables: Optional[List[str]] = None):
        """
        Initialize prompt template.
        
        Args:
            name: Template name
            template: Template string with {variable} placeholders
            variables: List of expected variables
        """
        self.name = name
        self.template = template
        self.variables = variables or []
    
    def render(self, **kwargs) -> str:
        """
        Render template with provided variables.
        
        Args:
            **kwargs: Variable values
        
        Returns:
            Rendered prompt string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable {e} in template {self.name}")
            return self.template
    
    def get_info(self) -> Dict[str, Any]:
        """Get template information."""
        return {
            "name": self.name,
            "variables": self.variables,
            "template_length": len(self.template)
        }


class PromptManager:
    """Manages AI prompts and templates for different scenarios."""
    
    def __init__(self):
        """Initialize prompt manager with default templates."""
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        
        # System prompt for general conversation
        self.add_template(
            "system_general",
            """You are Aether, an intelligent AI companion designed to help with productivity, business management, and personal organization. You are knowledgeable, helpful, and proactive in offering assistance.

Key characteristics:
- You help with business planning, task management, and idea development
- You maintain context from previous conversations
- You can integrate with tools like Google Calendar and Monday.com
- You provide actionable advice and break down complex problems
- You are supportive and encouraging while being practical

Guidelines:
- Keep responses concise but comprehensive
- Ask clarifying questions when needed
- Suggest specific next steps when appropriate
- Reference previous context when relevant
- Be proactive in identifying opportunities to help""",
            []
        )
        
        # Context-aware conversation prompt
        self.add_template(
            "conversation_with_context",
            """You are Aether, an intelligent AI companion. The user has provided the following context from previous conversations:

{context}

Based on this context and the user's current message, provide a helpful and relevant response. Reference previous discussions when appropriate and build upon established topics.

User's current message: {user_input}""",
            ["context", "user_input"]
        )
        
        # Task extraction prompt
        self.add_template(
            "extract_tasks",
            """Analyze the following conversation and extract any actionable tasks or to-do items mentioned by the user. Focus on concrete actions that can be completed.

Conversation:
{conversation_text}

Please list any tasks you identify, one per line, in a clear and actionable format. If no tasks are found, respond with "No tasks identified."

Tasks:""",
            ["conversation_text"]
        )
        
        # Idea development prompt
        self.add_template(
            "develop_idea",
            """The user has shared an idea: "{idea_content}"

Help them develop this idea by:
1. Asking clarifying questions to understand the scope and goals
2. Identifying key components or requirements
3. Suggesting next steps for implementation
4. Highlighting potential challenges or considerations

Provide a structured response that helps turn this idea into actionable plans.""",
            ["idea_content"]
        )
        
        # Business planning prompt
        self.add_template(
            "business_planning",
            """The user is working on business planning and has mentioned: "{business_context}"

As their AI business companion, help them by:
- Analyzing the business opportunity or challenge
- Suggesting key metrics to track
- Recommending planning frameworks or approaches
- Identifying potential next steps
- Asking strategic questions to clarify their goals

Focus on practical, actionable advice that can help them move forward with their business objectives.""",
            ["business_context"]
        )
        
        # Memory integration prompt
        self.add_template(
            "memory_integration",
            """You have access to relevant information from previous conversations:

{memory_context}

The user is now asking: "{user_input}"

Use the context from previous conversations to provide a more personalized and relevant response. Reference past discussions when helpful, but focus on addressing their current question.""",
            ["memory_context", "user_input"]
        )
        
        # Error handling prompt
        self.add_template(
            "error_recovery",
            """I apologize, but I encountered an issue while processing your request. Let me try to help you in a different way.

Your message: "{user_input}"

Could you please:
- Rephrase your question or request
- Provide more specific details about what you're looking for
- Let me know if you'd like help with a particular aspect

I'm here to assist you with productivity, business planning, task management, and idea development.""",
            ["user_input"]
        )
        
        # Summarization prompt
        self.add_template(
            "summarize_conversation",
            """Please provide a concise summary of the following conversation, highlighting:
- Key topics discussed
- Important decisions or conclusions
- Action items or next steps identified
- Any unresolved questions or topics

Conversation:
{conversation_text}

Summary:""",
            ["conversation_text"]
        )
    
    def add_template(self, name: str, template: str, variables: Optional[List[str]] = None):
        """
        Add a new prompt template.
        
        Args:
            name: Template name
            template: Template string
            variables: Expected variables
        """
        self.templates[name] = PromptTemplate(name, template, variables)
        logger.debug(f"Added prompt template: {name}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a prompt template by name.
        
        Args:
            name: Template name
        
        Returns:
            PromptTemplate or None if not found
        """
        return self.templates.get(name)
    
    def render_prompt(self, template_name: str, **kwargs) -> str:
        """
        Render a prompt template with variables.
        
        Args:
            template_name: Name of template to render
            **kwargs: Variable values
        
        Returns:
            Rendered prompt string
        """
        template = self.get_template(template_name)
        if template:
            return template.render(**kwargs)
        else:
            logger.error(f"Template {template_name} not found")
            return f"Template {template_name} not found"
    
    def list_templates(self) -> List[str]:
        """
        List all available template names.
        
        Returns:
            List of template names
        """
        return list(self.templates.keys())
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a template.
        
        Args:
            name: Template name
        
        Returns:
            Template information dictionary
        """
        template = self.get_template(name)
        return template.get_info() if template else None
    
    def build_conversation_prompt(
        self, 
        user_input: str, 
        context: str = "", 
        memory_context: str = "",
        conversation_type: str = "general"
    ) -> str:
        """
        Build a comprehensive conversation prompt.
        
        Args:
            user_input: User's input message
            context: Conversation context
            memory_context: Relevant memory context
            conversation_type: Type of conversation (general, business, task, idea)
        
        Returns:
            Complete prompt string
        """
        prompt_parts = []
        
        # Start with system prompt
        if conversation_type == "business":
            prompt_parts.append(self.render_prompt("business_planning", business_context=user_input))
        elif conversation_type == "idea":
            prompt_parts.append(self.render_prompt("develop_idea", idea_content=user_input))
        else:
            prompt_parts.append(self.render_prompt("system_general"))
        
        # Add memory context if available
        if memory_context.strip():
            prompt_parts.append(f"\nRelevant context from previous conversations:\n{memory_context}")
        
        # Add conversation context if available
        if context.strip():
            prompt_parts.append(f"\nRecent conversation history:\n{context}")
        
        # Add current user input
        prompt_parts.append(f"\nUser: {user_input}")
        prompt_parts.append("\nAether:")
        
        return "\n".join(prompt_parts)
    
    def extract_conversation_type(self, user_input: str) -> str:
        """
        Determine conversation type based on user input.
        
        Args:
            user_input: User's input message
        
        Returns:
            Conversation type (general, business, task, idea)
        """
        user_input_lower = user_input.lower()
        
        # Business-related keywords
        business_keywords = [
            "business", "revenue", "profit", "customer", "market", "strategy",
            "dashboard", "metrics", "kpi", "analytics", "sales", "growth"
        ]
        
        # Task-related keywords
        task_keywords = [
            "task", "todo", "organize", "priority", "deadline", "schedule",
            "plan", "manage", "complete", "finish"
        ]
        
        # Idea-related keywords
        idea_keywords = [
            "idea", "concept", "innovation", "create", "build", "develop",
            "design", "feature", "product", "solution"
        ]
        
        # Check for keyword matches
        if any(keyword in user_input_lower for keyword in business_keywords):
            return "business"
        elif any(keyword in user_input_lower for keyword in task_keywords):
            return "task"
        elif any(keyword in user_input_lower for keyword in idea_keywords):
            return "idea"
        else:
            return "general"


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """
    Get global prompt manager instance.
    
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def initialize_prompt_manager() -> PromptManager:
    """
    Initialize global prompt manager.
    
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    _prompt_manager = PromptManager()
    return _prompt_manager