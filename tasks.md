# Project Tasks

## Phase 1: Foundation

- [x] Build auth.py (Google OAuth with google-auth)
- [x] Build config.py (Pydantic settings)
- [x] Build logger (structured logging)
- [x] Test Blogger API connection

## Phase 2: Publishing Engine

- [x] OAuth completed
- [x] Desktop App created
- [x] Publish first post to Blogger
- [ ] Test scheduled posts

## Phase 3: SEO Engine

- [ ] Title optimization
- [ ] Meta description generation
- [ ] Schema markup
- [ ] Internal linking suggestions
- [ ] Keyword density optimization
- [ ] Readability improvements

## Phase 4: AI Engine (Current Focus)

- [x] Basic article generation working
- [x] SEO title generation
- [x] Meta optimization (with free model issues)
- [x] FAQ generation (with defensive parsing)
- [ ] Free model output sanitization
- [ ] HTML validation
- [ ] Structured data (FAQ schema)

## Phase 5: SEO Enhancement (Current Priority)

### High Priority Tasks

1. **Schema Markup Generation**
   - [ ] Article/BlogPosting JSON-LD schema generation
   - [ ] BreadcrumbList JSON-LD schema generation
   - [ ] Combined schema output for all markup types
   - [ ] Integration with AIArticleGenerator

2. **H1-H6 Hierarchy Enforcement**
   - [ ] Update AI prompts for 5-7 H2 sections with 2-3 H3 subsections each
   - [ ] Content length: 2,500+ words for competitive topics
   - [ ] Proper heading structure validation
   - [ ] Free model output structure fixing

3. **Internal Linking Suggestions**
   - [ ] Link Genius implementation (find related posts)
   - [ ] Keyword-rich anchor text generation
   - [ ] 3-5 internal links per 1,000 words
   - [ ] Content clustering strategy

4. **LSI Keyword Generation**
   - [ ] Semantic keyword variations
   - [ ] 10+ LSI keywords per topic
   - [ ] Keyword grouping by semantic meaning

5. **Open Graph & Twitter Card Tags**
   - [ ] OG title and description generation
   - [ ] Twitter Card meta tags
   - [ ] Image dimensions (1200x630px recommended)
   - [ ] Social media optimization

6. **Keyword Density Validation**
   - [ ] 1-2% keyword density check
   - [ ] Primary and secondary keyword tracking
   - [ ] Optimization recommendations

### Medium Priority Tasks

- [ ] Featured image alt text generation
- [ ] Image optimization recommendations
- [ ] Content quality score improvement to 95+

## Article Writing Format (RankMath-Optimized)

### Content Structure Requirements

**Word Count**: 2,500+ words minimum for competitive topics

**Heading Hierarchy**:
- 1 H1 tag (main title, matches primary keyword)
- 5-7 H2 sections: Introduction, Background, Current Situation, Analysis, Implications, Conclusion
- 2-3 H3 subsections under each H2 for detailed discussion

**Example Structure**:
```html
<h1>Complete Guide to Python Programming</h1>

<h2>Introduction</h2>
<p>Opening paragraph with primary keyword in first 10% of content...</p>
<h3>What is Python?</h3>
<p>Detailed explanation...</p>
<h3>Python vs Other Languages</h3>
<p>Comparison discussion...</p>

<h2>Background</h2>
<p>Historical context...</p>
<h3>History of Python</h3>
<p>Detailed history...</p>
<h3>Key Milestones</h3>
<p>Milestone discussion...</p>

<!-- Continue with Analysis, Implications, Conclusion -->
```

### Content Quality Requirements

- **Paragraph Length**: Maximum 120 words (3-4 sentences)
- **Readability**: 8th-10th grade level (Flesch-Kincaid)
- **Keyword Placement**:
  - Primary keyword in H1, first 10%, H2 headings, meta title, meta description
  - Secondary keywords in H2/H3 headings
  - Natural distribution: 1-2% keyword density

- **Images**: Minimum 4 images/videos with AI-generated alt text
- **Internal Links**: 3-5 per 1,000 words with keyword-rich anchor text
- **External Links**: 2-3 authoritative sources

### Meta Description Requirements

- Length: 120-160 characters
- Include primary keyword near beginning
- Compelling call-to-action
- Unique per page

### Open Graph & Twitter Card Requirements

- og:title: 50-60 characters
- og:description: 120-160 characters
- og:image: 1200x630px recommended
- twitter:card: summary_large_image

## Current Sprint: Publish Tata Sierra EV Article

- [ ] Generate clean article content (2,500+ words)
- [ ] Generate proper meta description (120-160 chars)
- [ ] Ensure proper H1-H2-H3 heading structure
- [ ] Include 4+ images with alt text
- [ ] Add 3-5 internal links
- [ ] Generate Article and Breadcrumb schema markup
- [ ] Publish to Blogger
- [ ] Verify SEO score (target: 95+)
- [ ] Update documentation
