# Phase 6 CLI Commands Reference

## Analytics Commands

| Command | Description | Example |
|---------|-------------|---------|
| `analytics-top-queries` | Get top GSC queries | `python app.py analytics-top-queries --days 90 --limit 100` |
| `analytics-audit` | Run content audit | `python app.py analytics-audit --detect-decaying --decaying-threshold 20` |
| `refresh-audit` | Content refresh audit | `python app.py refresh-audit --threshold 20` |

## SERP Analysis Commands

| Command | Description | Example |
|---------|-------------|---------|
| `serp-analyze` | SERP feature extraction | `python app.py serp-analyze --keyword "ksp recruitment" --location "IN"` |
| `content-brief` | Generate content brief | `python app.py content-brief --topic "Police" --keyword "ksp constable"` |

## Schema Commands

| Command | Description | Example |
|---------|-------------|---------|
| `schema-job` | JobPosting schema | `python app.py schema-job --title "KSP Police" --date "2026-07-15"` |
| `schema-howto` | HowTo schema | `python app.py schema-howto --title "How to Apply" --steps '[{"text":"Step 1"}]'` |

## AI Image Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ai-image` | Generate AI images | `python app.py ai-image --type feature --title "My Post"` |
| `ai-image` | Generate diagrams | `python app.py ai-image --type diagram --topic "Process"` |

## Keyword Research Commands

| Command | Description | Example |
|---------|-------------|---------|
| `keywords-research` | Keyword opportunities | `python app.py keywords-research --seed "recruitment" --easy-wins` |
| `internal-links` | Link suggestions | `python app.py internal-links --topic "police" --top-k 5` |

## Approval Workflow Commands

| Command | Description | Example |
|---------|-------------|---------|
| `brief-create` | Create for approval | `python app.py brief-create --topic "KSP" --keyword "ksp constable"` |

## Original CLI Commands (Phases 1-5)

### Authentication
```bash
python app.py auth
python app.py list-blogs
```

### Publishing
```bash
python app.py publish --title "Title" --content "<h1>Content</h1>" --labels "tag1,tag2"
python app.py schedule --title "Future" --when "2026-08-01"
python app.py update --post-id "123" --title "New Title"
python app.py delete --post-id "123" --confirm
python app.py bulk-publish --file data/posts.json
```

### SEO
```bash
python app.py seo-check --title "Test" --content "..."
python app.py ai-generate --topic "Python" --tone professional --words 800
python app.py ai-title --topic "..." --keywords "python,seo"
python app.py ai-meta --title "My Post" --content "..." --keyword "python"
python app.py ai-faq --title "..." --content "..." --count 5
python app.py ai-summary --content "..." --style brief
python app.py ai-keywords --topic "Python" --content "..."
python app.py eeat-score --title "..." --content "..."
```

### Media
```bash
python app.py image-optimize --input photo.jpg --output optimized.jpg
python app.py thumbnail --title "My Post" --output thumb.jpg --type og
python app.py images-suggest --topic "Python" --count 4
```