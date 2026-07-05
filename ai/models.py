"""
AI Engine data models.

ARCHITECTURAL DECISION: Pydantic Models for AI Requests/Responses
--------------------------------------------------------------
We use Pydantic models because:
1. Automatic validation of input/output data
2. Type safety throughout the application
3. Easy serialization/deserialization
4. Clear documentation of expected fields
5. Seamless integration with existing dataclasses
"""

from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class AIArticleRequest(BaseModel):
    """
    Request for AI article generation.

    Attributes:
        topic: Main topic for the article
        target_keywords: Optional list of target keywords
        tone: Writing tone (professional, casual, technical, friendly)
        word_count: Target word count
        include_faq: Whether to include FAQ section
        include_headings: Whether to include structured headings
    """

    topic: str = Field(..., min_length=1, description="Main topic for the article")
    target_keywords: Optional[List[str]] = Field(
        default_factory=list, description="Target keywords to include"
    )
    tone: str = Field(
        default="professional",
        description="Writing tone: professional, casual, technical, friendly",
    )
    word_count: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Target word count (100-10000)",
    )
    include_faq: bool = Field(
        default=True, description="Include FAQ section at end"
    )
    include_headings: bool = Field(
        default=True, description="Include structured HTML headings"
    )

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Validate tone is one of the allowed values."""
        allowed = {"professional", "casual", "technical", "friendly"}
        if v.lower() not in allowed:
            raise ValueError(f"tone must be one of {allowed}, got {v}")
        return v.lower()


class AIArticleResponse(BaseModel):
    """
    Response from AI article generation.

    Attributes:
        title: Generated article title
        content: Generated HTML content
        meta_description: Generated meta description
        target_keywords: Keywords used in the article
        word_count: Actual word count
        seo_score: Estimated SEO score (0-100)
    """

    title: str = Field(..., description="Generated article title")
    content: str = Field(..., description="Generated HTML content")
    meta_description: Optional[str] = Field(
        default=None, description="Generated meta description"
    )
    target_keywords: List[str] = Field(
        default_factory=list, description="Keywords included in article"
    )
    word_count: int = Field(default=0, description="Actual word count achieved")
    seo_score: int = Field(
        default=0, ge=0, le=100, description="Estimated SEO score"
    )


class SEOTitleRequest(BaseModel):
    """
    Request for SEO title generation.

    Attributes:
        topic: Main topic for the title
        target_keywords: Keywords to include
        platform: Target platform (google, blogger, both)
        max_length: Maximum title length
    """

    topic: str = Field(..., min_length=1, description="Topic for title generation")
    target_keywords: Optional[List[str]] = Field(
        default_factory=list, description="Keywords to include in title"
    )
    platform: str = Field(
        default="both", description="Target platform: google, blogger, or both"
    )
    max_length: int = Field(
        default=60, ge=30, le=100, description="Maximum title length"
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform is supported."""
        allowed = {"google", "blogger", "both"}
        if v.lower() not in allowed:
            raise ValueError(f"platform must be one of {allowed}, got {v}")
        return v.lower()


class SEOTitleResponse(BaseModel):
    """
    Response from SEO title generation.

    Attributes:
        title: Generated SEO title
        seo_score: SEO quality score (0-100)
        keyword_coverage: Percentage of keywords included
    """

    title: str = Field(..., description="Generated SEO title")
    seo_score: int = Field(ge=0, le=100, description="SEO quality score")
    keyword_coverage: int = Field(
        ge=0, le=100, description="Percentage of keywords included in title"
    )


class MetaOptimizationRequest(BaseModel):
    """
    Request for meta description optimization.

    Attributes:
        content: HTML content to extract from
        title: Post title
        target_keyword: Primary keyword to optimize for
        length: Target length for meta description
    """

    content: str = Field(..., min_length=1, description="Post content")
    title: str = Field(..., min_length=1, description="Post title")
    target_keyword: Optional[str] = Field(
        default=None, description="Primary keyword for optimization"
    )
    length: int = Field(
        default=155, ge=120, le=160, description="Target length (120-160 chars)"
    )


class MetaOptimizationResponse(BaseModel):
    """
    Response from meta description optimization.

    Attributes:
        meta_description: Optimized meta description
        original_score: Score before optimization
        optimized_score: Score after optimization
        character_count: Final character count
    """

    meta_description: str = Field(..., description="Optimized meta description")
    original_score: int = Field(ge=0, le=100, description="Score before optimization")
    optimized_score: int = Field(ge=0, le=100, description="Score after optimization")
    character_count: int = Field(description="Final character count")


