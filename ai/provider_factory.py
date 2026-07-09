"""
Provider Factory for AI Engine.

ARCHITECTURAL DECISION: Factory Pattern
-------------------------------------------
Extracts provider selection logic to a single place to avoid duplication
across AI modules (generator, faq_generator, seo_title, etc.).

This follows the DRY principle and makes adding new providers easier.
"""

from typing import Optional

from config import get_settings
from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openrouter_provider import OpenRouterProvider

# Lazy import for OpenAI (optional dependency)
def _get_openai_provider() -> Optional[type]:
    """Lazy load OpenAI provider if available."""
    try:
        from ai.providers.openai_provider import OpenAIProvider
        return OpenAIProvider
    except ImportError:
        return None


def create_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> BaseProvider:
    """
    Create an AI provider based on configuration or parameters.

    This is the single source of truth for provider selection.
    All AI modules should use this function instead of duplicating logic.

    Args:
        provider_name: Provider to use ("openrouter", "anthropic", "openai")
        model: Model name to use
        api_key: API key (uses settings if not provided)
        max_tokens: Max tokens (uses settings default if not provided)
        temperature: Temperature (uses settings default if not provided)

    Returns:
        Configured BaseProvider instance

    Raises:
        AIServiceError: If provider cannot be created

    Example:
        >>> provider = create_provider()
        >>> provider = create_provider(provider_name="openai", model="gpt-4o")
    """
    settings = get_settings()

    # Resolve parameters with settings defaults
    resolved_provider = provider_name or settings.ai_default_provider
    resolved_model = model or settings.ai_default_model
    resolved_api_key = api_key or (
        settings.openrouter_api_key
        or settings.anthropic_api_key
        or settings.openai_api_key
        or ""
    )
    resolved_max_tokens = max_tokens or settings.ai_max_tokens
    resolved_temperature = temperature or settings.ai_temperature

    config = ProviderConfig(
        api_key=resolved_api_key,
        model=resolved_model,
        max_tokens=resolved_max_tokens,
        temperature=resolved_temperature,
    )

    if resolved_provider == "openrouter":
        return OpenRouterProvider(config)
    elif resolved_provider == "openai":
        OpenAIProvider = _get_openai_provider()
        if OpenAIProvider is None:
            from ai.exceptions import AIServiceError
            raise AIServiceError(
                "openai package not installed. Install with: pip install openai",
                details={"pip_install": "openai"},
            )
        return OpenAIProvider(config)

    return AnthropicProvider(config)