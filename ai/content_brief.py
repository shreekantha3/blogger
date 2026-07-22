"""
Content brief generator with SERP insights.

ARCHITECTURAL DECISION: Content Brief Strategy
----------------------------------------------
A content brief captures search intent, competitor gaps, and unique angles
before AI generation. This prevents the "template structure" problem
identified in the Honest Code Review.

Instead of: Topic → AI → Publish
Do:         Topic → SERP Analysis → Content Brief → Human Approval → AI → Human Edit → Publish
"""

from dataclasses import dataclass
from typing import Optional
import json

from config import get_logger
from seo.serp_analyzer import SERPAnalyzer, ContentBrief as SERPContentBrief
from ai.models import Language

logger = get_logger("ai", "content_brief")


@dataclass
class ContentBriefRequest:
    """Request to generate a content brief."""

    topic: str
    target_keyword: str
    location: str = "IN"
    language: str = "en"
    word_count_target: Optional[int] = None
    include_faq: bool = True
    include_entities: bool = True


@dataclass
class ContentBriefResponse:
    """Generated content brief response."""

    target_keyword: str
    secondary_keywords: list[str]
    search_intent: str
    recommended_word_count: int
    required_h2_sections: list[str]
    paa_questions: list[str]
    entities_to_cover: list[str]
    competitor_urls: list[str]
    content_gaps: list[str]
    unique_angle_options: list[str]
    tone_suggestions: list[str]
    formatted_brief: str  # Markdown formatted version


class ContentBriefGenerator:
    """
    Generate content briefs for AI generation.

    Usage:
        generator = ContentBriefGenerator()
        brief = await generator.generate(ContentBriefRequest(topic="KSP Recruitment"))
        # Review the brief, then pass to AI generator
        article = await ai_generator.generate(brief)
    """

    def __init__(self) -> None:
        """Initialize brief generator."""
        self._serp_analyzer = SERPAnalyzer()

    async def generate(
        self,
        request: ContentBriefRequest,
    ) -> ContentBriefResponse:
        """
        Generate a content brief for the topic.

        Args:
            request: Content brief request parameters

        Returns:
            ContentBriefResponse with structured brief
        """
        # Get SERP insights
        serp_brief = await self._serp_analyzer.analyze(
            request.target_keyword,
            request.location,
            request.language,
        )

        # Format as markdown for human review
        formatted = self._format_brief(serp_brief, request)

        # Generate tone suggestions based on intent
        tones = self._suggest_tones(serp_brief.search_intent)

        response = ContentBriefResponse(
            target_keyword=serp_brief.target_keyword,
            secondary_keywords=serp_brief.secondary_keywords,
            search_intent=serp_brief.search_intent,
            recommended_word_count=request.word_count_target or serp_brief.recommended_word_count,
            required_h2_sections=serp_brief.required_h2_sections,
            paa_questions=serp_brief.paa_questions,
            entities_to_cover=serp_brief.entities_to_cover,
            competitor_urls=serp_brief.competitor_urls,
            content_gaps=serp_brief.content_gaps,
            unique_angle_options=serp_brief.unique_angle_suggestions,
            tone_suggestions=tones,
            formatted_brief=formatted,
        )

        logger.info("Generated content brief", keyword=request.target_keyword)
        return response

    def _format_brief(
        self,
        brief: SERPContentBrief,
        request: ContentBriefRequest,
    ) -> str:
        """Format brief as markdown for human review."""
        lines = [
            f"# Content Brief: {brief.target_keyword}",
            "",
            f"## Search Intent",
            f"**Type:** {brief.search_intent}",
            "",
            f"## Target Keywords",
            f"- Primary: {brief.target_keyword}",
            f"- Secondary: {', '.join(brief.secondary_keywords[:5])}",
            "",
            f"## Word Count Target",
            f"**Recommended:** {brief.recommended_word_count} words",
            f"**Sections:** {len(brief.required_h2_sections)} H2s",
            "",
            f"## Required Sections",
            "",
        ]

        for i, section in enumerate(brief.required_h2_sections, 1):
            lines.append(f"{i}. {section}")

        lines.extend([
            "",
            f"## People Also Ask Questions",
            "",
        ])

        for q in brief.paa_questions[:10]:
            lines.append(f"- {q}")

        if brief.content_gaps:
            lines.extend([
                "",
                f"## Competitor Gaps (Opportunity!)",
                "",
            ])
            for gap in brief.content_gaps:
                lines.append(f"- {gap}")

        if brief.unique_angle_options:
            lines.extend([
                "",
                f"## Unique Angle Suggestions",
                "",
            ])
            for angle in brief.unique_angle_options:
                lines.append(f"- {angle}")

        return "\n".join(lines)

    def _suggest_tones(
        self,
        intent: str,
    ) -> list[str]:
        """Suggest appropriate tones based on search intent."""
        tone_map = {
            "informational": ["educational", "professional", "helpful"],
            "commercial": ["persuasive", "professional", "trustworthy"],
            "transactional": ["action-oriented", "urgent", "clear"],
            "navigational": ["helpful", "direct", "authoritative"],
        }
        return tone_map.get(intent, ["professional"])

    async def close(self) -> None:
        """Clean up resources."""
        await self._serp_analyzer.close()