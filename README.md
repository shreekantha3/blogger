# Blogger Automation Platform

A production-grade platform for automating Blogger content creation, publishing, and SEO optimization.

## Architecture

This platform follows **Clean Architecture** principles with a layered design:

```
blogger-automation/
├── app.py                    # Entry point / CLI interface
├── config/                   # Configuration and logging
├── core/                     # Business logic (auth, API client, models)
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

### Phase 2: Publishing Engine
- [ ] Create/update/delete posts
- [ ] Draft and scheduled publishing
- [ ] Bulk publishing support
- [ ] Retry mechanism for failed operations

### Phase 3: SEO Engine
- [ ] SEO title generation
- [ ] Meta description optimization
- [ ] Readability analysis
- [ ] Keyword density checking
- [ ] Open Graph and Twitter Card support

### Phase 4: AI Engine
- [ ] AI article generation
- [ ] FAQ generation
- [ ] Summary generation
- [ ] Internal link suggestions
- [ ] Keyword optimization

### Phase 5: Media Engine
- [ ] Image generation (AI)
- [ ] Image optimization
- [ ] Thumbnail creation
- [ ] Blogger image upload

### Phase 6: Analytics
- [ ] Google Search Console integration
- [ ] Publishing analytics
- [ ] SEO reporting

### Phase 7: Web Dashboard
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