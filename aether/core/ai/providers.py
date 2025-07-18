"""
AI provider implementations for Aether AI Companion.
"""

import asyncio
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import httpx

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name."""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        user_input: str, 
        context: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response to user input."""
        pass
    
    @abstractmethod
    async def get_embedding(
        self,
        text: str
    ) -> List[float]:
        """Generate embedding for text."""
        pass
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get provider capabilities."""
        return {
            "chat": True,
            "embeddings": False,
            "function_calling": False,
            "streaming": False,
            "local": False
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "provider_type": self.__class__.__name__,
            "model_name": self.model_name,
            "capabilities": self.capabilities
        }


class SimpleAIProvider(AIProvider):
    """Simple AI provider for development and testing."""
    
    def __init__(self):
        """Initialize simple AI provider."""
        self._model_name = "simple-ai"
        self.responses = {
            # Greeting patterns
            r"hello|hi|hey": [
                "Hello! I'm Aether, your AI companion. How can I help you today?",
                "Hi there! I'm here to help you with your ideas, tasks, and productivity. What's on your mind?",
                "Hey! Great to see you. What would you like to work on together?"
            ],
            
            # Dashboard/business patterns
            r"dashboard|business|metrics|kpi": [
                "A business dashboard sounds like a great idea! I can help you break that down into actionable steps. What specific metrics are most important to you?",
                "Business dashboards are powerful tools for tracking performance. Would you like to start with revenue metrics, operational KPIs, or customer analytics?",
                "I'd love to help you design a comprehensive dashboard. What's your primary goal - daily monitoring, strategic planning, or team reporting?"
            ],
            
            # Task/productivity patterns
            r"task|todo|productivity|organize": [
                "I can help you organize your tasks and boost productivity! What's your biggest challenge right now - prioritization, time management, or staying focused?",
                "Task management is one of my strengths. Would you like me to help you break down a big project or organize your daily workflow?",
                "Let's get you organized! I can help prioritize tasks, set deadlines, and track your progress. What's most urgent on your list?"
            ],
            
            # Ideas/planning patterns
            r"idea|plan|project|build": [
                "I love helping with new ideas and projects! Tell me more about what you're thinking - I can help you develop it into actionable steps.",
                "That sounds like an exciting project! I can help you plan it out, identify key milestones, and break it into manageable tasks. What's the vision?",
                "Great thinking! I'm here to help turn ideas into reality. What's the core problem you're trying to solve or opportunity you want to pursue?"
            ],
            
            # Memory/context patterns
            r"remember|memory|context|previous": [
                "Yes, I remember our previous conversations and can reference them anytime. I'm designed to maintain context across all our interactions.",
                "I keep track of everything we discuss so I can provide better, more personalized assistance. What would you like me to recall?",
                "My memory system helps me understand your preferences and past decisions. I can reference any of our previous conversations - what specifically are you thinking about?"
            ],
            
            # Integration patterns
            r"calendar|google|monday|integration": [
                "I can help integrate with your existing tools like Google Calendar and Monday.com to streamline your workflow. What integration would be most helpful?",
                "Tool integration is key to productivity! I can sync with your calendar, project management tools, and other systems. Which tools do you use most?",
                "Let's connect your tools for a seamless experience. I can work with Google Calendar, Monday.com, and other platforms. What's your current setup?"
            ],
            
            # Help patterns
            r"help|what can you do|capabilities": [
                "I'm your AI companion for productivity and business management! I can help with:\\n• Capturing and organizing ideas\\n• Task management and prioritization\\n• Business planning and analysis\\n• Memory and context across conversations\\n• Integration with your existing tools\\n\\nWhat would you like to explore?",
                "I'm designed to be your intelligent assistant for:\\n• Idea development and planning\\n• Task and project management\\n• Business intelligence and dashboards\\n• Contextual memory and insights\\n• Tool integration and automation\\n\\nHow can I help you be more productive today?",
                "Think of me as your personal productivity partner! I excel at:\\n• Turning ideas into actionable plans\\n• Managing tasks and deadlines\\n• Providing business insights\\n• Remembering context from all our conversations\\n• Connecting with your favorite tools\\n\\nWhat's your biggest productivity challenge?"
            ]
        }
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    async def generate_response(
        self, 
        user_input: str, 
        context: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response to user input.
        
        Args:
            user_input: User's input message
            context: Conversation context
            metadata: Optional metadata
        
        Returns:
            AI response string
        """
        try:
            user_input_lower = user_input.lower()
            
            # Find matching pattern
            for pattern, responses in self.responses.items():
                if re.search(pattern, user_input_lower):
                    import random
                    response = random.choice(responses)
                    
                    # Add context-aware elements
                    if context and "memory" in context.lower():
                        response += "\\n\\nI can see from our conversation history that we've discussed related topics before."
                    
                    return response
            
            # Default response for unmatched input
            default_responses = [
                "That's interesting! I'd love to help you explore that further. Can you tell me more about what you're trying to accomplish?",
                "I'm here to help! Could you provide a bit more context about what you're working on or what you'd like to achieve?",
                "Thanks for sharing that with me. How can I best assist you with this? Are you looking for planning help, task organization, or something else?",
                "I want to make sure I give you the most helpful response. Could you elaborate on what specific support you're looking for?"
            ]
            
            import random
            return random.choice(default_responses)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble processing that right now. Could you try rephrasing your question?"
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding
        """
        # Simple hash-based embedding for testing
        import numpy as np
        
        # Create a simple vector based on word hashes
        dimension = 384
        vector = np.zeros(dimension)
        words = text.lower().split()
        
        for i, word in enumerate(words[:50]):  # Limit to first 50 words
            # Use hash to create pseudo-random but deterministic values
            word_hash = hash(word) % (2**31)
            
            # Distribute hash across vector dimensions
            for j in range(min(8, dimension)):  # Use up to 8 dimensions per word
                idx = (word_hash + j * i) % dimension
                vector[idx] += np.sin(word_hash + j) * 0.1
        
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get provider capabilities."""
        return {
            "chat": True,
            "embeddings": True,  # Simple embeddings are available
            "function_calling": False,
            "streaming": False,
            "local": True  # This is a local provider
        }


