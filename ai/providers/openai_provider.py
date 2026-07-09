"""
OpenAI GPT provider implementation.

ARCHITECTURAL DECISION: Alternative Provider
--------------------------------------------
This is an alternative to AnthropicProvider following the same interface.
Users can switch providers via AI_DEFAULT_PROVIDER setting.
"""

import json
from typing import Optional

from config import get_logger
from ai.exceptions import AIServiceError, AIContentError
from ai.providers.base import BaseProvider, ProviderConfig

logger = get_logger("ai", "providers", "openai")

# Import openai if available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseProvider):
    """
    OpenAI GPT provider for AI content generation.

    Supports GPT-4 and GPT-3.5 models via the OpenAI SDK.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize OpenAI provider.

        Raises:
            AIServiceError: If openai package not installed or API key invalid
        """
        if not OPENAI_AVAILABLE:
            raise AIServiceError(
                "openai package not installed. Install with: pip install openai",
                details={"pip_install": "openai"},
            )
        super().__init__(config)
        self._client = openai.OpenAI(api_key=config.api_key)

    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using OpenAI model."""
        max_tokens = max_tokens or self._config.max_tokens
        temperature = temperature or self._config.temperature

        logger.debug(
            "Generating text with OpenAI",
            model=self._config.model,
            prompt_length=len(prompt),
        )

        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e))
            raise AIServiceError(
                f"OpenAI API error: {e}",
                details={"error_type": type(e).__name__},
            ) from e
        except Exception as e:
            logger.error("Unexpected error in generate_text", error=str(e))
            raise AIServiceError(
                f"Failed to generate text: {e}",
                details={"error_type": type(e).__name__},
            ) from e

    def generate_article(
        self,
        topic: str,
        tone: str,
        target_keywords: Optional[list[str]] = None,
        word_count: int = 1000,
        language: str = "en",
        research_insights: Optional[str] = None,
    ) -> tuple[str, str]:
        """Generate a complete article."""
        keywords = target_keywords or []
        keyword_instruction = f" Include these keywords naturally: {', '.join(keywords)}." if keywords else ""

        research_instruction = ""
        if research_insights:
            research_instruction = f"\n\nResearch findings to ensure accuracy:\n{research_insights[:800]}"

        language_instruction = ""
        if language and language.lower() != "en":
            language_map = {
                "kn": "Kannada",
                "hi": "Hindi",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "zh": "Chinese",
                "ja": "Japanese",
                "ta": "Tamil",
                "te": "Telugu",
            }
            lang_name = language_map.get(language.lower(), language)
            language_instruction = f"\n- Write the entire article in {lang_name} ({language.upper()}) language."

        prompt = f"""You are a professional blog writer. Write a comprehensive article about "{topic}".

Requirements:
- Tone: {tone}
- Target length: approximately {word_count} words{language_instruction}
- Include an H1 title, H2 section headings, and paragraph content
- Make it engaging and valuable to readers{keyword_instruction}{research_instruction}
- Use proper HTML tags (<h1>, <h2>, <p>)
- No markdown, only HTML

Return ONLY the HTML content starting with <h1>.
"""

        content = self.generate_text(prompt)

        title_match = content.split("<h1>")
        if len(title_match) > 1:
            title = title_match[1].split("</h1>")[0].strip()
        else:
            title = topic

        logger.info(
            "Article generated",
            title=title[:50],
            word_count=len(content.split()),
            language=language,
        )

        return title, content

    def generate_seo_title(
        self,
        topic: str,
        target_keywords: Optional[list[str]] = None,
        max_length: int = 60,
    ) -> str:
        """Generate an SEO-optimized title."""
        return self.generate_text(
            f"""Generate an SEO-optimized title for a blog post about "{topic}".

Maximum {max_length} characters.
Include keywords naturally.
Return ONLY the title.
""",
            max_tokens=100,
        ).strip()

    def optimize_meta_description(
        self,
        content: str,
        title: str,
        target_keyword: Optional[str] = None,
        length: int = 155,
    ) -> str:
        """Optimize or generate a meta description."""
        return self.generate_text(
            f"""Write a meta description for a blog post titled "{title}".

Exactly {length} characters.
Compelling call to action.
Return ONLY the meta description.
""",
            max_tokens=200,
        ).strip()[:length]

    def generate_faq(
        self,
        content: str,
        title: Optional[str] = None,
        num_questions: int = 5,
    ) -> list[tuple[str, str]]:
        """Generate FAQ from content."""
        response = self.generate_text(
            f"""Generate {num_questions} FAQ items based on: {content[:2000]}

Format as JSON array with "question" and "answer" keys. Return JSON only.
""",
            max_tokens=1500,
        )

        try:
            faqs = json.loads(response)
            return [(f["question"], f["answer"]) for f in faqs[:num_questions]]
        except (json.JSONDecodeError, KeyError) as e:
            raise AIContentError("Failed to parse FAQ JSON") from e

    def generate_summary(
        self,
        content: str,
        style: str = "brief",
        max_length: int = 200,
    ) -> str:
        """Generate a summary of content."""
        return self.generate_text(
            f"""Summarize: {content[:3000]}

Style: {style}. Max {max_length} chars. Return summary only.
""",
            max_tokens=300,
        ).strip()

    def optimize_keywords(
        self,
        content: str,
        main_topic: str,
        target_keywords: Optional[list[str]] = None,
    ) -> tuple[str, list[str]]:
        """Optimize content for keywords."""
        response = self.generate_text(
            f"""Analyze content about "{main_topic}" and suggest related keywords.

Content: {content[:2000]}

Return JSON: {{"optimized_content": "...", "related_keywords": ["..."]}}
""",
            max_tokens=1000,
        )

        try:
            result = json.loads(response)
            return result.get("optimized_content", content), result.get("related_keywords", [])
        except (json.JSONDecodeError, KeyError) as e:
            raise AIContentError("Failed to parse keyword optimization") from e