"""
AI Engine for Blogger Automation Platform (Phase 4).

ARCHITECTURAL DECISION: Provider Abstraction Pattern
---------------------------------------------------
We use a provider abstraction pattern because:
1. Supports multiple LLM providers (Anthropic, OpenAI)
2. Each provider can be developed and tested independently
3. Allows easy switching between providers via configuration
4. Enables failover between providers if needed

Components:
- models.py: Pydantic models for requests/responses
- exceptions.py: AI-specific exceptions
- providers/: Abstract and concrete provider implementations
- generator.py: Main AI content generator
- seo_title.py: SEO-optimized title generation
- meta_optimizer.py: Meta description optimization
- faq_generator.py: FAQ generation from content
- summary_generator.py: Content summarization
- keyword_optimizer.py: Keyword optimization and suggestions
- fact_checker.py: Fact checking against reference sources
"""

from ai.models import (
    AIArticleRequest,
    AIArticleResponse,
    SEOTitleRequest,
    SEOTitleResponse,
    MetaOptimizationRequest,
    MetaOptimizationResponse,
    FAQRequest,
    FAQResponse,
    SummaryRequest,
    SummaryResponse,
    KeywordOptimizationRequest,
    KeywordOptimizationResponse,
)
from ai.generator import AIArticleGenerator
from ai.seo_title import SEOTitleGenerator
from ai.meta_optimizer import MetaDescriptionOptimizer
from ai.faq_generator import FAQGenerator
from ai.summary_generator import SummaryGenerator
from ai.keyword_optimizer import KeywordOptimizer
from ai.schema_generator import SchemaGenerator, HowToStep
from ai.fact_checker import FactChecker

__all__ = [
    # Models
    "AIArticleRequest",
    "AIArticleResponse",
    "SEOTitleRequest",
    "SEOTitleResponse",
    "MetaOptimizationRequest",
    "MetaOptimizationResponse",
    "FAQRequest",
    "FAQResponse",
    "SummaryRequest",
    "SummaryResponse",
    "KeywordOptimizationRequest",
    "KeywordOptimizationResponse",
    # Generators
    "AIArticleGenerator",
    "SEOTitleGenerator",
    "MetaDescriptionOptimizer",
    "FAQGenerator",
    "SummaryGenerator",
    "KeywordOptimizer",
    "SchemaGenerator",
    "HowToStep",
    "FactChecker",
]