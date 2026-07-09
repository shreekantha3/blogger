"""
Anthropic Claude provider implementation.

ARCHITECTURAL DECISION: Implementation Details
-----------------------------------------------
This provider uses the Anthropic SDK for Claude models.
It follows the BaseProvider interface for consistency.

Production considerations:
1. API key is loaded from settings (not passed directly)
2. Model versions are configurable via settings
3. Built-in retry logic via the base provider
4. Structured logging for all operations
"""

import json
from typing import Optional

from config import get_logger
from ai.exceptions import AIServiceError, AIContentError
from ai.providers.base import BaseProvider, ProviderConfig

logger = get_logger("ai", "providers", "anthropic")

# Import anthropic if available, will raise informative error in __init__ if not
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider(BaseProvider):
    """
    Anthropic Claude provider for AI content generation.

    Supports all Claude models (Opus, Sonnet, Haiku) with the latest versions.
    Uses the official Anthropic SDK for API calls.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize Anthropic provider.

        Raises:
            AIServiceError: If anthropic package not installed or API key invalid
        """
        if not ANTHROPIC_AVAILABLE:
            raise AIServiceError(
                "anthropic package not installed. Install with: pip install anthropic",
                details={"pip_install": "anthropic"},
            )
        super().__init__(config)
        self._client = anthropic.Anthropic(api_key=config.api_key)

    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using Claude model."""
        max_tokens = max_tokens or self._config.max_tokens
        temperature = temperature or self._config.temperature

        logger.debug(
            "Generating text with Anthropic",
            model=self._config.model,
            prompt_length=len(prompt),
        )

        try:
            response = self._client.messages.create(
                model=self._config.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error("Anthropic API error", error=str(e))
            raise AIServiceError(
                f"Anthropic API error: {e}",
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

        research_instruction = ""
        if research_insights:
            research_instruction = f"\n\nUse these research insights to ensure accuracy:\n{research_insights[:1000]}"

        prompt = f"""You are a professional blog writer. Write a comprehensive article about "{topic}".

Requirements:
- Tone: {tone}
- Target length: approximately {word_count} words{language_instruction}
- Include an H1 title, H2 section headings, and paragraph content
- Make it engaging and valuable to readers{keyword_instruction}{research_instruction}
- Use proper HTML tags (<h1>, <h2>, <p>)
- No markdown, only HTML
- Ensure content is written in the specified language

Return ONLY the HTML content starting with <h1>.
"""

        content = self.generate_text(prompt)

        # Extract title from H1
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
        language: str = "en",
    ) -> str:
        """Generate an SEO-optimized title."""
        keywords = target_keywords or []
        keyword_instruction = f" Include these keywords: {', '.join(keywords)}." if keywords else ""

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
            language_instruction = f"\n- Write the title in {lang_name} ({language.upper()}) language."

        prompt = f"""Generate an SEO-optimized title for a blog post about "{topic}".

Requirements:
- Maximum {max_length} characters
- Include primary keywords naturally{keyword_instruction}{language_instruction}
- Make it compelling for search users
- No clickbait, genuinely descriptive

Return ONLY the title, no formatting.
"""

        title = self.generate_text(prompt, max_tokens=100)
        return title.strip()

    def optimize_meta_description(
        self,
        content: str,
        title: str,
        target_keyword: Optional[str] = None,
        length: int = 155,
        language: str = "en",
    ) -> str:
        """Optimize or generate a meta description."""
        keyword_instruction = f" Include the keyword '{target_keyword}'." if target_keyword else ""

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
            language_instruction = f"\n- Write the meta description in {lang_name} ({language.upper()}) language."

        prompt = f"""Write a meta description for a blog post titled "{title}".

Requirements:
- Exactly {length} characters (Google displays ~{length} chars)
- Compelling call to action (e.g., "Learn about...", "Discover...")
- Accurate summary of the content{keyword_instruction}{language_instruction}
- No generic phrases like "Click here" or "Read more"

Return ONLY the meta description.
"""

        meta = self.generate_text(prompt, max_tokens=200)
        return meta.strip()[:length]

    def generate_faq(
        self,
        content: str,
        title: Optional[str] = None,
        num_questions: int = 5,
        language: str = "en",
    ) -> list[tuple[str, str]]:
        """Generate FAQ from content."""
        context = f" for a post titled '{title}'" if title else ""

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
            language_instruction = f"\n- Write the questions and answers in {lang_name} ({language.upper()}) language."

        prompt = f"""Generate {num_questions} frequently asked questions{context} based on this content:

{content[:2000]}

Format your response as JSON array with objects containing "question" and "answer" keys.
Each answer should be 1-2 sentences.
Be specific and relevant to the content.{language_instruction}
Return ONLY the JSON array.
"""

        response = self.generate_text(prompt, max_tokens=1500)

        try:
            faqs = json.loads(response)
            return [(f["question"], f["answer"]) for f in faqs[:num_questions]]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse FAQ JSON", error=str(e))
            raise AIContentError(
                "Failed to parse generated FAQ",
                details={"raw_response": response[:200]},
            ) from e

    def generate_summary(
        self,
        content: str,
        style: str = "brief",
        max_length: int = 200,
    ) -> str:
        """Generate a summary of content."""
        style_instructions = {
            "brief": "Write a concise summary (1-2 sentences).",
            "detailed": "Write a detailed summary covering all main points (3-5 sentences).",
            "bullets": "Write a bullet-point summary of key takeaways.",
        }
        instruction = style_instructions.get(style, style_instructions["brief"])

        prompt = f"""Summarize the following content.

{instruction}
Maximum {max_length} characters.

{content[:3000]}

Return ONLY the summary.
"""

        return self.generate_text(prompt, max_tokens=300).strip()

    def optimize_keywords(
        self,
        content: str,
        main_topic: str,
        target_keywords: Optional[list[str]] = None,
    ) -> tuple[str, list[str]]:
        """Optimize content for keywords."""
        keywords = target_keywords or []

        prompt = f"""Analyze this content about "{main_topic}" and suggest related keywords.

Content:
{content[:2000]}

{"Target keywords to enhance: " + ', '.join(keywords) if keywords else ""}

Return a JSON object with:
- "optimized_content": the content with improved keyword placement (optional)
- "related_keywords": list of 10 related keywords

Format as valid JSON only.
"""

        response = self.generate_text(prompt, max_tokens=1000)

        try:
            result = json.loads(response)
            return result.get("optimized_content", content), result.get("related_keywords", [])
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse keyword optimization JSON", error=str(e))
            raise AIContentError(
                "Failed to parse keyword optimization",
                details={"raw_response": response[:200]},
            ) from e