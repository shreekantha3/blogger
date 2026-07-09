"""
Media Engine for Blogger Automation Platform (Phase 5).

ARCHITECTURAL DECISION: Image Selection Pattern
------------------------------------------------
This module handles image-related features for SEO:
1. Alt text generation
2. Image selection from Unsplash/Pexels
3. Open Graph optimized images
4. Image validation for SEO requirements

Based on RankMath SEO guidelines requiring 4+ images per post
with descriptive alt text for accessibility and SEO.
"""

from media.image_selector import ImageSelector, ImageSuggestion

__all__ = [
    "ImageSelector",
    "ImageSuggestion",
]