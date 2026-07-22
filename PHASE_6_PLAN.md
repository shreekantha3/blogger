# Phase 6 Implementation Plan: Analytics + Strategy Layer

## The Hard Truth (From Honest Code Review)
You built a Ferrari engine (Phases 1-5) but put it in a go-kart (no strategy, no analytics, no feedback loop).

The code is clean, tested, extensible — hireable senior engineer work. But as a content business, you're missing the parts that actually drive traffic.

## Priority Implementation Order

### Priority 1: GSC/GA4 Integration (Days 1-3)
**Goal:** Data-driven everything - close the feedback loop

**Files to create:**
- `analytics/gsc_client.py` - Search Console API client
- `analytics/ga4_client.py` - GA4 Measurement Protocol client
- `analytics/models.py` - Data models for analytics

**Key capabilities:**
- `get_top_queries(days=90)` - Returns query, clicks, impressions, CTR, position
- `get_url_performance(url)` - Traffic trend, position history
- `submit_urls(urls)` - IndexNow/Instant Indexing API
- `get_decaying_posts(threshold=20%)` - Posts with traffic drop YoY

### Priority 2: SERP Analyzer + Content Brief (Days 3-5)
**Goal:** Answer "what to write" - competitive content strategy

**Files to create:**
- `seo/serp_analyzer.py` - SERP feature detection and competitor analysis
- `ai/content_brief.py` - Content brief data models and generator
- `seo/models.py` - Extend with SERP and Brief models

**Key capabilities:**
- Extract top 10 URLs, word counts, structures, PAA questions
- Identify content gaps, missing entities, schema opportunities
- Generate content brief with recommended H2 sections

### Priority 3: Content Refresh Scheduler (Days 5-7)
**Goal:** Highest ROI activity (refresh > new)

**Files to create:**
- `analytics/refresh_scheduler.py` - Auto-detect decaying posts
- `analytics/content_audit.py` - Stale content and orphan page detection

**Key capabilities:**
- Run weekly audit and identify priority updates
- Detect outdated stats, broken links, new competitors
- Generate update briefs with specific fixes

### Priority 4: AI Image Generation (Days 7-9)
**Goal:** Visual differentiation, unique feature images

**Files to create:**
- `media/ai_image_generator.py` - DALL-E 3/Flux API integration
- `media/diagram_generator.py` - Technical diagrams from content

**Key capabilities:**
- `generate_feature_image(title, topic, brand_colors)` - Custom OG images
- `generate_diagram(concept, data)` - Data visualizations
- `generate_chart(chart_type, data, title)` - Charts and graphs

### Priority 5: Expanded Schema Types (Days 9-10)
**Goal:** Rich snippets = CTR improvement

**Files to extend:**
- `ai/schema_generator.py` - Add HowTo, JobPosting, VideoObject, Course, Product

**Current schemas:**
- Article, FAQ, BreadcrumbList (already implemented)

**Missing schemas:**
- HowToStep, HowToSection, HowTo - Tutorial rich snippets
- JobPosting - Recruitment article schema (high priority!)
- VideoObject - Video content support
- Course, LearningResource - Educational content
- Product, Review - Affiliate/commercial opportunities

### Priority 6: Internal Link Graph (Days 10-11)
**Goal:** Authority distribution, better topical clusters

**Files to extend:**
- `ai/internal_linking.py` - PageRank-based graph analysis

**Key capabilities:**
- Build content graph (nodes = posts, edges = semantic links)
- Find orphan pages that need links
- Find authority hubs to boost new content

### Priority 7: Event-Driven Architecture (Days 11-13)
**Goal:** Decouple, trace, debug workflows

**Files to create:**
- `core/events.py` - Domain events for tracing workflows
- `workflows/new_content_pipeline.py` - Strategy orchestration
- `workflows/content_refresh_pipeline.py` - Refresh automation

### Priority 8: Keyword Research Module (Days 13-15)
**Goal:** Find opportunities, not just check density

**Files to create:**
- `seo/keyword_research.py` - Keyword clustering and opportunity finding

**Key capabilities:**
- Get suggestions (GSC, free APIs, or scraped)
- Cluster by intent (informational, commercial, transactional)
- Map to content pillars
- Identify "easy wins" (low difficulty, decent volume)

## Architecture: Strategy Layer Separation

```
blogger-automation/
├── engine/           # What you have (publishing, AI, SEO, media)
│   ├── publishing/
│   ├── ai/
│   ├── seo/
│   └── media/
├── strategy/         # NEW — Business logic layer
│   ├── keyword_research/
│   ├── serp_analysis/
│   ├── content_briefs/
│   ├── competitor_intel/
│   └── content_audit/
├── analytics/        # NEW — Feedback loop
│   ├── gsc/
│   ├── ga4/
│   ├── rank_tracking/
│   └── reporting/
└── workflows/        # NEW — Orchestration
    ├── new_content_pipeline/
    ├── content_refresh_pipeline/
    └── link_building_pipeline/
```

## CLI Commands to Add

```bash
# Analytics (Priority 1)
python app.py analytics-top-queries --days 90
python app.py analytics-url-performance --url "..."
python app.py analytics-audit --detect-decaying

# SERP Analysis (Priority 2)
python app.py serp-analyze --keyword "..." --location "IN"
python app.py content-brief --topic "..." --keyword "..."

# Content Refresh (Priority 3)
python app.py refresh-detect --threshold 20
python app.py refresh-update --post-id "..."

# AI Images (Priority 4)
python app.py ai-image --type feature --title "..." --topic "..."
python app.py ai-diagram --concept "..." --data '{"key": "value"}'

# Schemas (Priority 5)
python app.py schema-howto --title "..." --steps "..." --output schema.json
python app.py schema-job --title "..." --date "2026-07-15" --output schema.json

# Internal Linking (Priority 6)
python app.py internal-links --topic "..." --top-k 5
```

## Quick Wins for Existing Recruitment Articles

Based on the review, recruitment articles need:
1. **JobPosting schema** - HIGH PRIORITY (recruitment = job listings)
2. **Step-by-step "How to Apply" diagrams** - Visual differentiation
3. **Insider tips sections** - Personal experience / E-E-A-T
4. **Topic-wise weightage analysis** - Original data vs copy notification
5. **Medical standards deep-dive** - More detailed than official notifications

## Testing Strategy

Each new module must have:
- Unit tests in `tests/test_analytics.py`, `tests/test_serp.py`, etc.
- Integration tests for API clients (mocked)
- Schema validation tests
- End-to-end workflow tests

## Dependencies to Add

```
# Future phases
openai>=1.51.0  # For DALL-E 3 integration
serpapi>=1.0.0  # For SERP analysis (or httpx for scraping)
# or free alternatives:
google-search-results>=4.0.0  # SerpAPI wrapper
```