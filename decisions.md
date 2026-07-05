# Architecture Decision Records (ADRs)

## Decision #1: Authentication Library

**Rejected:**
- `oauth2client` - deprecated since 2018

**Chosen:**
- `google-auth`

**Reason:**
- `oauth2client` is deprecated
- Future compatibility with Google APIs
- Automatic token refresh support
- Official Google-maintained library
- Better error handling and logging integration

**Date:** 2026-06-30