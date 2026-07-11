# Blogger Automation Platform

A production-grade platform for automating Blogger content creation, publishing, and SEO optimization with AI-powered content generation and multilingual support.

## Architecture

This platform follows **Clean Architecture** principles with a layered design:

```
blogger-automation/
├── app.py                    # Entry point / CLI interface
├── config/                   # Configuration and logging
├── core/                     # Business logic (auth, API client, models)
├── ai/                       # AI generation and optimization
├── utils/                    # Shared utility functions
├── tests/                    # Test suite
```

## Features

### Phase 1: Foundation ✓
- [x] Modern Google OAuth (google-auth) migration
- [x] Centralized configuration with validation
- [x] Structured logging with JSON support
- [x] Clean exception hierarchy
- [x] API client wrapper with error handling
- [x] Domain models using dataclasses

### Phase 2: Publishing Engine ✓
- [x] Create/update/delete posts
- [x] Draft and scheduled publishing
- [x] Bulk publishing support
- [x] Retry mechanism with exponential backoff

### Phase 3: SEO Engine ✓
- [x] SEO title generation
- [x] Meta description optimization
- [x] Readability analysis
- [x] Keyword density checking
- [x] Open Graph and Twitter Card support
- [x] Schema markup generation (Article, FAQ, BreadcrumbList)
- [x] LSI keyword generation with semantic clustering
- [x] Internal linking suggestions

### Phase 4: AI Engine ✓
- [x] AI article generation (Claude, GPT, OpenRouter models)
- [x] Multilingual support (English, Kannada, Hindi, Spanish, French, German, Chinese, Japanese, Tamil, Telugu)
- [x] FAQ generation
- [x] Summary generation
- [x] Keyword optimization with LSI keywords
- [x] SEO title generation
- [x] Meta description optimization
- [x] Content structure fixing for SEO compliance

### Phase 5: Media Engine ✓
- [x] Image optimization (ImageProcessor)
- [x] WebP format conversion
- [x] Thumbnail creation (1200x630, Twitter, Square)
- [x] Storage backends (Local, S3, Cloudinary)
- [x] Image alt text generation
- [x] EEAT quality scoring

### Phase 6: Multi-Account & Post Management ✓
- [x] `list_posts()` - Fetch all existing posts
- [x] `list-posts` CLI - Display posts with IDs and titles
- [x] `seo-audit` CLI - Batch SEO analysis of published posts
- [x] `post-optimize` CLI - Review and AI-optimize existing posts
- [x] AccountProfile - Multi-account configuration model
- [x] AccountManager - Multiple account support
- [x] `accounts`, `account-add`, `publish-to` CLI commands

### Phase 7: Analytics (Planned)
- [ ] Google Search Console integration
- [ ] Publishing analytics
- [ ] SEO reporting

### Phase 8: Web Dashboard (Planned)
- [ ] FastAPI backend
- [ ] React/TypeScript frontend
- [ ] Real-time publishing status

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd blogger-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy `.env` to `.env.local` and fill in your values:

```bash
cp .env .env.local
```

2. Ensure `client_secret.json` is in the root directory (create via Google Cloud Console)

3. The platform will prompt for OAuth authentication on first run

## Usage

### Simple CLI

```bash
# Test authentication
python app.py

# Authenticate (opens browser)
python app.py auth

# List accessible blogs
python app.py list-blogs

# Publish a post
python app.py publish --title "My Post" --labels "python,automation"

# Phase 6: Existing Post Management
python app.py list-posts --status published --limit 50    # List existing posts
python app.py seo-audit --max-results 100                  # SEO audit all posts
python app.py post-optimize --post-id 123456789 --auto-fix  # Optimize existing post

# Phase 6: Multi-Account Support
python app.py accounts                                   # List all accounts
python app.py account-add --name "work"                  # Add new account
python app.py publish-to --account "work" --title "..."   # Publish to specific account
```

### Programmatic Usage

```python
from core.auth import Authenticator
from core.blogger_client import BloggerClient
from core.models import BlogPost

# Authenticate
auth = Authenticator()
credentials = auth.load_credentials()

# Publish a post
client = BloggerClient()
post = BlogPost(
    title="My First Automated Post",
    content="<h1>Hello World</h1><p>Automated content!</p>",
    labels=["automation", "tutorial"]
)
result = client.publish_post(post)

if result.success:
    print(f"Published: {result.url}")
```

## Development Standards

- **Type hints** on all functions
- **Dataclasses** for data models
- **Custom exceptions** with context
- **Structured logging** for observability
- **No hardcoded values** - everything configurable
- **Testable design** - all modules designed for mocking

## License

MIT