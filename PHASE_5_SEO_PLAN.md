# Phase 5 SEO Enhancement Implementation Plan

## RankMath SEO Research Summary

Based on comprehensive research of RankMath's official documentation, Google's Search Central guidelines, and authoritative SEO sources, here are the key findings for optimizing AI-generated content:

## 1. Content Structure Requirements

### Heading Hierarchy (H1-H6)

| Element | Requirement | RankMath Recommendation |
|---------|-------------|------------------------|
| **H1** | One per page | Match primary keyword, under 70 characters |
| **H2** | 3-5 main sections | Use semantic keywords, natural flow |
| **H3** | 2-3 subsections each | Under each H2 for detailed discussion |
| **H4-H6** | Deep nesting only | Avoid skipping levels (H1→H3 invalid) |

### Content Length Standards

- **Minimum**: 600 words (passes basic SEO test)
- **Recommended**: 2,500+ words for competitive topics
- **Optimal**: 3,000-3,500 words for authority content
- **AI Prompt**: "Generate 2,500+ words of comprehensive content"

### Readability Metrics

- **Flesch-Kincaid Grade Level**: 8th-10th grade
- **Sentence Length**: Average 15-20 words
- **Paragraph Length**: Maximum 120 words (3-4 sentences)
- **Passive Voice**: Keep under 20%

## 2. Schema Markup Recommendations

### Article/BlogPosting Schema

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Your Article Title",
  "description": "Meta description of the article",
  "author": {
    "@type": "Person",
    "name": "Author Name"
  },
  "datePublished": "2025-01-01",
  "dateModified": "2025-01-02",
  "image": "https://example.com/image.jpg",
  "keywords": "python, programming, tutorial",
  "publisher": {
    "@type": "Organization",
    "name": "Site Name",
    "logo": {
      "@type": "ImageObject",
      "url": "https://yoursite.com/logo.png"
    }
  }
}
```

### BreadcrumbList Schema

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://yoursite.com/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Blog",
      "item": "https://yoursite.com/blog/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Article Title",
      "item": "https://yoursite.com/article-url/"
    }
  ]
}
```

### ⚠️ FAQ Schema Deprecation

**Important**: Google deprecated FAQ rich results in May 2026. While FAQ schema markup still works, it no longer appears as rich results in Google Search. Focus on Article and Breadcrumb schemas for rich result eligibility.

## 3. Keyword Placement Strategy

### Primary Keyword Distribution

| Location | Requirement | Example |
|----------|-------------|---------|
| H1 Tag | 1 time | `<h1>Python Programming Guide</h1>` |
| First 10% | 1 time | First paragraph |
| H2 Headings | 2-3 times | `<h2>Python Programming Basics</h2>` |
| Meta Title | 1 time | "Python Programming Guide: Complete Tutorial" |
| Meta Description | 1 time | "Learn Python programming with this comprehensive guide..." |
| Content Body | 1-2% density | ~20-40 times in 2,500 words |

### Secondary Keyword Strategy

- Use in H3 headings
- Natural distribution throughout content
- Create keyword clusters around main topic
- LSI (Latent Semantic Indexing) keywords: 10+ variations

### AI Prompt Template for Keywords
```
Include primary keyword "python programming" in:
- H1 heading naturally
- First 10% of content
- At least 2 H2 headings
- Meta title and description
- Throughout content naturally (1-2% density)
```

## 4. Internal Linking Requirements

### Link Quantity
- **3-5 internal links per 1,000 words**
- For 2,500-word article: 8-12 internal links
- Plus 2-3 external authoritative links

