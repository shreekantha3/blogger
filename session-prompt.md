# New Session Prompt

Welcome to the Blogger Automation Platform! Here's the current state and where to start:

## 📊 Current Status

**Primary Goal:** Publish production-quality Blogger articles using AI

**Last Accomplished:**
- ✅ Published "Tata Sierra EV" article to https://www.gyanasangam.com
- ✅ SEO score: 92/100
- ✅ All 32 tests passing

## 🚀 Quick Start Commands

```bash
# Check current status
python3 -m pytest tests/ -v

# List accessible blogs
python3 app.py list-blogs

# Generate and publish an article
python3 app.py ai-generate --topic "YOUR_TOPIC" --publish --words 800

# Publish manually created content
python3 -c "
from core.models import BlogPost
from core.publishing import Publisher
post = BlogPost(title='Title', content='<h1>HTML content</h1>', labels=['tag'])
result = Publisher().publish(post)
print(f'Published: {result.url}')
"
```

## ⚙️ Current Settings

**Model:** `meta-llama/llama-3.3-70b-instruct:free` (free tier)

**Note:** Free models have rate limits and may occasionally return corrupted output. The platform handles this gracefully with fallback logic.

## 📁 Project Structure

```
├── ai/              # AI Engine (article generation, SEO titles, meta, FAQ)
├── core/            # Foundation (auth, models, blogger_client)
├── seo/             # SEO Engine (meta, headings, keywords, readability)
├── config/          # Settings and logging
├── data/            # Generated articles
├── tests/           # 32 unit tests
└── agents/          # Agent role documentation
```

## 🔧 What Needs Work

1. **Free Model Output Sanitization** - Sometimes returns reasoning text
2. **Phase 5: Media Engine** - Image upload/optimization
3. **Phase 6: Analytics** - Post performance tracking
4. **Phase 7: Web Dashboard** - Browser-based UI

## 📚 Key Files to Review

- `.env` - Current configuration (OpenRouter API key, blog ID, model settings)
- `CLAUDE.md` - Full platform documentation
- `goal.md` - Primary objectives
- `tasks.md` - Task tracking
- `decisions.md` - Architecture decisions