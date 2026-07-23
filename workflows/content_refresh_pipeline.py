"""
Content Refresh Pipeline - automates the highest ROI SEO activity.

ARCHITECTURAL DECISION: Refresh Pipeline Strategy
-------------------------------------------------
Based on Honest Code Review: "refresh > new - Highest ROI SEO activity"

This pipeline:
1. Identifies decaying posts (via GSC)
2. Generates update briefs
3. Suggests improvements
4. Tracks refresh events

Addresses: "Your recruitment articles from July will be stale by January.
No system catches this."
"""

from datetime import datetime
from typing import Optional

from config import get_logger
from core.events import get_publisher, EventType, DomainEvent
from analytics.content_audit import ContentAuditor, run_audit
from ai.content_brief import ContentBriefGenerator, ContentBriefRequest

logger = get_logger("workflows", "refresh")


class ContentRefreshPipeline:
    """
    Automated content refresh workflow.

    Usage:
        pipeline = ContentRefreshPipeline()
        report = pipeline.run_weekly_refresh_audit()
        for post in report.priority_updates[:3]:
            brief = pipeline.generate_refresh_brief(post.url)
    """

    def __init__(self) -> None:
        """Initialize refresh pipeline."""
        self._publisher = get_publisher()
        self._auditor = ContentAuditor()

    def run_weekly_refresh_audit(
        self,
        traffic_drop_threshold: float = 20.0,
    ) -> None:
        """
        Run weekly content audit and emit events for declining posts.

        Args:
            traffic_drop_threshold: % drop to flag as priority
        """
        audit = run_audit(traffic_drop_threshold=traffic_drop_threshold)

        # Emit events for each declining post
        for post in audit.priority_updates:
            event = self._publisher.publish(
                EventType.RANK_DROPPED,
                {
                    "post_id": post.post_id,
                    "url": post.url,
                    "traffic_drop_pct": post.traffic_drop_pct,
                    "action": post.suggested_action,
                },
            )

            logger.info(
                "Identified declining post",
                url=post.url,
                drop=post.traffic_drop_pct,
            )

        # Emit events for stale content
        for post in audit.refresh_candidates:
            self._publisher.publish(
                EventType.CONTENT_STALE,
                {
                    "post_id": post.post_id,
                    "url": post.url,
                    "days_since_update": post.days_since_update,
                    "suggested_sections": post.suggested_sections,
                },
            )

        logger.info(
            "Weekly refresh audit complete",
            declining=len(audit.priority_updates),
            stale=len(audit.refresh_candidates),
        )

        return audit

    async def generate_refresh_brief(
        self,
        url: str,
        add_serp_insights: bool = True,
    ) -> dict:
        """
        Generate an update brief for a post.

        Args:
            url: Post URL to refresh
            add_serp_insights: Include SERP analysis

        Returns:
            ContentBrief for the update
        """
        # Extract topic from URL for SERP analysis
        topic = url.split("/")[-1].replace("-", " ").title()

        brief = await ContentBriefGenerator().generate(
            ContentBriefRequest(
                topic=topic,
                target_keyword=topic,
                language="en",
            )
        )

        logger.info("Generated refresh brief", url=url)

        return {
            "topic": topic,
            "keywords_to_add": brief.secondary_keywords[:5],
            "sections_to_expand": brief.required_h2_sections[:3],
            "paa_questions": brief.paa_questions[:5],
            "content_gaps": brief.content_gaps,
        }


# Convenience function for CLI
def run_refresh_audit(threshold: float = 20.0):
    """
    Run refresh audit from CLI.

    Args:
        threshold: Traffic drop % for flagging
    """
    pipeline = ContentRefreshPipeline()
    audit = pipeline.run_weekly_refresh_audit(threshold)

    print(f"# Content Refresh Audit - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"\nFound {audit.total_issues} issues to address:")

    print(f"\n## Priority Updates ({len(audit.priority_updates)})")
    for post in audit.priority_updates:
        print(f"  - {post.title}: {post.traffic_drop_pct:.1f}% traffic drop")

    print(f"\n## Staleness Candidates ({len(audit.refresh_candidates)})")
    for post in audit.refresh_candidates[:5]:
        print(f"  - {post.title}: {post.days_since_update} days since update")