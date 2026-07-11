# Thumbnail Publishing Feature (2026-07-11)

## Summary
Added native Blogger image upload capability with texture-based thumbnails.

## Changes Made

1. **BloggerClient.upload_image()** - Uploads image bytes directly to Blogger's media storage using `MediaIoBaseUpload`

2. **Publisher._select_texture()** - Auto-selects from `media/textures/` based on topic hash (consistent per topic)

3. **CLI --thumbnail flag** - Add `--thumbnail` to publish command to auto-generate and embed thumbnails

4. **publish_all_thumbnails.py** - Batch script to publish all recruitment articles with thumbnails

## Usage

```bash
# Publish with auto thumbnail
python3 app.py publish --title "AIIMS Recruitment 2026" --content "<h1>...</h1>" --labels "recruitment,medical" --thumbnail

# Or batch publish all
python3 publish_all_thumbnails.py
```

## Texture Selection

- Uses `hash(topic) % len(textures)` for deterministic selection
- Same topic always gets the same texture
- 16 dark-textured backgrounds available in `media/textures/`

## How to apply

Use `--thumbnail` flag when publishing to have auto-generated featured images.