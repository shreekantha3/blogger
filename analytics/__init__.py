"""
Analytics module for GSC, GA4, and content performance data.

ARCHITECTURAL DECISION: Analytics Layer
--------------------------------------
This module provides the feedback loop missing from Phase 1-5:
- GSC integration for search performance data
- GA4 integration for user engagement metrics
- Content audit for detecting decaying/stale posts
- Rank tracking for SERP position monitoring

Without this layer, the platform generates content but cannot:
- Measure what works
- Identify decaying traffic
- Make data-driven decisions
- Close the optimization loop
"""

from analytics.models import (
    QueryData,
    PageData,
    IndexingResult,
    AuditReport,
    DecayingPost,
    StalePost,
    OrphanPage,
)
from analytics.gsc_client import GSCClient
from analytics.ga4_client import GA4Client

__all__ = [
    "QueryData",
    "PageData",
    "IndexingResult",
    "AuditReport",
    "DecayingPost",
    "StalePost",
    "OrphanPage",
    "GSCClient",
    "GA4Client",
]