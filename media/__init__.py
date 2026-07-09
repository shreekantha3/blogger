"""
Media Engine for Blogger Automation Platform (Phase 5).

ARCHITECTURAL DECISION: Media Processing Pipeline
----------------------------------------------------
The Media Engine provides:
1. Image processing and optimization
2. Thumbnail generation for social sharing
3. Media storage integration (local, S3, Cloudinary)
4. Image selection and alt text generation

Based on RankMath SEO guidelines requiring:
- 1200x630px images for Open Graph
- 4+ images per post with descriptive alt text
- WebP format for optimal performance
"""

from media.image_processor import ImageProcessor, ImageOptimizationConfig
from media.thumbnail_generator import ThumbnailGenerator, ThumbnailConfig
from media.storage import StorageBackend, LocalStorage, S3Storage, CloudinaryStorage
from media.image_selector import ImageSelector, ImageSuggestion

__all__ = [
    # Image Processing
    "ImageProcessor",
    "ImageOptimizationConfig",
    # Thumbnail Generation
    "ThumbnailGenerator",
    "ThumbnailConfig",
    # Storage
    "StorageBackend",
    "LocalStorage",
    "S3Storage",
    "CloudinaryStorage",
    # Image Selection
    "ImageSelector",
    "ImageSuggestion",
]