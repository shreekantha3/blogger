"""
OpenRouter provider implementation.

ARCHITECTURAL DECISION: Unified Model Access
----------------------------------------------
OpenRouter provides a unified API for accessing multiple AI models
(Claude, GPT, Llama, etc.) through a single interface.

This is ideal for:
1. Access to multiple models with one API key
2. Failover between models if one is unavailable
3. Cost optimization (route to cheaper models)
4. Testing different models for the same task
"""

import json
from typing import Optional

from config import get_logger
from ai.exceptions import AIServiceError, AIContentError
from ai.providers.base import BaseProvider, ProviderConfig

logger = get_logger("ai", "providers", "openrouter")

# Import openai if available (OpenRouter uses OpenAI-compatible API)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# Recommended model presets for different tasks
OPENROUTER_MODELS = {
    # Free models (recommended for testing/no-cost usage)
    "poolside-m-free": "poolside/laguna-m.1:free",
    "poolside-xs-free": "poolside/laguna-xs-2.1:free",
    "gemma-4-26b-free": "google/gemma-4-26b-a4b-it:free",
    "gemma-4-31b-free": "google/gemma-4-31b-it:free",
    "nemotron-ultra-free": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nemotron-120b-free": "nvidia/nemotron-3-super-120b-a12b:free",
    "cohere-north-mini-free": "cohere/north-mini-code:free",
    # Claude models
    "claude-fable-5": "anthropic/claude-fable-5",
    "claude-sonnet-5": "anthropic/claude-sonnet-5",
    "claude-opus-4-8": "anthropic/claude-opus-4-8",
    "claude-haiku-4-5": "anthropic/claude-haiku-4-5-20251001",
    # OpenAI models
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    # Meta Llama models
    "llama-3-70b": "meta/llama-3-70b",
    "llama-3-8b": "meta/llama-3-8b",
    # Default to free poolside model (actively available)
    "default": "poolside/laguna-m.1:free",
}


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter provider for unified AI model access.

    OpenRouter provides access to multiple models (Claude, GPT, Llama, etc.)
    through a single OpenAI-compatible API endpoint.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize OpenRouter provider.

        Raises:
            AIServiceError: If openai package not installed or API key invalid
        """
        if not OPENAI_AVAILABLE:
            raise AIServiceError(
                "openai package not installed. Install with: pip install openai",
                details={"pip_install": "openai"},
            )
        super().__init__(config)

        # OpenRouter uses OpenAI-compatible API with different base URL
        self._client = openai.OpenAI(
            api_key=config.api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using OpenRouter model."""
        max_tokens = max_tokens or self._config.max_tokens
        temperature = temperature or self._config.temperature

        # Map model name to OpenRouter format
        model = self._get_openrouter_model(self._config.model)

        logger.debug(
            "Generating text with OpenRouter",
            model=model,
            prompt_length=len(prompt),
        )

        try:
            response = self._client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except openai.APIError as e:
            logger.error("OpenRouter API error", error=str(e))
            raise AIServiceError(
                f"OpenRouter API error: {e}",
                details={"error_type": type(e).__name__, "model": model},
            ) from e
        except Exception as e:
            logger.error("Unexpected error in generate_text", error=str(e))
            raise AIServiceError(
                f"Failed to generate text: {e}",
                details={"error_type": type(e).__name__},
            ) from e

    def _get_openrouter_model(self, model: str) -> str:
        """Convert model name to OpenRouter format."""
        return OPENROUTER_MODELS.get(model, model)

    def generate_article(
        self,
        topic: str,
        tone: str,
        target_keywords: Optional[list[str]] = None,
        word_count: int = 1000,
        language: str = "en",
    ) -> tuple[str, str]:
        """Generate a complete article."""
        keywords = target_keywords or []
        keyword_str = ', '.join(keywords) if keywords else "none"

        # Language instruction for multilingual content
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
            language_instruction = f"\n- Write the entire content in {lang_name} ({language.upper()}) language."

        # Split into two calls for better free model compatibility
        # First, generate the title (optimized for SEO: 50-70 chars)
        title_prompt = f'''Write an SEO-optimized blog title for topic: {topic}
Tone: {tone}
Length: 50-70 characters (crucial for SEO - exactly this range)
Include primary keywords naturally
{language_instruction}
Output only the title, no formatting, no html, no quotes.

EXAMPLE: Karnataka Leadership Shift: DKS vs Siddaramaiah and 2028 Impact

TITLE:'''
        title = self.generate_text(title_prompt, max_tokens=100).strip()
        # Clean title (remove any artifacts)
        if "TITLE:" in title:
            title = title.split("TITLE:")[-1].strip()
        title = title.strip('"\'').strip()

        # Then generate content with SEO-optimized structure
        content_prompt = f'''Write a comprehensive blog article about {topic}.
Tone: {tone}
Length: {word_count} words minimum (target 2500+ words for competitive topics)
{language_instruction}

SEO REQUIREMENTS (MUST FOLLOW STRICTLY):
- Start with EXACT: <h1>{title}</h1>
- Include exactly 6 H2 sections:
  * <h2>Introduction</h2>
  * <h2>Background</h2>
  * <h2>Current Situation</h2>
  * <h2>Analysis</h2>
  * <h2>Implications</h2>
  * <h2>Conclusion</h2>
- Under EACH H2, include 2-3 H3 subsections for detailed discussion
- Use keywords naturally in headings and body: {keyword_str}
- Keep paragraphs short (2-4 sentences max, 120 words or less)
- Use active voice, 8th-10th grade reading level
- End with strong conclusion

Format: HTML only. No markdown. Start immediately with <h1>.

CONTENT:'''
        content = self.generate_text(content_prompt, max_tokens=self._config.max_tokens)
        # Clean content
        if "CONTENT:" in content:
            content = content.split("CONTENT:")[-1].strip()

        # Ensure h1 exists, fix if needed
        if "<h1>" not in content:
            content = f"<h1>{title}</h1>\n{content}"

        logger.info(
            "Article generated via OpenRouter",
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
            language_instruction = f"\nWrite in {lang_name} ({language.upper()}) language."

        return self.generate_text(
            f"""Generate an SEO-optimized title for a blog post about "{topic}".

Maximum {max_length} characters. Include keywords naturally.{language_instruction}
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
        language: str = "en",
    ) -> str:
        """Optimize or generate a meta description."""
        # Extract first paragraph for context
        import re
        text_content = re.sub(r'<[^>]+>', '', content)[:500]

        keyword_str = target_keyword or ""
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
            language_instruction = f"\nWrite in {lang_name} ({language.upper()}) language."

        # Very explicit prompt for free models
        prompt = f'''Write an SEO-optimized meta description.
Blog post title: "{title}"
Primary keyword: {keyword_str}
Content preview: {text_content[:200]}...
{language_instruction}

Requirements:
- Length: 120-160 characters (EXACTLY in this range for SEO)
- One compelling sentence
- Include the primary keyword
- No quotes, no HTML
- Descriptive, not salesy

META:'''
        response = self.generate_text(prompt, max_tokens=200)
        # Extract the actual meta description - look for META marker
        if "META:" in response.upper():
            text = response.split("META:")[-1].strip()
        else:
            text = response.strip()
        # Clean up common artifacts
        text = text.replace('\n', ' ').strip()
        text = text.strip('"\'').strip()
        # Ensure optimal length (120-160 chars)
        if len(text) < 120:
            # Pad if too short
            text = text + " - analysis and insights included."
        return text[:160]

    def generate_faq(
        self,
        content: str,
        title: Optional[str] = None,
        num_questions: int = 5,
        language: str = "en",
    ) -> list[tuple[str, str]]:
        """Generate FAQ from content."""
        context = f" titled '{title}'" if title else ""

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
            language_instruction = f" (in {lang_name} ({language.upper()}) language)"

        response = self.generate_text(
            f"Generate {num_questions} FAQ questions and answers{context} about this content:{language_instruction}:\n\n{content[:2000]}\n\n"
            f"Format each as: Q: Question here? A: Answer here.\nOne per line.",
            max_tokens=1500,
        )

        return self._parse_faq_flexible(response, num_questions)

    def _parse_faq_flexible(self, response: str, num_questions: int) -> list[tuple[str, str]]:
        """
        Parse FAQ response with fallback for free model output formats.

        Design decision: Defensive parsing - handle multiple output formats
        since free models may not follow strict JSON instructions.
        """
        # Try JSON first
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                faqs = json.loads(json_str)
                return [(f["question"], f["answer"]) for f in faqs[:num_questions]]
        except (json.JSONDecodeError, KeyError):
            pass

        # Try line-by-line format: Q: ... A: ...
        faqs: list[tuple[str, str]] = []
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            if 'Q:' in line and 'A:' in line:
                try:
                    q_part = line.split('Q:')[1]
                    a_part = q_part.split('A:')[1] if 'A:' in q_part else ""
                    q_text = q_part.split('A:')[0].strip().rstrip('?')
                    a_text = a_part.strip()
                    if q_text and a_text:
                        faqs.append((q_text + "?", a_text))
                except (IndexError, ValueError):
                    continue

        if faqs:
            return faqs[:num_questions]

        # Final fallback: return empty list (caller handles gracefully)
        logger.warning("Could not parse FAQ response, returning empty list")
        return []

    
    def _clean_free_model_output(self, text: str) -> str:
        """
        Clean and normalize output from free models.

        Free models often produce:
        - Incomplete sentences
        - Truncated outputs
        - Formatting artifacts
        - Extra whitespace

        This method normalizes the output for better quality.
        """
        if not text:
            return ""

        # Remove common artifacts
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

        # Remove leading markers that models sometimes add
        markers = ['TITLE:', 'CONTENT:', 'META:', 'SUMMARY:', 'ANSWER:', 'Q:', 'A:']
        for marker in markers:
            if text.upper().startswith(marker):
                text = text[len(marker):].strip()

        # Fix incomplete sentences at the end
        if text and not text.endswith(('.', '!', '?', '}', ']')):
            # Try to complete the sentence
            text = text.rstrip()
            if len(text) > 50:
                text = text[:-1] + "..."

        return text

    def _ensure_proper_html_structure(self, content: str, title: str) -> str:
        """
        Ensure HTML content has proper structure for SEO.

        Free models may produce:
        - Missing h1 tags
        - Too many/too few h2 tags
        - Improper nesting

        This method fixes common issues.
        """
        import re

        # Ensure content starts with h1
        if not re.search(r'<h1>', content, re.IGNORECASE):
            content = f"<h1>{title}</h1>" + content

        # Count headings
        h2_count = len(re.findall(r'<h2>', content, re.IGNORECASE))
        h1_count = len(re.findall(r'<h1>', content, re.IGNORECASE))

        # If missing proper structure, rebuild
        if h2_count < 3 or h1_count != 1:
            # Extract main content
            clean_content = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', content, flags=re.DOTALL | re.IGNORECASE)
            clean_content = re.sub(r'<[^>]+>', '', clean_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()

            # Build proper structure
            sections = [
                ("Introduction", 1),
                ("Background", 2),
                ("Key Points", 2),
                ("Analysis", 2),
                ("Conclusion", 2),
            ]

            html_parts = [f"<h1>{title}</h1>"]
            words = clean_content.split()

            # Distribute content across sections
            words_per_section = max(1, len(words) // len(sections))
            for i, (section_name, level) in enumerate(sections):
                html_parts.append(f"<h{level}>{section_name}</h{level}>")
                start = i * words_per_section
                end = start + words_per_section if i < len(sections) - 1 else len(words)
                section_text = " ".join(words[start:end])
                html_parts.append(f"<p>{section_text}</p>")

            content = "".join(html_parts)

        return content

    def _optimize_for_free_model(self, text: str, target_length: int = None) -> str:
        """
        Optimize text for better quality from free models.

        Free models benefit from:
        - Explicit length constraints
        - Clear formatting instructions
        - Post-processing for quality
        """
        if not text:
            return ""

        # Clean the output
        cleaned = self._clean_free_model_output(text)

        # If target_length specified, trim/pad
        if target_length and len(cleaned) > target_length:
            # Find a good breaking point
            cutoff = cleaned.rfind('.', 0, target_length)
            if cutoff > target_length * 0.8:
                cleaned = cleaned[:cutoff + 1]
            else:
                cleaned = cleaned[:target_length]

        return cleaned.strip()


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