### Anchor Text Best Practices
- Descriptive, keyword-rich (but natural)
- Vary anchor text (don't repeat same phrase)
- Link to cornerstone/pillar content
- Use "Fix with AI" to find missing internal link opportunities

### Content Clustering Strategy
```
Pillar Content (Comprehensive Guide)
├── Cluster 1 (Subtopic A)
├── Cluster 2 (Subtopic B)
├── Cluster 3 (Subtopic C)
└── Related Articles (Internal Links)
```

## 5. Image Optimization Standards

### Alt Text Generation
- **RankMath AI Alt Text**: Generate descriptive alt text using AI
- Available in Media Library or block editor
- Currently English-only feature

### File Naming Convention
```
Before: img12345.jpg
After: python-programming-tutorial.jpg
```

### Image Requirements
- **Dimensions**: 1200x630px (Open Graph standard)
- **File Size**: Under 100KB for web
- **Format**: WebP preferred, JPEG/PNG fallback
- **Quantity**: Minimum 4 images per post

### HTML Image Tag
```html
<img src="python-tutorial.jpg"
     alt="Python programming code example showing a for loop"
     title="Python For Loop Example"
     loading="lazy"
     width="1200"
     height="630">
```

## 6. Meta Description Best Practices

### Character Limits
- **Minimum**: 120 characters
- **Optimal**: 150-160 characters
- **Maximum**: 160 characters (Google's truncation point)

### Content Requirements
- Include primary keyword near beginning
- Compelling call-to-action (Learn, Discover, Understand)
- Unique for each page
- Accurately summarize content

### AI Prompt Template
```
Write a 155-character meta description for:
Title: "Complete Guide to Python Programming"
Keyword: "python programming"
Content: [First 200 chars of article]

Requirements:
- Include keyword naturally
- One compelling sentence
- No quotes or HTML
- 120-160 characters exactly
```

## 7. Open Graph & Twitter Card Requirements

### Open Graph Meta Tags

```html
<meta property="og:title" content="Article Title (50-60 chars)">
<meta property="og:description" content="Meta description (120-160 chars)">
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta property="og:url" content="https://example.com/article">
```

### Twitter Card Meta Tags

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Article Title">
<meta name="twitter:description" content="Meta description">
<meta name="twitter:image" content="https://example.com/image.jpg">
```

### Image Dimensions
- **Recommended**: 1200x630px
- **Aspect Ratio**: 1.91:1
- **File Size**: Under 5MB
- **Format**: JPEG, PNG, or GIF

## 8. Technical SEO Factors

### Core Web Vitals (Updated 2025)

| Metric | Requirement | Threshold |
|--------|-------------|-----------|
| LCP (Largest Contentful Paint) | Loading performance | ≤ 2.5 seconds |
| INP (Interaction to Next Paint) | Interactivity | ≤ 200 milliseconds |
| CLS (Cumulative Layout Shift) | Visual stability | ≤ 0.1 |

### Page Experience Signals
- Mobile-responsive design
- HTTPS with valid SSL certificate
- Safe browsing (no malware)
- Intrusive interstitial avoidance
- Page speed (under 3 seconds)

### SEO Score Thresholds (RankMath)

| Score | Status | Action |
|-------|--------|--------|
| 81-100 | Green | Good to go |
| 51-80 | Yellow | Needs improvement |
| 0-50 | Red | Major issues |

### RankMath 100/100 Requirements
- Content length: over 2,500 words
- Paragraph length: under 120 words
- Focus keyword in first 10% of content
- Focus keyword in SEO title and description
- External links present
- 4+ images or videos

## 9. AI-Generated Content Specific Recommendations

### Pre-Generation Planning
1. Create H1-H3 outline before generation
2. Define primary and secondary keywords
3. Plan content sections (6 H2 sections recommended)
4. Estimate word count (2,500+ for competitive topics)

### Generation Process
1. **AI Title Generation**: 50-60 characters with keywords
2. **Content Generation**: Specify structure and keyword placement
3. **Meta Description**: Generate 120-160 character description
4. **Image Alt Text**: Generate for all images
5. **Internal Links**: Use Link Genius to find opportunities
6. **Schema Markup**: Add Article and Breadcrumb JSON-LD

### Post-Processing for Free Models
1. Clean output artifacts (TITLE:, CONTENT: markers)
2. Fix heading structure (ensure H1-H2-H3 hierarchy)
3. Normalize whitespace and formatting
4. Ensure content completeness (no truncated sentences)
5. Verify keyword density (1-2%)

### AI Prompt Template for Article Generation

```
Generate a comprehensive blog post about {topic}.

Tone: {tone}
Length: {word_count} words (minimum 2,500 words)

Structure Requirements:
- Start with: <h1>{title}</h1>
- Include exactly 6 H2 sections: Introduction, Background, Current Situation, Analysis, Implications, Conclusion
- Under each H2, include 2-3 H3 subsections for detailed discussion
- Use primary keyword naturally in first 10% of content
- Include secondary keywords in H3 headings
- Keep paragraphs under 120 words (3-4 sentences max)
- Use active voice, 8th-10th grade reading level
- Add 4+ relevant images with descriptive alt text
- Include 3-5 internal links with keyword-rich anchor text

Keywords: {primary_keyword}, {secondary_keywords}

Format: HTML only, no markdown, start immediately with <h1>
```

## 10. Content Quality Score Optimization

### RankMath SEO Tests

1. **Basic SEO** (30 pts possible)
   - Focus keyword in SEO title
   - Focus keyword in meta description
   - Focus keyword in URL
   - Focus keyword at beginning of content
   - Content length

2. **Additional SEO** (40 pts possible)
   - Focus keyword in subheadings
   - Image alt attributes
   - Keyword density
   - URL length
   - External/internal links
   - Focus keyword uniqueness

3. **Title Readability** (20 pts possible)
   - Focus keyword at beginning
   - Sentiment
   - Power words
   - Numbers in title

4. **Content Readability** (10 pts possible)
   - Paragraph length
   - Media usage

### Achieving 95+ SEO Score

1. **Content Length**: Over 2,500 words
2. **Keyword Placement**: In title, meta, first 10%, headings
3. **Images**: 4+ with optimized alt text
4. **Links**: 3-5 internal + external links
5. **Readability**: Short paragraphs, simple language
6. **Structure**: Proper H1-H2-H3 hierarchy

## Implementation Checklist

### Schema Markup Generation
- [ ] Create `ai/schema_generator.py` module
- [ ] Generate Article JSON-LD from content
- [ ] Generate BreadcrumbList JSON-LD
- [ ] Combine all schemas into single output
- [ ] Add tests for schema validation

### Heading Structure Enforcement
- [ ] Update AI prompts in `ai/providers/openrouter_provider.py`
- [ ] Implement 6 H2 sections with 2-3 H3 subsections
- [ ] Add content length requirement (2,500+ words)
- [ ] Fix free model output structure issues
- [ ] Add tests for heading hierarchy

### Internal Linking
- [ ] Create `ai/internal_linking.py` module
- [ ] Implement Link Genius functionality
- [ ] Generate keyword-rich anchor text
- [ ] Find related posts based on content
- [ ] Add tests for linking suggestions

### LSI Keywords
- [ ] Implement semantic keyword generation
- [ ] Group keywords by semantic meaning
- [ ] Return 10+ LSI variations
- [ ] Add tests for keyword diversity

### Open Graph & Twitter Cards
- [ ] Update `ai/meta_optimizer.py` for social tags
- [ ] Generate OG title/description
- [ ] Generate Twitter Card tags
- [ ] Add tests for meta tag generation

### Keyword Density Validation
- [ ] Implement 1-2% density checking
- [ ] Track primary and secondary keywords
- [ ] Provide optimization suggestions
- [ ] Add tests for density validation

## Files to Create/Modify

### New Files
1. `ai/schema_generator.py` - Schema markup generation
2. `ai/internal_linking.py` - Internal linking suggestions
3. `media/image_selector.py` - Image selection logic

### Modified Files
1. `ai/providers/openrouter_provider.py` - Enhanced prompts for structure
2. `ai/generator.py` - Schema integration, content optimization
3. `app.py` - New CLI commands for SEO features
4. `tests/test_seo_enhancement.py` - Comprehensive SEO tests

## Success Criteria

- [ ] All existing tests pass (32 tests)
- [ ] New SEO tests added and passing
- [ ] Schema markup validates in Google Rich Results Test
- [ ] Content structure follows H1-H2-H3 hierarchy
- [ ] Internal links suggest 3-5 relevant posts
- [ ] LSI keywords include 10+ semantic variations
- [ ] Open Graph tags render correctly on social platforms
- [ ] Content achieves 95+ SEO score
- [ ] Article/BlogPosting schema validates
- [ ] BreadcrumbList schema validates

## Key Resources

- **RankMath SEO Guide**: https://rankmath.com/kb/seo-checklist/
- **Google Rich Results Test**: https://search.google.com/test/rich-results
- **Schema.org Article**: https://schema.org/Article
- **Schema.org BreadcrumbList**: https://schema.org/BreadcrumbList
- **Open Graph Protocol**: https://ogp.me/
- **Core Web Vitals**: https://web.dev/vitals/
- **Google SEO Starter Guide**: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
