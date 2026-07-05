# Changelog

## 2026-06-30

### Added
- Authentication with google-auth (migrated from deprecated oauth2client)
- OAuth token persistence to credentials.storage
- AI Engine with OpenRouter integration
- Free model support (meta-llama/llama-3.3-70b-instruct:free)
- Published "Tata Sierra EV" article to Blogger (SEO score: 92/100)

### Fixed
- Credentials loading - now uses `google.oauth2.credentials.Credentials`
- Meta description sanitization for free model output
- FAQ parsing with fallback formats
- Credentials saving - fixed `to_json()` method

### Changed
- Updated default model to Llama 3.3 70B free
- Increased AI_MAX_TOKENS to 10000 for larger context window

## 2026-01-15

### Added
- Initial project structure
- Core models (BlogPost, PostResult)
- SEO analyzer foundation

## 2026-01-15

### Added
- Initial project structure
- Core models (BlogPost, PostResult)
- SEO analyzer foundation