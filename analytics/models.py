"""
Data models for analytics module.

ARCHITECTURAL DECISION: Dataclasses for Analytics Data
------------------------------------------------------
Using dataclasses for clean, typed data structures that:
- Are serializable for caching/testing
- Provide type hints for IDE support
- Contain validation logic in __post_init__
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QueryData:
    """Search Console query performance data."""

    query: str
    clicks: int
    impressions: int
    ctr: float  # Click-through rate (0.0-1.0)
    position: float  # Average position
    days: int = 90  # Days of data

    def __post_init__(self) -> None:
        """Validate data on initialization."""
        if not 0 <= self.ctr <= 1:
            raise ValueError(f"CTR must be between 0 and 1, got {self.ctr}")
        if self.position < 1:
            raise ValueError(f"Position must be >= 1, got {self.position}")


@dataclass
class PageData:
    """Page performance data from GSC/GA4."""

    url: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    avg_position: float = 0.0
    sessions: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0  # seconds
    last_updated: Optional[datetime] = None

    # Traffic trend (percent change)
    pct_change_30d: Optional[float] = None
    pct_change_90d: Optional[float] = None

    # Top queries for this page
    top_queries: list[QueryData] = field(default_factory=list)


@dataclass
class IndexingResult:
    """Result of URL indexing submission."""

    successful: list[str]
    failed: list[str]
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = len(self.successful) + len(self.failed)
        if total == 0:
            return 0.0
        return len(self.successful) / total


@dataclass
class DecayingPost:
    """Post with declining traffic that needs refresh."""

    url: str
    post_id: str
    title: str
    traffic_drop_pct: float  # Percentage drop in clicks
    impression_drop_pct: float = 0.0
    position_change: float = 0.0  # Positive = dropped in rankings
    days_since_publish: int = 0
    last_updated: Optional[datetime] = None
    suggested_action: str = "refresh"  # refresh, update, or republish


@dataclass
class StalePost:
    """Post that hasn't been updated in a long time."""

    url: str
    post_id: str
    title: str
    days_since_update: int
    days_since_publish: int
    needs_update: bool = True
    suggested_sections: list[str] = field(default_factory=list)


@dataclass
class OrphanPage:
    """Page with no internal links pointing to it."""

    url: str
    post_id: str
    title: str
    inbound_links: int = 0  # Should be 0 for true orphans
    suggested_parent_pages: list[str] = field(default_factory=list)


@dataclass
class AuditReport:
    """Weekly audit report combining all findings."""

    generated_at: datetime
    priority_updates: list[DecayingPost] = field(default_factory=list)
    refresh_candidates: list[StalePost] = field(default_factory=list)
    link_opportunities: list[OrphanPage] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        """Total number of issues found."""
        return (
            len(self.priority_updates)
            + len(self.refresh_candidates)
            + len(self.link_opportunities)
        )

    def to_markdown(self) -> str:
        """Generate markdown report for easy reading."""
        lines = [
            f"# Content Audit Report - {self.generated_at.strftime('%Y-%m-%d')}",
            "",
            f"## Priority Updates ({len(self.priority_updates)})",
            "",
        ]

        for post in self.priority_updates[:10]:
            lines.extend([
                f"### {post.title}",
                f"- **Traffic Drop:** {post.traffic_drop_pct:.1f}%",
                f"- **Position Change:** {post.position_change:+.1f}",
                f"- **Action:** {post.suggested_action}",
                "",
            ])

        lines.extend([
            f"## Refresh Candidates ({len(self.refresh_candidates)})",
            "",
        ])

        for post in self.refresh_candidates[:10]:
            lines.extend([
                f"### {post.title}",
                f"- **Days Since Update:** {post.days_since_update}",
                f"- **Suggested Sections:** {', '.join(post.suggested_sections[:3])}",
                "",
            ])

        return "\n".join(lines)