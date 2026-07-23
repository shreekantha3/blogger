"""
Content audit for detecting decaying, stale, and orphaned posts.

ARCHITECTURAL DECISION: Content Audit Strategy
-----------------------------------------------
Based on the Honest Code Review finding that "refresh > new" for SEO ROI.

This module:
1. Identifies posts with declining traffic (GSC data)
2. Finds stale content that hasn't been updated
3. Detects orphan pages with no internal links
4. Generates actionable refresh suggestions
"""

from datetime import datetime, timedelta
from typing import Optional

from config import get_settings, get_logger
from analytics.models import (
    DecayingPost,
    StalePost,
    OrphanPage,
    AuditReport,
)
from analytics.gsc_client import GSCClient
from core.blogger_client import BloggerClient

logger = get_logger("analytics", "audit")


class ContentAuditor:
    """
    Audit blog content for performance and quality issues.

    Usage:
        auditor = ContentAuditor()
        report = await auditor.run_weekly_audit()
        print(report.to_markdown())
    """

    def __init__(self) -> None:
        """Initialize auditor with necessary clients."""
        self._settings = get_settings()
        self._gsc = GSCClient()
        self._blogger = BloggerClient()

    def run_weekly_audit(
        self,
        traffic_drop_threshold: float = 20.0,
        stale_days: int = 365,
    ) -> AuditReport:
        """
        Run a comprehensive content audit.

        Args:
            traffic_drop_threshold: % drop to flag as decaying
            stale_days: Days since update to flag as stale

        Returns:
            AuditReport with all findings
        """
        now = datetime.now()

        # Find decaying posts
        decaying = self._find_decaying_posts(traffic_drop_threshold)

        # Find stale content
        stale = self._find_stale_content(stale_days)

        # Find orphan pages
        orphan = self._find_orphan_pages()

        report = AuditReport(
            generated_at=now,
            priority_updates=decaying,
            refresh_candidates=stale,
            link_opportunities=orphan,
        )

        logger.info(
            "Weekly audit complete",
            decaying=len(decaying),
            stale=len(stale),
            orphan=len(orphan),
        )

        return report

    def _find_decaying_posts(
        self,
        threshold_pct: float,
    ) -> list[DecayingPost]:
        """
        Find posts with significant traffic declines.

        Compares 90-day performance to detect drops.
        """
        decaying = []

        # Get posts from Blogger
        posts = self._blogger.list_posts()

        for post in posts:
            if not post.get("url"):
                continue

            # Get GSC performance
            perf = self._gsc.get_url_performance(post["url"], days=180)

            # Check for significant drop (would need historical data comparison)
            if perf.pct_change_90d and perf.pct_change_90d <= -threshold_pct:
                decaying.append(DecayingPost(
                    url=post["url"],
                    post_id=post.get("id", ""),
                    title=post.get("title", ""),
                    traffic_drop_pct=abs(perf.pct_change_90d),
                    days_since_publish=self._days_since(
                        post.get("published", datetime.now())
                    ),
                    suggested_action=self._suggest_refresh_action(perf),
                ))

        # Also use GSC's built-in detection
        gsc_decaying = self._gsc.get_decaying_posts(threshold_pct, days=180)
        decaying.extend(gsc_decaying)

        return decaying[:20]  # Top 20 priority

    def _find_stale_content(self, days_threshold: int) -> list[StalePost]:
        """
        Find content that hasn't been updated in a long time.

        These are candidates for refresh with new information.
        """
        stale = []
        posts = self._blogger.list_posts()

        cutoff = datetime.now() - timedelta(days=days_threshold)

        for post in posts:
            updated_str = post.get("updated")
            if updated_str:
                try:
                    updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
            else:
                updated = None

            if updated and updated < cutoff:
                days_since = (datetime.now() - updated).days

                stale.append(StalePost(
                    url=post.get("url", ""),
                    post_id=post.get("id", ""),
                    title=post.get("title", ""),
                    days_since_update=days_since,
                    days_since_publish=self._days_since(
                        post.get("published", datetime.now())
                    ),
                    suggested_sections=self._suggest_update_sections(
                        post.get("title", "")
                    ),
                ))

        return stale[:30]

    def _find_orphan_pages(self) -> list[OrphanPage]:
        """
        Find pages with no internal links pointing to them.

        These lose authority and don't rank well.
        """
        orphan = []
        posts = self._blogger.list_posts()

        for post in posts:
            post_id = post.get("id", "")
            if not post_id:
                continue

            # Check for inbound links (would need to scan all posts)
            inbound = self._count_inbound_links(post_id, post.get("url", ""))

            if inbound == 0:
                orphan.append(OrphanPage(
                    url=post.get("url", ""),
                    post_id=post_id,
                    title=post.get("title", ""),
                    inbound_links=0,
                    suggested_parent_pages=self._suggest_parent_pages(
                        post.get("title", "")
                    ),
                ))

        return orphan[:20]

    def _count_inbound_links(
        self,
        post_id: str,
        url: str,
    ) -> int:
        """Count internal links pointing to a post."""
        count = 0
        posts = self._blogger.list_posts()

        for other in posts:
            if other.get("id") == post_id:
                continue

            content = other.get("content", "")
            if url in content or post_id in content:
                count += content.count(url) + content.count(post_id)

        return count

    def _suggest_refresh_action(self, perf: any) -> str:
        """Suggest refresh action based on performance data."""
        if perf.avg_position > 10:
            return "rewrite"
        if perf.top_queries and len(perf.top_queries) < 5:
            return "expand_keywords"
        return "refresh"

    def _suggest_update_sections(self, title: str) -> list[str]:
        """Suggest sections to add for refresh."""
        suggestions = []

        # For recruitment articles, always suggest:
        if "recruitment" in title.lower():
            suggestions.extend([
                "Latest Updates",
                "Updated Syllabus",
                "New Application Process",
                "Current Salary Structure",
            ])

        return suggestions

    def _suggest_parent_pages(self, title: str) -> list[str]:
        """Suggest which existing pages could link to this orphan."""
        # Would be smarter with topic clustering
        return ["sitemap.html", "index.html", "category-page.html"]

    def _days_since(self, date: any) -> int:
        """Calculate days since a date."""
        if isinstance(date, datetime):
            return (datetime.now() - date).days
        if isinstance(date, str):
            try:
                return (datetime.now() - datetime.fromisoformat(date)).days
            except (ValueError, TypeError):
                return 0
        return 0


# Convenience function for CLI
def run_audit(
    traffic_drop_threshold: float = 20.0,
    stale_days: int = 365,
) -> AuditReport:
    """
    Run content audit and return report.

    This is the main entry point for the analytics-audit CLI command.

    Args:
        traffic_drop_threshold: Traffic decline % to flag
        stale_days: Days since update to flag as stale

    Returns:
        AuditReport with findings
    """
    auditor = ContentAuditor()
    return auditor.run_weekly_audit(
        traffic_drop_threshold=traffic_drop_threshold,
        stale_days=stale_days,
    )