class FAQRequest(BaseModel):
    """
    Request for FAQ generation.

    Attributes:
        content: Content to generate FAQs from
        title: Post title for context
        num_questions: Number of questions to generate
        style: FAQ style (paragraph, list, structured)
    """

    content: str = Field(..., min_length=50, description="Content for FAQ context")
    title: Optional[str] = Field(default=None, description="Post title")
    num_questions: int = Field(
        default=5, ge=1, le=20, description="Number of questions (1-20)"
    )
    style: str = Field(
        default="structured", description="FAQ style: paragraph, list, or structured"
    )


class FAQItem(BaseModel):
    """Single FAQ item with question and answer."""

    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")


class FAQResponse(BaseModel):
    """
    Response from FAQ generation.

    Attributes:
        faqs: List of generated FAQ items
        structured_html: FAQ formatted as HTML
    """

    faqs: List[FAQItem] = Field(default_factory=list, description="Generated FAQs")
    structured_html: str = Field(..., description="FAQ formatted as HTML")


class SummaryRequest(BaseModel):
    """
    Request for summary generation.

    Attributes:
        content: Content to summarize
        style: Summary style (brief, detailed, bullets)
        max_length: Maximum summary length
        include_key_points: Whether to extract key points
    """

    content: str = Field(..., min_length=50, description="Content to summarize")
    style: str = Field(
        default="brief", description="Summary style: brief, detailed, or bullets"
    )
    max_length: int = Field(
        default=200, ge=50, le=500, description="Maximum summary length"
    )
    include_key_points: bool = Field(
        default=False, description="Extract key points list"
    )


class SummaryResponse(BaseModel):
    """
    Response from summary generation.

    Attributes:
        summary: Generated summary
        key_points: Extracted key points (if requested)
        original_length: Original content length
        summary_length: Summary length
    """

    summary: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(
        default_factory=list, description="Extracted key points"
    )
    original_length: int = Field(description="Original content length in chars")
    summary_length: int = Field(description="Summary length in chars")


class KeywordOptimizationRequest(BaseModel):
    """
    Request for keyword optimization.

    Attributes:
        content: Existing content to optimize
        main_topic: Main topic of the content
        target_keywords: Keywords to focus on
        enhance_density: Whether to enhance keyword density
        max_suggestions: Maximum number of keyword suggestions
    """

    content: str = Field(..., min_length=1, description="Content to optimize")
    main_topic: str = Field(..., description="Main topic keyword")
    target_keywords: Optional[List[str]] = Field(
        default_factory=list, description="Target keywords to enhance"
    )
    enhance_density: bool = Field(
        default=True, description="Add keywords to improve density"
    )
    max_suggestions: int = Field(
        default=10, ge=1, le=50, description="Max keyword suggestions"
    )


class KeywordSuggestion(BaseModel):
    """Single keyword suggestion with metrics."""

    keyword: str = Field(..., description="Keyword suggestion")
    search_volume: Optional[int] = Field(
        default=None, description="Estimated monthly search volume"
    )
    difficulty: Optional[int] = Field(
        default=None, ge=0, le=100, description="SEO difficulty score (0-100)"
    )
    relevance: int = Field(ge=0, le=100, description="Relevance to topic (0-100)")


class KeywordOptimizationResponse(BaseModel):
    """
    Response from keyword optimization.

    Attributes:
        optimized_content: Content with enhanced keywords
        keyword_density: Dict of keyword:count ratios
        suggestions: List of related keyword suggestions
        seo_improvement: Estimated SEO score improvement
    """

    optimized_content: Optional[str] = Field(
        default=None, description="Content with enhanced keywords"
    )
    keyword_density: dict[str, float] = Field(
        default_factory=dict, description="Keyword:density ratios"
    )
    suggestions: List[KeywordSuggestion] = Field(
        default_factory=list, description="Related keyword suggestions"
    )
    seo_improvement: int = Field(
        ge=0, le=100, description="Estimated SEO score improvement"
    )

