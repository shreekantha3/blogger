"""
SEO Engine for Blogger Automation Platform.

ARCHITECTURAL DECISION: Analyzer Pattern
----------------------------------------
Each SEO check is a separate analyzer that can:
1. Be tested independently
2. Provide specific feedback for failures
3. Be combined into a comprehensive report
4. Be extended with new rules easily

This follows the Single Responsibility Principle - each class
has one reason to change.

Future: In Phase 7, these analyzers will power the web dashboard
showing SEO scores and suggestions.
"""

from seo.analyzer import SEOAnalyzer
from seo.meta import MetaDescriptionGenerator
from seo.headings import HeadingAnalyzer
from seo.keywords import KeywordAnalyzer
from seo.readability import ReadabilityAnalyzer

__all__ = [
    "SEOAnalyzer",
    "MetaDescriptionGenerator",
    "HeadingAnalyzer",
    "KeywordAnalyzer",
    "ReadabilityAnalyzer",
]