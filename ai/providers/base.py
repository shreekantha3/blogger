"""
Abstract base class for LLM providers.

ARCHITECTURAL DECISION: Abstract Base Class Pattern
----------------------------------------------------
We define a common interface that all providers must implement.
This follows the Strategy pattern for algorithm variation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from config import get_logger
from ai.exceptions import AIServiceError

logger = get_logger("ai", "providers", "base")


@dataclass
class ProviderConfig:
    """
    Configuration for an AI provider.

    Attributes:
        api_key: API key for authentication
        model: Model name to use
        max_tokens: Maximum tokens for generation
        temperature: Sampling temperature
    """

    api_key: str
    model: str = "claude-sonnet-5"
    max_tokens: int = 4000
    temperature: float = 0.7


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement this interface to ensure
    consistent behavior across the application.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize provider with configuration.

        Args:
            config: Provider configuration

        Raises:
            AIServiceError: If configuration is invalid
        """
        if not config.api_key:
            raise AIServiceError(
                "API key is required for AI provider",
                details={"provider": self.__class__.__name__},
            )
        self._config = config
        logger.debug(
            "Provider initialized",
            provider=self.__class__.__name__,
            model=config.model,
        )

    @property
    def model_name(self) -> str:
        """Get the model name being used."""
        return self._config.model

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Override max tokens (uses config default if None)
            temperature: Override temperature (uses config default if None)

        Returns:
            Generated text response

        Raises:
            AIServiceError: If the API call fails
        """
        pass

    @abstractmethod
    def generate_article(
        self,
        topic: str,
        tone: str,
        target_keywords: Optional[list[str]] = None,
        word_count: int = 1000,
    ) -> tuple[str, str]:
        """
        Generate a complete article.

        Args:
            topic: Main topic for the article
            tone: Writing tone
            target_keywords: Keywords to include
            word_count: Target word count

        Returns:
            Tuple of (title, content)
        """
        pass

    @abstractmethod
    def generate_seo_title(
        self,
        topic: str,
        target_keywords: Optional[list[str]] = None,
        max_length: int = 60,
    ) -> str:
        """
        Generate an SEO-optimized title.

        Args:
            topic: Topic for the title
            target_keywords: Keywords to include
            max_length: Maximum title length

        Returns:
            Generated SEO title
        """
        pass

    @abstractmethod
    def optimize_meta_description(
        self,
        content: str,
        title: str,
        target_keyword: Optional[str] = None,
        length: int = 155,
    ) -> str:
        """
        Optimize or generate a meta description.

        Args:
            content: Post content
            title: Post title
            target_keyword: Primary keyword
            length: Target length

        Returns:
            Optimized meta description
        """
        pass

    @abstractmethod
    def generate_faq(
        self,
        content: str,
        title: Optional[str] = None,
        num_questions: int = 5,
    ) -> list[tuple[str, str]]:
        """
        Generate FAQ from content.

        Args:
            content: Content to base FAQs on
            title: Post title for context
            num_questions: Number of questions to generate

        Returns:
            List of (question, answer) tuples
        """
        pass

    @abstractmethod
    def generate_summary(
        self,
        content: str,
        style: str = "brief",
        max_length: int = 200,
    ) -> str:
        """
        Generate a summary of content.

        Args:
            content: Content to summarize
            style: Summary style
            max_length: Maximum length

        Returns:
            Generated summary
        """
        pass

    @abstractmethod
    def optimize_keywords(
        self,
        content: str,
        main_topic: str,
        target_keywords: Optional[list[str]] = None,
    ) -> tuple[str, list[str]]:
        """
        Optimize content for keywords.

        Args:
            content: Original content
            main_topic: Main topic keyword
            target_keywords: Keywords to optimize

        Returns:
            Tuple of (optimized_content, related_keywords)
        """
        pass