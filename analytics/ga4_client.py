"""
Google Analytics 4 client for user engagement metrics.

ARCHITECTURAL DECISION: GA4 Measurement Protocol
-----------------------------------------------
Uses GA4 API to:
1. Fetch user engagement metrics (sessions, bounce rate, duration)
2. Track content performance beyond just SEO
3. Support content audit decisions with engagement data

GA4 complements GSC by showing user behavior, not just search visibility.
"""

from datetime import datetime, timedelta
from typing import Optional

import httpx
try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
    )
    GA4_AVAILABLE = True
except ImportError:
    GA4_AVAILABLE = False

from config import get_settings, get_logger
from analytics.models import PageData

logger = get_logger("analytics", "ga4")


class GA4Client:
    """
    Google Analytics 4 API client.

    Usage:
        client = GA4Client()
        data = client.get_page_metrics("/2026/07/my-post.html")
        print(f"Sessions: {data.sessions}, Bounce: {data.bounce_rate}")
    """

    def __init__(self, property_id: Optional[str] = None) -> None:
        """
        Initialize GA4 client.

        Args:
            property_id: GA4 property ID (defaults from settings)
        """
        self._settings = get_settings()
        # Property ID format: GA4-XXXXXXXXX
        self._property_id = property_id or "GA4-BLOG-PROPERTY"

    def get_page_metrics(
        self,
        path: str,
        days: int = 90,
    ) -> PageData:
        """
        Get engagement metrics for a specific page.

        Args:
            path: Page path (e.g., "/2026/07/my-post.html")
            days: Number of days of data

        Returns:
            PageData with GA4 engagement metrics
        """
        if not GA4_AVAILABLE:
            logger.warning("google-analytics-data not installed")
            return PageData(url=path)

        try:
            client = BetaAnalyticsDataClient()

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            request = RunReportRequest(
                property=f"properties/{self._property_id}",
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="screenPageViews"),
                ],
                date_ranges=[DateRange(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )],
            )

            response = client.run_report(request)

            # Find matching row
            for row in response.rows:
                if path in row.dimension_values[0].value:
                    page_path = row.dimension_values[0].value
                    sessions = int(row.metric_values[0].value)
                    bounce_rate = float(row.metric_values[1].value)
                    avg_duration = float(row.metric_values[2].value)

                    logger.info("Fetched GA4 metrics", path=path, sessions=sessions)

                    return PageData(
                        url=page_path,
                        sessions=sessions,
                        bounce_rate=bounce_rate,
                        avg_session_duration=avg_duration,
                    )

            # No data found
            return PageData(url=path)

        except Exception as e:
            logger.error("Error fetching GA4 metrics", error=str(e))
            return PageData(url=path)

    def get_top_pages(
        self,
        days: int = 30,
        limit: int = 100,
    ) -> list[PageData]:
        """
        Get top performing pages by sessions.

        Args:
            days: Number of days of data
            limit: Maximum number of pages

        Returns:
            List of PageData sorted by sessions descending
        """
        if not GA4_AVAILABLE:
            logger.warning("google-analytics-data not installed")
            return []

        try:
            client = BetaAnalyticsDataClient()

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            request = RunReportRequest(
                property=f"properties/{self._property_id}",
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                ],
                date_ranges=[DateRange(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )],
                limit=limit,
                order_bys=[{"metric_name": "sessions", "desc": True}],
            )

            response = client.run_report(request)

            pages = []
            for row in response.rows:
                pages.append(PageData(
                    url=row.dimension_values[0].value,
                    sessions=int(row.metric_values[0].value),
                    bounce_rate=float(row.metric_values[1].value),
                    avg_session_duration=float(row.metric_values[2].value),
                ))

            logger.info("Fetched top pages", count=len(pages))
            return pages

        except Exception as e:
            logger.error("Error fetching top pages", error=str(e))
            return []