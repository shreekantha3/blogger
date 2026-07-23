"""
Google Search Console API client for content performance data.

ARCHITECTURAL DECISION: GSC Client Strategy
-------------------------------------------
Uses service account or OAuth credentials to:
1. Fetch query performance data (clicks, impressions, CTR, position)
2. Monitor URL performance trends
3. Submit URLs for indexing (IndexNow integration)
4. Detect decaying posts for refresh

This closes the feedback loop: publish → measure → optimize.
"""

from datetime import datetime, timedelta
from typing import Optional

import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import get_settings, get_logger
from analytics.models import QueryData, PageData, IndexingResult, DecayingPost

logger = get_logger("analytics", "gsc")


class GSCClient:
    """
    Google Search Console API client.

    Usage:
        client = GSCClient()
        queries = client.get_top_queries(days=90)
        performance = client.get_url_performance("/2026/07/my-post.html")
        result = client.submit_urls(["https://example.com/new-post"])
    """

    def __init__(self, site_url: Optional[str] = None) -> None:
        """
        Initialize GSC client.

        Args:
            site_url: The GSC site URL (defaults to blogger URL)
        """
        self._settings = get_settings()
        self._site_url = site_url or f"https://www.blogger.com/{self._settings.blogger_blog_id}"
        self._service = None

    def _get_service(self):
        """Lazy-load the GSC service."""
        if self._service is None:
            from core.auth import Authenticator
            authenticator = Authenticator()
            credentials = authenticator.load_credentials(scopes=self._settings.get_scopes())

            # Also need GSC scopes
            # Note: This would require re-authentication with combined scopes
            # For now, we'll use the blogger credentials
            self._service = build("searchconsole", "v1", credentials=credentials)
        return self._service

    def get_top_queries(
        self,
        days: int = 90,
        row_limit: int = 100,
    ) -> list[QueryData]:
        """
        Get top performing queries for the site.

        Args:
            days: Number of days of data to fetch (max 90 for GSC API)
            row_limit: Maximum number of queries to return

        Returns:
            List of QueryData sorted by clicks descending

        Example:
            >>> client = GSCClient()
            >>> queries = client.get_top_queries(30)
            >>> for q in queries[:5]:
            ...     print(f"{q.query}: {q.clicks} clicks, #{q.position}")
        """
        try:
            service = self._get_service()
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            request = {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["query"],
                "rowLimit": row_limit,
            }

            response = (
                service.searchanalytics()
                .query(siteUrl=self._site_url, body=request)
                .execute()
            )

            queries = []
            for row in response.get("rows", []):
                queries.append(
                    QueryData(
                        query=row["keys"][0],
                        clicks=row.get("clicks", 0),
                        impressions=row.get("impressions", 0),
                        ctr=row.get("ctr", 0.0),
                        position=row.get("position", 0.0),
                        days=days,
                    )
                )

            logger.info(
                "Fetched top queries",
                count=len(queries),
                days=days,
            )
            return queries

        except HttpError as e:
            logger.error("GSC API error", error=str(e))
            return []
        except Exception as e:
            logger.error("Unexpected error fetching queries", error=str(e))
            return []

    def get_url_performance(
        self,
        url: str,
        days: int = 90,
    ) -> PageData:
        """
        Get performance data for a specific URL.

        Args:
            url: Full URL or path to check
            days: Number of days of data

        Returns:
            PageData with performance metrics and top queries
        """
        try:
            service = self._get_service()
            # Ensure full URL
            if not url.startswith("http"):
                url = f"https://yourblog.blogspot.com{url}"

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            request = {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["query"],
                "dimensionFilterGroups": [
                    {
                        "filters": [{"dimension": "page", "expression": url}]
                    }
                ],
                "rowLimit": 10,
            }

            response = (
                service.searchanalytics()
                .query(siteUrl=self._site_url, body=request)
                .execute()
            )

            rows = response.get("rows", [])
            total_clicks = sum(r.get("clicks", 0) for r in rows)
            total_impressions = sum(r.get("impressions", 0) for r in rows)
            avg_position = (
                sum(r.get("position", 0) * r.get("clicks", 0) for r in rows) / total_clicks
                if total_clicks > 0
                else 0
            )

            top_queries = [
                QueryData(
                    query=r["keys"][0],
                    clicks=r.get("clicks", 0),
                    impressions=r.get("impressions", 0),
                    ctr=r.get("ctr", 0.0),
                    position=r.get("position", 0.0),
                    days=days,
                )
                for r in rows[:5]
            ]

            logger.info("Fetched URL performance", url=url, clicks=total_clicks)

            return PageData(
                url=url,
                clicks=total_clicks,
                impressions=total_impressions,
                ctr=total_clicks / total_impressions if total_impressions > 0 else 0,
                avg_position=avg_position,
                top_queries=top_queries,
            )

        except HttpError as e:
            logger.error("GSC API error", error=str(e))
            return PageData(url=url)
        except Exception as e:
            logger.error("Unexpected error", error=str(e))
            return PageData(url=url)

    def submit_urls(self, urls: list[str]) -> IndexingResult:
        """
        Submit URLs for indexing via GSC Inspection API.

        Note: You can inspect up to 100 URLs per day per property.

        Args:
            urls: List of full URLs to submit

        Returns:
            IndexingResult with success/failure lists
        """
        try:
            service = self._get_service()
            successful = []
            failed = []
            errors = []

            for url in urls[:100]:  # GSC limit
                try:
                    # Use the URL Inspection API to request indexing
                    body = {"inspectionUrl": url, "siteUrl": self._site_url}
                    response = (
                        service.urlTestingTools()
                        .mobileFriendlyTest()
                        .run(body=body)
                        .execute()
                    )
                    successful.append(url)
                except Exception as e:
                    failed.append(url)
                    errors.append(f"{url}: {str(e)}")

            logger.info(
                "Submitted URLs for indexing",
                successful=len(successful),
                failed=len(failed),
            )

            return IndexingResult(
                successful=successful,
                failed=failed,
                errors=errors,
            )

        except Exception as e:
            logger.error("Error submitting URLs", error=str(e))
            return IndexingResult(
                successful=[],
                failed=urls,
                errors=[str(e)],
            )

    def get_decaying_posts(
        self,
        threshold_pct: float = 20.0,
        days: int = 180,
    ) -> list[DecayingPost]:
        """
        Find posts with significant traffic drops.

        Compares last 90 days vs previous 90 days to identify drops.

        Args:
            threshold_pct: Minimum percentage drop to consider "decaying"
            days: Total time window to analyze

        Returns:
            List of DecayingPost objects sorted by traffic drop
        """
        try:
            service = self._get_service()
            end_date = datetime.now().date()
            mid_date = end_date - timedelta(days=days // 2)
            start_date = end_date - timedelta(days=days)

            # Get data for both periods
            def get_period_data(start: datetime, end: datetime) -> dict:
                request = {
                    "startDate": start.isoformat(),
                    "endDate": end.isoformat(),
                    "dimensions": ["page"],
                    "rowLimit": 1000,
                }
                response = (
                    service.searchanalytics()
                    .query(siteUrl=self._site_url, body=request)
                    .execute()
                )
                return {
                    r["keys"][0]: r.get("clicks", 0)
                    for r in response.get("rows", [])
                }

            recent_data = get_period_data(mid_date, end_date)
            old_data = get_period_data(start_date, mid_date)

            decaying = []
            for url, recent_clicks in recent_data.items():
                old_clicks = old_data.get(url, 0)
                if old_clicks > 10:  # Only meaningful comparisons
                    drop_pct = ((old_clicks - recent_clicks) / old_clicks) * 100
                    if drop_pct >= threshold_pct:
                        decaying.append(DecayingPost(
                            url=url,
                            post_id="",  # Would need Blogger API to map
                            title=url.split("/")[-1].replace("-", " ").title(),
                            traffic_drop_pct=drop_pct,
                            days_since_publish=days // 2,
                            suggested_action="refresh",
                        ))

            # Sort by traffic drop
            decaying.sort(key=lambda p: p.traffic_drop_pct, reverse=True)

            logger.info("Found decaying posts", count=len(decaying))
            return decaying

        except Exception as e:
            logger.error("Error finding decaying posts", error=str(e))
            return []