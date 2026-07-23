"""
SERP analyzer for competitive content strategy.

ARCHITECTURAL DECISION: SERP Analysis Strategy
-----------------------------------------------
Instead of just checking SEO scores, analyze what top competitors have:
1. Extract SERP features (PAA, featured snippets, video carousels)
2. Analyze top 10 URL structures and word counts
3. Identify content gaps competitors missed
4. Generate actionable content briefs

This answers "what to write" - the missing piece from Phase 1-5.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
import json

import httpx

from config import get_settings, get_logger

logger = get_logger("seo", "serp")


@dataclass
class SERPFeature:
    """A feature found in search results."""

    type: Literal[
        "featured_snippet",
        "people_also_ask",
        "video_carousel",
        "image_pack",
        "local_pack",
        "knowledge_panel",
        "top_stories",
        "shopping",
    ]
    content: str
    position: int  # SERP position (1-10+)


@dataclass
class CompetitorContent:
    """Content analysis of a competitor URL."""

    url: str
    title: str
    word_count: int
    h2_count: int
    h3_count: int
    has_faq: bool
    has_table: bool
    has_images: bool
    has_video: bool
    schema_types: list[str] = field(default_factory=list)


@dataclass
class ContentBrief:
    """Generated content brief with competitive insights."""

    target_keyword: str
    secondary_keywords: list[str]
    search_intent: Literal["informational", "commercial", "transactional", "navigational"]
    recommended_word_count: int
    required_h2_sections: list[str]
    paa_questions: list[str]
    entities_to_cover: list[str]
    competitor_urls: list[str]
    content_gaps: list[str]
    unique_angle_suggestions: list[str]


class SERPAnalyzer:
    """
    Analyze search engine results for content strategy.

    Usage:
        analyzer = SERPAnalyzer()
        brief = analyzer.analyze("python tutorial", "IN")
        print(brief.recommended_word_count)
        print(brief.paa_questions)
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize SERP analyzer.

        Args:
            api_key: SerpAPI key (or use environment variable)
        """
        self._settings = get_settings()
        self._api_key = api_key or self._settings.openai_api_key
        self._http_client = httpx.AsyncClient()

    async def analyze(
        self,
        keyword: str,
        location: str = "IN",
        language: str = "en",
    ) -> ContentBrief:
        """
        Analyze SERP and generate content brief.

        Args:
            keyword: Target search keyword
            location: ISO country code (IN, US, UK, etc.)
            language: Language code (en, hi, etc.)

        Returns:
            ContentBrief with competitive insights
        """
        # For now, use a mock implementation
        # In production, integrate with SerpAPI, ScrapingBee, or similar

        features = await self._extract_serp_features(keyword, location, language)
        competitors = await self._analyze_competitors(keyword, location, language)

        logger.info("Analyzed SERP", keyword=keyword, competitors=len(competitors))

        # Determine search intent
        search_intent = self._determine_intent(keyword, features)

        # Extract PAA questions
        paa_questions = [
            f.question for f in features if f.type == "people_also_ask"
        ]

        # Determine recommended word count from competitors
        word_counts = [c.word_count for c in competitors if c.word_count > 0]
        recommended_wc = int(
            sum(word_counts) / len(word_counts) * 1.25
        ) if word_counts else 1500

        # Identify content gaps
        gaps = self._identify_gaps(competitors)

        # Get secondary keywords
        secondary = self._extract_secondary_keywords(keyword, features, competitors)

        return ContentBrief(
            target_keyword=keyword,
            secondary_keywords=secondary,
            search_intent=search_intent,
            recommended_word_count=recommended_wc,
            required_h2_sections=self._suggest_h2_sections(keyword, competitors),
            paa_questions=paa_questions[:10],
            entities_to_cover=self._extract_entities(competitors),
            competitor_urls=[c.url for c in competitors],
            content_gaps=gaps,
            unique_angle_suggestions=self._suggest_angles(keyword, competitors),
        )

    async def _extract_serp_features(
        self,
        keyword: str,
        location: str,
        language: str,
    ) -> list[SERPFeature]:
        """Extract SERP features for the keyword."""
        features = []

        # Mock data - in production, call SerpAPI:
        # response = await self._http_client.get(
        #     "https://serpapi.com/search",
        #     params={"api_key": self._api_key, "q": keyword, ...}
        # )

        # For recruitment keywords, likely features:
        if "recruitment" in keyword.lower() or "job" in keyword.lower():
            features = [
                SERPFeature(type="people_also_ask", content="Eligibility criteria", position=1),
                SERPFeature(type="people_also_ask", content="Syllabus details", position=2),
                SERPFeature(type="people_also_ask", content="Application process", position=3),
            ]

        return features

    async def _analyze_competitors(
        self,
        keyword: str,
        location: str,
        language: str,
    ) -> list[CompetitorContent]:
        """Analyze top 10 competitor pages."""
        competitors = []

        # Mock competitor data - in production, would:
        # 1. Get top 10 URLs from SERP
        # 2. Fetch each page
        # 3. Analyze content structure

        # For recruitment articles, typical competitor patterns:
        if "recruitment" in keyword.lower():
            competitors = [
                CompetitorContent(
                    url="https://example.com/official-notification",
                    title=f"{keyword.title()} Official Notification",
                    word_count=800,
                    h2_count=6,
                    h3_count=12,
                    has_faq=False,
                    has_table=True,
                    has_images=False,
                    has_video=False,
                ),
                CompetitorContent(
                    url="https://example.com/recruitment-guide",
                    title=f"Complete Guide to {keyword.title()}",
                    word_count=1200,
                    h2_count=8,
                    h3_count=15,
                    has_faq=True,
                    has_table=True,
                    has_images=True,
                    has_video=False,
                ),
                CompetitorContent(
                    url="https://example.com/preparation-tips",
                    title=f"How to Prepare for {keyword.title()}",
                    word_count=1500,
                    h2_count=10,
                    h3_count=20,
                    has_faq=True,
                    has_table=True,
                    has_images=True,
                    has_video=True,
                ),
            ]

        return competitors

    def _determine_intent(
        self,
        keyword: str,
        features: list[SERPFeature],
    ) -> Literal["informational", "commercial", "transactional", "navigational"]:
        """Determine search intent from keyword and features."""
        # Recruitment keywords are typically informational/commercial
        if any(word in keyword.lower() for word in ["how", "what", "guide", "tips"]):
            return "informational"
        if any(word in keyword.lower() for word in ["buy", "price", "cost", "purchase"]):
            return "transactional"
        if any(word in keyword.lower() for word in ["best", "review", "vs", "comparison"]):
            return "commercial"

        return "informational"

    def _identify_gaps(self, competitors: list[CompetitorContent]) -> list[str]:
        """Identify content gaps competitors haven't covered."""
        gaps = []

        # Analyze what competitors are missing
        has_faq = any(c.has_faq for c in competitors)
        if not has_faq:
            gaps.append("FAQ section (nobody has one)")

        total_images = sum(c.has_images for c in competitors)
        if total_images < len(competitors) // 2:
            gaps.append("Visual examples (underused by competitors)")

        avg_words = sum(c.word_count for c in competitors) / len(competitors)
        if avg_words < 1000:
            gaps.append("Deep-dive content (competitors are shallow)")

        return gaps

    def _extract_secondary_keywords(
        self,
        keyword: str,
        features: list[SERPFeature],
        competitors: list[CompetitorContent],
    ) -> list[str]:
        """Extract related keywords from features and competitors."""
        keywords = [keyword]

        # From PAA questions
        for f in features:
            if f.type == "people_also_ask":
                # Extract key terms from questions
                keywords.append(f.content.lower().replace("?", ""))

        # Common secondary keywords for recruitment
        if "recruitment" in keyword.lower():
            keywords.extend([
                f"{keyword} eligibility",
                f"{keyword} syllabus",
                f"{keyword} application",
                f"{keyword} salary",
                f"{keyword} exam pattern",
            ])

        return list(set(keywords))[:10]

    def _suggest_h2_sections(
        self,
        keyword: str,
        competitors: list[CompetitorContent],
    ) -> list[str]:
        """Suggest H2 sections based on competitor analysis."""
        # Average H2 count from competitors
        avg_h2 = sum(c.h2_count for c in competitors) / len(competitors) if competitors else 6

        # For recruitment, standard sections:
        if "recruitment" in keyword.lower():
            return [
                "Overview",
                "Important Dates",
                "Eligibility Criteria",
                "Application Process",
                "Syllabus and Exam Pattern",
                "Selection Procedure",
                "Salary and Benefits",
                "How to Prepare",
                "Common Mistakes to Avoid",
                "FAQs",
            ][:int(avg_h2) + 2]

        return ["Introduction", "Background", "Main Content", "FAQs", "Conclusion"]

    def _extract_entities(self, competitors: list[CompetitorContent]) -> list[str]:
        """Extract key entities that should be covered."""
        entities = []

        for c in competitors:
            entities.extend(["date", "salary", "criteria", "process", "documents"])

        return list(set(entities))

    def _suggest_angles(self, keyword: str, competitors: list[CompetitorContent]) -> list[str]:
        """Suggest unique angles competitors haven't covered."""
        return [
            f"Personal experience with {keyword}",
            f"Common mistakes in {keyword}",
            f"Insider tips for {keyword}",
            f"Year-over-year analysis of {keyword}",
        ]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()