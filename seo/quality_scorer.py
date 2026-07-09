"""
Content Quality Scorer - EEAT Evaluation.

ARCHITECTURAL DECISION: EEAT Quality Assessment
--------------------------------------------------
This module implements Google's EEAT (Experience, Expertise, Authoritativeness, Trustworthiness)
content quality scoring for AI-generated content.

Based on Google's Search Central guidelines for content quality evaluation.
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class QualityScore:
    """Content quality score with EEAT breakdown."""
    overall: int  # 0-100
    experience: int  # 0-100
    expertise: int  # 0-100
    authoritativeness: int  # 0-100
    trustworthiness: int  # 0-100
    issues: List[str]
    suggestions: List[str]


class QualityScorer:
    """
    Scores content quality based on EEAT guidelines.

    Evaluates AI-generated content for:
    - Experience: First-hand experience indicators
    - Expertise: Technical depth and accuracy
    - Authoritativeness: Credible sources and references
    - Trustworthiness: Factual accuracy and transparency
    """

    def __init__(self) -> None:
        """Initialize quality scorer."""
        self._experience_indicators = [
            "i have experience",
            "in my experience",
            "i tested",
            "we found",
            "our research",
            "case study",
            "hands-on",
            "personal experience",
        ]
        self._expertise_indicators = [
            "according to",
            "research shows",
            "study found",
            "data indicates",
            "analysis reveals",
            "statistical",
            "methodology",
            "hypothesis",
        ]
        self._trust_indicators = [
            "source:",
            "according to",
            "references:",
            "citation",
            "published in",
            "peer-reviewed",
            "official data",
            "verified",
        ]

    def score_content(
        self,
        title: str,
        content: str,
        author_expertise: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> QualityScore:
        """
        Score content quality across EEAT dimensions.

        Args:
            title: Article title
            content: Full article content (HTML)
            author_expertise: Author's stated expertise
            sources: List of reference sources used

        Returns:
            QualityScore with detailed breakdown

        Example:
            >>> scorer = QualityScorer()
            >>> score = scorer.score_content("Python Guide", content)
            >>> score.overall >= 50
        """
        # Extract text from HTML
        text = self._extract_text(content)

        # Score each dimension
        experience = self._score_experience(text, author_expertise)
        expertise = self._score_expertise(text)
        authoritativeness = self._score_authoritativeness(text, sources)
        trustworthiness = self._score_trustworthiness(text, sources)

        # Calculate overall
        overall = int((experience + expertise + authoritativeness + trustworthiness) / 4)

        issues: List[str] = []
        suggestions: List[str] = []

        # Identify issues
        if experience < 50:
            issues.append("Lacks first-hand experience indicators")
            suggestions.append("Add 'In my experience' or case study references")

        if expertise < 60:
            issues.append("Could use more technical depth")
            suggestions.append("Include specific data, methodology, or research references")

        if authoritativeness < 50:
            issues.append("Missing credible references")
            suggestions.append("Add links to authoritative sources (official docs, research)")

        if trustworthiness < 70:
            issues.append("Lacks fact checking or source attribution")
            suggestions.append("Add 'Source:' citations for key claims")

        return QualityScore(
            overall=overall,
            experience=experience,
            expertise=expertise,
            authoritativeness=authoritativeness,
            trustworthiness=trustworthiness,
            issues=issues,
            suggestions=suggestions,
        )

    def _extract_text(self, html: str) -> str:
        """Extract plain text from HTML."""
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _score_experience(self, text: str, author_expertise: Optional[str]) -> int:
        """Score experience indicators in content."""
        score = 50  # Base score

        # Check for first-hand experience language
        text_lower = text.lower()
        experience_matches = sum(
            1 for indicator in self._experience_indicators
            if indicator in text_lower
        )
        score += min(30, experience_matches * 10)

        # Check for author expertise
        if author_expertise:
            score += 20

        return min(100, score)

    def _score_expertise(self, text: str) -> int:
        """Score technical expertise depth."""
        score = 40  # Base score

        # Check for technical indicators
        text_lower = text.lower()
        expertise_matches = sum(
            1 for indicator in self._expertise_indicators
            if indicator in text_lower
        )
        score += min(30, expertise_matches * 10)

        return min(100, score)

    def _score_authoritativeness(self, text: str, sources: Optional[List[str]]) -> int:
        """Score for credible sources and references."""
        score = 30  # Base score

        # Check for source references
        if sources:
            score += min(40, len(sources) * 10)
        else:
            # Check for inline source indicators
            text_lower = text.lower()
            source_matches = sum(
                1 for indicator in ["source:", "study", "report", "data", "research"]
                if indicator in text_lower
            )
            score += min(40, source_matches * 5)

        return min(100, score)

    def _score_trustworthiness(self, text: str, sources: Optional[List[str]]) -> int:
        """Score for factual accuracy and transparency."""
        score = 50  # Base score

        # Check for trust indicators
        text_lower = text.lower()
        trust_matches = sum(
            1 for indicator in self._trust_indicators
            if indicator in text_lower
        )
        score += min(30, trust_matches * 10)

        # Check for sources
        if sources:
            score += 10

        return min(100, score)

    def generate_eeat_report(
        self,
        content: str,
        title: str,
    ) -> Dict[str, Any]:
        """
        Generate full EEAT report for content.

        Args:
            content: HTML content
            title: Article title

        Returns:
            Detailed EEAT report dictionary
        """
        score = self.score_content(title, content)

        grade = "A" if score.overall >= 90 else \
                "B" if score.overall >= 80 else \
                "C" if score.overall >= 70 else \
                "D" if score.overall >= 60 else "F"

        return {
            "overall_score": score.overall,
            "grade": grade,
            "breakdown": {
                "experience": score.experience,
                "expertise": score.expertise,
                "authoritativeness": score.authoritativeness,
                "trustworthiness": score.trustworthiness,
            },
            "issues": score.issues,
            "suggestions": score.suggestions,
        }