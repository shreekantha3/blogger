"""
Readability analysis.

ARCHITECTURAL DECISION: Flesch Reading Ease approximation
--------------------------------------------------------
Without external dependencies (nltk, textstat), we implement
basic readability checks:

1. Average sentence length (< 20 words ideal)
2. Average word length (< 5 chars ideal)
3. Paragraph length (2-4 sentences ideal)
4. Passive voice detection (simplified)

These correlate with Flesch scores and catch most readability issues.

Future: In Phase 3, we'll add proper Flesch-Kincaid and Gunning Fog
calculations when nltk/textstat is installed.
"""

import re
from config import get_logger
from seo.models import SEOScore
from utils.helpers import extract_text_from_html

logger = get_logger("seo", "readability")


class ReadabilityAnalyzer:
    """
    Analyzes content readability.

    Design decisions:
    - No external dependencies for core functionality
    - Scores based on sentence/word complexity
    - Provides actionable suggestions
    """

    IDEAL_SENTENCE_WORDS = 20  # Words per sentence
    IDEAL_WORD_CHARS = 5       # Characters per word
    IDEAL_PARAGRAPH_SENTENCES = 3

    def analyze(self, html: str) -> SEOScore:
        """
        Analyze readability of HTML content.

        Scoring:
        - Short sentences (< 20 words): +30 pts
        - Short words (< 5 chars avg): +20 pts
        - Good paragraphs (2-5 sentences): +20 pts
        - No excessive passive voice: +30 pts
        """
        issues: list[str] = []
        suggestions: list[str] = []
        score = 0

        text = extract_text_from_html(html)

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return SEOScore(
                value=0,
                label="Readability",
                issues=["No sentences detected"],
                suggestions=["Add sentence-structured content"],
            )

        # Check sentence length
        avg_sentence_words = self._avg_sentence_length(sentences)
        if avg_sentence_words <= self.IDEAL_SENTENCE_WORDS:
            score += 30
        else:
            issues.append(
                f"Long sentences (avg {avg_sentence_words:.0f} words)"
            )
            suggestions.append(
                f"Aim for sentences under {self.IDEAL_SENTENCE_WORDS} words"
            )

        # Check word length
        avg_word_chars = self._avg_word_length(text)
        if avg_word_chars <= self.IDEAL_WORD_CHARS:
            score += 20
        else:
            suggestions.append(
                "Consider simpler vocabulary for broader audience"
            )

        # Check paragraph structure (simplified)
        paragraphs = re.split(r"\n\n|\r\n\r\n|<p>", html)
        avg_para_sentences = self._avg_paragraph_sentences(
            paragraphs, sentences
        )
        if 2 <= avg_para_sentences <= 5:
            score += 20

        # Check passive voice (simplified check)
        passive_count = self._count_passive_voice(sentences)
        passive_ratio = passive_count / len(sentences) if sentences else 0

        if passive_ratio < 0.2:
            score += 30
        else:
            issues.append(
                f"High passive voice usage ({passive_ratio * 100:.0f}%)"
            )
            suggestions.append(
                "Use active voice for more engaging content"
            )

        return SEOScore(
            value=max(0, min(100, score)),
            label="Readability",
            issues=issues,
            suggestions=suggestions,
        )

    def _avg_sentence_length(self, sentences: list[str]) -> float:
        """Calculate average words per sentence."""
        if not sentences:
            return 0.0

        total_words = sum(len(s.split()) for s in sentences)
        return total_words / len(sentences)

    def _avg_word_length(self, text: str) -> float:
        """Calculate average characters per word."""
        words = text.split()
        if not words:
            return 0.0

        total_chars = sum(len(w) for w in words)
        return total_chars / len(words)

    def _avg_paragraph_sentences(
        self, paragraphs: list[str], sentences: list[str]
    ) -> float:
        """Estimate average sentences per paragraph."""
        # Simplified: divide sentences by paragraphs
        num_paragraphs = max(1, len(paragraphs))
        return len(sentences) / num_paragraphs

    def _count_passive_voice(self, sentences: list[str]) -> int:
        """Simplified passive voice detection."""
        passive_words = ["is", "are", "was", "were", "be", "been", "being"]
        passive_patterns = [
            r"\b(am|are|is|was|were|being|been)\s+\w+ed\b",
            r"\b(have|has|had)\s+been\s+\w+ed\b",
        ]

        count = 0
        for sentence in sentences:
            for pattern in passive_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    count += 1
                    break

        return count

    def get_reading_grade_level(self, html: str) -> str:
        """
        Estimate grade level for content.

        Simplified approximation based on sentence and word length.
        """
        text = extract_text_from_html(html)
        avg_sentence = self._avg_sentence_length(
            re.split(r"[.!?]+", text)
        )
        avg_word = self._avg_word_length(text)

        # Rough approximation
        if avg_sentence < 15 and avg_word < 4.5:
            return "5th grade or lower"
        elif avg_sentence < 20 and avg_word < 5.5:
            return "6th-8th grade"
        elif avg_sentence < 25 and avg_word < 6:
            return "9th-10th grade"
        else:
            return "11th grade or higher"