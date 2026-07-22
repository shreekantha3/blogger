# Blogger Automation Platform

Production-grade platform for automated Blogger content creation, publishing, and SEO optimization.

## Architecture

Built in phases following clean architecture principles:
- **Phase 1**: Foundation (config, auth, models, exceptions) ✅
- **Phase 2**: Publishing Engine (retry, queue, publisher) ✅
- **Phase 3**: SEO Engine (meta, headings, keywords, readability) ✅
- **Phase 4**: AI Engine (article generation, SEO titles, meta optimization, FAQ, summary, keywords) ✅ Enhanced
- **Phase 5**: Media Engine (image optimization, thumbnails, storage) ✅ Completed
  - `media/image_processor.py` - Image compression, WebP conversion
  - `media/thumbnail_generator.py` - 1200x630 social thumbnails
  - `media/storage.py` - Storage backends (Local, S3, Cloudinary)
  - `media/image_selector.py` - Alt text generation, Unsplash integration
  - `seo/quality_scorer.py` - EEAT content quality scoring
  - `ai/fact_checker.py` - Factual claim verification

- **Phase 6**: Analytics + Strategy Layer ✅ In Progress
  - `analytics/gsc_client.py` - Google Search Console API integration
  - `analytics/ga4_client.py` - GA4 Measurement Protocol client
  - `analytics/content_audit.py` - Decaying/stale post detection
  - `seo/serp_analyzer.py` - SERP feature extraction, competitor analysis
  - `ai/content_brief.py` - Content brief generation before AI writing
  - `ai/schema_howto.py` - HowTo, JobPosting, VideoObject schemas
  - `media/ai_image_generator.py` - DALL-E 3 integration for custom visuals
  - `seo/keyword_research.py` - Keyword opportunity discovery
  - `ai/internal_link_graph.py` - PageRank-based link analysis

## Key Patterns

| Module | Pattern | Purpose |
|--------|---------|---------|
| `config/settings.py` | Singleton + Pydantic | Validated, cached configuration |
| `core/auth.py` | Service | OAuth 2.0 with google-auth library |
| `core/blogger_client.py` | Facade | Simplified Blogger API wrapper |
| `core/publishing/retry.py` | Strategy | Configurable retry with exponential backoff |
| `core/publishing/queue.py` | Active Record | JSON-based publish queue |
| `core/publishing/publisher.py` | Facade | Publishing orchestration |
| `seo/analyzer.py` | Composite | Combined SEO checks |
| `ai/generator.py` | Facade | AI content generation orchestrator |
| `ai/providers/base.py` | Strategy | Abstract provider interface |
| `ai/providers/anthropic_provider.py` | Adapter | Anthropic Claude SDK wrapper |
| `ai/providers/openrouter_provider.py` | Adapter | OpenRouter unified API wrapper |

## CLI Usage