class SchemaMarkupRequest(BaseModel):
    """
    Request for schema markup generation.

    Attributes:
        title: Post title
        description: Meta description
        content: Full post content
        author: Author name
        image_url: Featured image URL
        publish_date: Publication date
        tags: List of tags/keywords
    """

    title: str = Field(..., description="Post title")
    description: str = Field(..., description="Meta description")
    content: str = Field(..., description="Full post content")
    author: Optional[str] = Field(default="Blog Author", description="Author name")
    image_url: Optional[str] = Field(default=None, description="Featured image URL")
    publish_date: Optional[str] = Field(default=None, description="Publication date (ISO)")
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tags")


class SchemaMarkupResponse(BaseModel):
    """
    Response from schema markup generation.

    Attributes:
        article_schema: Article JSON-LD schema
        faq_schema: FAQPage JSON-LD schema (if FAQs present)
        breadcrumb_schema: BreadcrumbList JSON-LD schema
        combined_schema: All schemas combined
    """

    article_schema: str = Field(..., description="Article JSON-LD schema")
    faq_schema: Optional[str] = Field(default=None, description="FAQPage JSON-LD schema")
    breadcrumb_schema: Optional[str] = Field(default=None, description="BreadcrumbList JSON-LD schema")
    combined_schema: str = Field(..., description="All schemas combined")


class InternalLinkRequest(BaseModel):
    """
    Request for internal linking suggestions.

    Attributes:
        content: Post content
        target_keywords: Primary keywords to link with
        related_posts: List of available posts to link to
    """

    content: str = Field(..., description="Post content")
    target_keywords: Optional[List[str]] = Field(
        default_factory=list, description="Keywords to find related posts"
    )
    related_posts: Optional[List[str]] = Field(
        default_factory=list, description="Available posts for linking"
    )


class InternalLinkSuggestion(BaseModel):
    """Single internal link suggestion."""

    url: str = Field(..., description="URL of the related post")
    title: str = Field(..., description="Title of the related post")
    anchor_text: str = Field(..., description="Suggested anchor text")


class InternalLinkResponse(BaseModel):
    """Response with internal linking suggestions."""

    suggestions: List[InternalLinkSuggestion] = Field(
        default_factory=list, description="List of link suggestions"
    )


class LSIKeywordRequest(BaseModel):
    """
    Request for LSI keyword generation.

    Attributes:
        topic: Main topic
        content: Existing content (optional)
        count: Number of LSI keywords to generate
    """

    topic: str = Field(..., description="Main topic")
    content: Optional[str] = Field(default=None, description="Existing content for context")
    count: int = Field(default=10, ge=1, le=50, description="Number of LSI keywords")


class LSIKeywordResponse(BaseModel):
    """Response with LSI keywords."""

    keywords: List[str] = Field(..., description="Generated LSI keywords")
    semantic_groups: dict = Field(
        default_factory=dict, description="Keywords grouped by semantic meaning"
    )


class KeywordDensityRequest(BaseModel):
    """
    Request for keyword density analysis.

    Attributes:
        content: Post content
        keywords: Keywords to analyze
    """

    content: str = Field(..., description="Post content")
    keywords: List[str] = Field(..., description="Keywords to analyze")


class KeywordDensityResult(BaseModel):
    """Keyword density result for a single keyword."""

    keyword: str = Field(..., description="Keyword")
    count: int = Field(..., description="Number of occurrences")
    density: float = Field(..., description="Keyword density percentage")
    recommended: bool = Field(..., description="Whether density is optimal (1-2%)")


class KeywordDensityResponse(BaseModel):
    """Response with keyword density analysis."""

    results: List[KeywordDensityResult] = Field(..., description="Density results")
    average_density: float = Field(..., description="Average keyword density")
    recommendations: List[str] = Field(default_factory=list, description="Optimization suggestions")


class OpenGraphRequest(BaseModel):
    """
    Request for Open Graph meta tag generation.

    Attributes:
        title: Post title
        description: Meta description
        image_url: Featured image URL
        url: Post URL
    """

    title: str = Field(..., description="Post title")
    description: str = Field(..., description="Meta description")
    image_url: Optional[str] = Field(default=None, description="Featured image URL")
    url: Optional[str] = Field(default=None, description="Post URL")


class OpenGraphResponse(BaseModel):
    """Response with Open Graph meta tags."""

    og_tags: dict = Field(..., description="Open Graph meta tags")
    twitter_tags: dict = Field(..., description="Twitter Card meta tags")
    html_meta_tags: str = Field(..., description="Complete HTML meta tags string")
