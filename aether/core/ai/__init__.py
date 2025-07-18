"""
AI providers and language model integration for Aether AI Companion.
"""

from .providers import (
    AIProvider,
    SimpleAIProvider,
    OllamaProvider,
    OpenAIProvider,
    get_ai_provider,
    initialize_ai_provider
)
from .prompts import PromptManager, get_prompt_manager

__all__ = [
    "AIProvider",
    "SimpleAIProvider", 
    "OllamaProvider",
    "OpenAIProvider",
    "get_ai_provider",
    "initialize_ai_provider",
    "PromptManager",
    "get_prompt_manager",
]