```bash
# Authentication
python app.py auth

# Publish single post
python app.py publish --title "My Title" --content "<h1>Content</h1>" --labels "python,automation"

# Schedule post for future publishing
python app.py schedule --title "Future Post" --when "2026-07-10T10:00:00"

# Update an existing post
python app.py update --post-id "123456789" --title "New Title" --labels "python,ai"

# Delete a post
python app.py delete --post-id "123456789"

# Bulk publish from JSON
python app.py bulk-publish --file data/sample_posts.json

# SEO check
python app.py seo-check --title "Test" --content "<h1>...</h1><p>...</p>"

# AI Content Generation (Phase 4)
python app.py ai-generate --topic "Python Tips" --tone professional --keywords "python,coding" --words 800

# AI SEO Title Generation
python app.py ai-title --topic "Python Tips" --keywords "python,programming"

# AI Meta Description Optimization
python app.py ai-meta --title "My Post" --content "<p>Post content</p>" --keyword "python"

# AI FAQ Generation
python app.py ai-faq --title "Python Guide" --content "<p>Python content...</p>" --count 5

# AI Summary Generation
python app.py ai-summary --content "<p>Long content...</p>" --style brief

# AI Keyword Optimization
python app.py ai-keywords --topic "Python" --content "<p>Content...</p>"

# Phase 5: Media Engine
python app.py image-optimize --input photo.jpg --output optimized.jpg --quality 85
python app.py thumbnail --title "My Article" --output thumb.jpg --type og
python app.py images-suggest --topic "Python" --count 4
python app.py eeat-score --title "My Post" --content "<p>...</p>"

# Phase 6: Analytics + Strategy
# Analytics
python app.py analytics-top-queries --days 90
python app.py analytics-audit --detect-decaying

# SERP Analysis
python app.py serp-analyze --keyword "ksp recruitment" --location "IN"
python app.py content-brief --topic "Police Exam" --keyword "ksp constable"

# Schema Generation
python app.py schema-job --title "KSP Recruitment 2026" --date "2026-07-15"
python app.py schema-howto --title "How to Apply" --steps '[{"text": "Step 1"}, {"text": "Step 2"}]'

# AI Images
python app.py ai-image --type feature --title "My Article" --topic "Recruitment"

# Keyword Research
python app.py keywords-research --seed "recruitment" --easy-wins
python app.py internal-links --topic "ksp"
```

**Note:** For AI commands, set `OPENROUTER_API_KEY` in `.env` (recommended) or `ANTHROPIC_API_KEY`.

**Note:** For image processing, install Pillow with: `pip install pillow`

## AI Provider Options

| Provider | Models Available | Use Case |
|----------|-----------------|----------|
| openrouter | Llama-3.3-70b (free), Claude 5, GPT-4, etc. | Recommended - unified access |
| anthropic | Claude models | Direct Anthropic access |
| openai | GPT models | Direct OpenAI access |

### OpenRouter Free Model

For no-cost usage, the platform supports OpenRouter's free models:
- `poolside/laguna-m.1:free` - Poolside Laguna (recommended)
- `google/gemma-4-26b-a4b-it:free` - Gemma 4 26B
- Set in `.env`: `AI_DEFAULT_MODEL=poolside/laguna-m.1:free`

## Engineering Standards

Never generate quick fixes.

Always prefer maintainability.

Always separate business logic.

Never hardcode credentials.

Always use type hints.

Always use logging.

Every module must have docstrings.

Every public function must contain examples.

## JSON Format for Bulk Publishing

`data/sample_posts.json`:
```json
{
  "posts": [
    {
      "title": "Post Title",
      "content": "<h1>HTML Content</h1>",
      "labels": ["tag1", "tag2"]
    }
  ]
}
```

## Testing

```bash
pytest tests/ -v
```

All 97 tests pass (20 new media tests added in Phase 5).

## Recent Improvements (2026-07-09)

### Phase 5: Media Engine
- **Image Processing**: Added `ImageProcessor` for compression and WebP conversion
- **Thumbnail Generation**: Added `ThumbnailGenerator` for 1200x630 social thumbnails
- **Storage Integration**: Added `LocalStorage`, `S3Storage`, `CloudinaryStorage` backends
- **Image Selection**: Added `ImageSelector` for alt text generation and Unsplash integration
- **EEAT Quality Scoring**: Added `QualityScorer` for content quality evaluation
- **Fact Checking**: Added `FactChecker` for factual claim verification

## Recent Improvements (2026-07-04)

### Phase 2: Publishing Engine
- **Scheduled Post Publishing**: Queue now preserves `published` datetime for proper scheduling
- **Update/Delete Operations**: Added `update_post()` and `delete_post()` methods with CLI commands

### Phase 4: AI Engine Enhancements
- **Free Model Output Handling**: Added cleaning, HTML structure fixes, and optimization methods
- **Improved Prompt Engineering**: Better instructions for free models to produce cleaner output
- **Defensive Parsing**: Multiple fallback strategies for parsing free model responses