class OllamaProvider(AIProvider):
    """Ollama-based AI provider for local LLM integration."""
    
    def __init__(
        self,
        model_name: str = "llama2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model_name: Ollama model name
            base_url: Ollama API base URL
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
        """
        self._model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for LLM responses
        
        logger.info(f"Initialized Ollama provider with model {model_name}")
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for Aether."""
        return (
            "You are Aether, an intelligent AI companion designed to help with business management and productivity. "
            "You excel at organizing ideas, managing tasks, and providing business insights. "
            "You have a memory system that allows you to remember past conversations and reference them when relevant. "
            "You are helpful, professional, and focused on providing practical assistance. "
            "When appropriate, break down complex topics into actionable steps. "
            "If you don't know something, admit it rather than making up information."
        )
    
    async def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama availability check failed: {e}")
            return False
    
    async def generate_response(
        self, 
        user_input: str, 
        context: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response using Ollama.
        
        Args:
            user_input: User's input message
            context: Conversation context
            metadata: Optional metadata
        
        Returns:
            AI response string
        """
        try:
            # Check if Ollama is available
            if not await self._check_ollama_availability():
                logger.warning("Ollama not available, falling back to simple response")
                return "I'm sorry, but I'm having trouble connecting to my language model right now. Please try again later."
            
            # Prepare prompt with context
            prompt = user_input
            if context:
                prompt = f"{context}\\n\\nUser: {user_input}"
            
            # Prepare request payload
            payload = {
                "model": self._model_name,
                "prompt": prompt,
                "system": self.system_prompt,
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "stream": False
            }
            
            # Send request to Ollama
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "I apologize, but I encountered an error generating a response. Please try again."
            
            # Parse response
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Error generating Ollama response: {e}")
            return "I apologize, but I'm having trouble processing that right now. Could you try again?"
    
    async def get_embedding(
        self,
        text: str
    ) -> List[float]:
        """
        Generate embedding for text using Ollama.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding
        """
        try:
            # Check if Ollama is available
            if not await self._check_ollama_availability():
                logger.warning("Ollama not available for embeddings, falling back to simple embeddings")
                # Fall back to simple embeddings
                simple_provider = SimpleAIProvider()
                return await simple_provider.get_embedding(text)
            
            # Prepare request payload
            payload = {
                "model": self._model_name,
                "prompt": text
            }
            
            # Send request to Ollama embeddings API
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama embeddings API error: {response.status_code} - {response.text}")
                # Fall back to simple embeddings
                simple_provider = SimpleAIProvider()
                return await simple_provider.get_embedding(text)
            
            # Parse response
            result = response.json()
            embedding = result.get("embedding", [])
            
            if not embedding:
                logger.warning("Ollama returned empty embedding, falling back to simple embeddings")
                simple_provider = SimpleAIProvider()
                return await simple_provider.get_embedding(text)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating Ollama embedding: {e}")
            # Fall back to simple embeddings
            simple_provider = SimpleAIProvider()
            return await simple_provider.get_embedding(text)
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get provider capabilities."""
        return {
            "chat": True,
            "embeddings": True,
            "function_calling": False,  # Ollama doesn't support function calling yet
            "streaming": True,  # Ollama supports streaming
            "local": True  # This is a local provider
        }


class OpenAIProvider(AIProvider):
    """OpenAI-based AI provider."""
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model_name: OpenAI model name
            api_key: OpenAI API key
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
        """
        self._model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=60.0,  # Longer timeout for LLM responses
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"Initialized OpenAI provider with model {model_name}")
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for Aether."""
        return (
            "You are Aether, an intelligent AI companion designed to help with business management and productivity. "
            "You excel at organizing ideas, managing tasks, and providing business insights. "
            "You have a memory system that allows you to remember past conversations and reference them when relevant. "
            "You are helpful, professional, and focused on providing practical assistance. "
            "When appropriate, break down complex topics into actionable steps. "
            "If you don't know something, admit it rather than making up information."
        )
    
    async def generate_response(
        self, 
        user_input: str, 
        context: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response using OpenAI.
        
        Args:
            user_input: User's input message
            context: Conversation context
            metadata: Optional metadata
        
        Returns:
            AI response string
        """
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not available, falling back to simple response")
                return "I'm sorry, but I'm not properly configured to use the OpenAI API. Please check your API key configuration."
            
            # Prepare messages
            messages = []
            
            # Add system message
            messages.append({"role": "system", "content": self.system_prompt})
            
            # Add context if available
            if context:
                messages.append({"role": "system", "content": f"Context: {context}"})
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Prepare request payload
            payload = {
                "model": self._model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # Send request to OpenAI
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return "I apologize, but I encountered an error generating a response. Please try again."
            
            # Parse response
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return "I apologize, but I'm having trouble processing that right now. Could you try again?"
    
    async def get_embedding(
        self,
        text: str
    ) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding
        """
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not available for embeddings, falling back to simple embeddings")
                # Fall back to simple embeddings
                simple_provider = SimpleAIProvider()
                return await simple_provider.get_embedding(text)
            
            # Prepare request payload
            payload = {
                "model": "text-embedding-ada-002",
                "input": text
            }
            
            # Send request to OpenAI embeddings API
            response = await self.client.post(
                "https://api.openai.com/v1/embeddings",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI embeddings API error: {response.status_code} - {response.text}")
                # Fall back to simple embeddings
                simple_provider = SimpleAIProvider()
                return await simple_provider.get_embedding(text)
            
            # Parse response
            result = response.json()
            embedding = result.get("data", [{}])[0].get("embedding", [])
            
            if not embedding:
                logger.warning("OpenAI returned empty embedding, falling back to simple embeddings")
                simple_provider = SimpleAIProvider()
                return await simple_provider.get_embedding(text)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            # Fall back to simple embeddings
            simple_provider = SimpleAIProvider()
            return await simple_provider.get_embedding(text)
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get provider capabilities."""
        return {
            "chat": True,
            "embeddings": True,
            "function_calling": True,  # OpenAI supports function calling
            "streaming": True,  # OpenAI supports streaming
            "local": False  # This is a cloud provider
        }


# Global AI provider instance
_ai_provider: Optional[AIProvider] = None


def initialize_ai_provider(
    provider_type: str = "simple",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    system_prompt: Optional[str] = None
) -> AIProvider:
    """
    Initialize global AI provider.
    
    Args:
        provider_type: Provider type ('simple', 'ollama', 'openai')
        model_name: Model name
        api_key: API key (for OpenAI)
        base_url: Base URL (for Ollama)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        system_prompt: System prompt
    
    Returns:
        AIProvider instance
    
    Raises:
        ValueError: If provider_type is invalid
    """
    global _ai_provider
    
    if provider_type == "simple":
        _ai_provider = SimpleAIProvider()
    elif provider_type == "ollama":
        _ai_provider = OllamaProvider(
            model_name=model_name or "llama2",
            base_url=base_url or "http://localhost:11434",
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
    elif provider_type == "openai":
        _ai_provider = OpenAIProvider(
            model_name=model_name or "gpt-3.5-turbo",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
    else:
        raise ValueError(f"Invalid provider type: {provider_type}")
    
    logger.info(f"Initialized AI provider: {provider_type} with model {_ai_provider.model_name}")
    return _ai_provider


def get_ai_provider() -> AIProvider:
    """
    Get global AI provider instance.
    
    Returns:
        AIProvider instance
    """
    global _ai_provider
    if _ai_provider is None:
        # Auto-initialize with simple provider
        _ai_provider = SimpleAIProvider()
    return _ai_provider