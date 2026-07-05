"""
AI Provider abstraction layer.

ARCHITECTURAL DECISION: Provider Interface Pattern
-------------------------------------------------
We define an abstract base class that all providers must implement.
This allows:
1. Swapping between OpenRouter, Anthropic, and OpenAI seamlessly
2. Easy testing with mock providers
3. Future expansion to other providers (Google, Cohere, etc.)
"""

from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openai_provider import OpenAIProvider

__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "OpenRouterProvider",
    "AnthropicProvider",
    "OpenAIProvider",
]