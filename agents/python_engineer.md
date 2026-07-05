# Agent: Python Engineer

## Responsibilities
- Python best practices
- Performance optimization
- Error handling patterns
- Refactoring for maintainability
- Type hints and static analysis

## Current Code Quality
- Type hints: Good coverage with `typing_extensions`
- Error handling: Uses custom exceptions (AIServiceError, AIContentError)
- Logging: Structured logging with structlog
- Performance: LRU cache for settings

## Known Issues
1. Free model output includes reasoning text - needs sanitization
2. JSON parsing for FAQ/keywords fails on malformed output
3. Large max_tokens (10000) may cause memory issues

## Recommendations
- Add `mypy` for type checking
- Add `pydantic` validation on API responses
- Implement circuit breaker for AI API calls
- Add retry logic for idempotent AI operations