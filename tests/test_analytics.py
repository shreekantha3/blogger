"""Tests for analytics module (GSC, GA4, content audit)."""

import pytest
from datetime import datetime

from analytics.models import (
    QueryData,
    PageData,
    IndexingResult,
    AuditReport,
    DecayingPost,
    StalePost,
    OrphanPage,
)


class TestQueryData:
    """Test QueryData model."""

    def test_valid_query_data(self):
        """Verify valid query data creation."""
        q = QueryData(
            query="python tutorial",
            clicks=1000,
            impressions=10000,
            ctr=0.1,
            position=5.0,
        )
        assert q.query == "python tutorial"
        assert q.clicks == 1000

    def test_ctr_validation(self):
        """Verify CTR must be between 0 and 1."""
        with pytest.raises(ValueError):
            QueryData(
                query="test",
                clicks=100,
                impressions=1000,
                ctr=1.5,  # Invalid - over 1.0
                position=1.0,
            )

    def test_position_validation(self):
        """Verify position must be >= 1."""
        with pytest.raises(ValueError):
            QueryData(
                query="test",
                clicks=100,
                impressions=1000,
                ctr=0.1,
                position=0.0,  # Invalid - below 1
            )


class TestPageData:
    """Test PageData model."""

    def test_empty_page_data(self):
        """Verify empty page data works."""
        p = PageData(url="https://example.com")
        assert p.url == "https://example.com"
        assert p.clicks == 0

    def test_page_data_with_metrics(self):
        """Verify page data with all metrics."""
        p = PageData(
            url="https://example.com",
            clicks=500,
            impressions=5000,
            ctr=0.1,
            avg_position=8.5,
            sessions=600,
            bounce_rate=0.45,
            avg_session_duration=180.0,
        )
        assert p.sessions == 600
        assert p.bounce_rate == 0.45

    def test_pct_change_calculated(self):
        """Verify percentage changes are tracked."""
        p = PageData(
            url="https://example.com",
            pct_change_30d=-15.5,
            pct_change_90d=-35.2,
        )
        assert p.pct_change_30d == -15.5


class TestIndexingResult:
    """Test IndexingResult model."""

    def test_success_rate(self):
        """Verify success rate calculation."""
        r = IndexingResult(
            successful=["url1", "url2", "url3"],
            failed=["url4"],
            errors=[],
        )
        assert r.success_rate == 0.75

    def test_edge_case_zero_total(self):
        """Verify zero division handling."""
        r = IndexingResult(successful=[], failed=[])
        assert r.success_rate == 0.0


class TestDecayingPost:
    """Test DecayingPost model."""

    def test_decaying_post_creation(self):
        """Verify decaying post model."""
        p = DecayingPost(
            url="https://example.com/post",
            post_id="123",
            title="Decaying Post",
            traffic_drop_pct=45.0,
            suggested_action="refresh",
        )
        assert p.traffic_drop_pct == 45.0

    def test_suggested_action_default(self):
        """Verify default action is refresh."""
        p = DecayingPost(
            url="https://example.com",
            post_id="",
            title="Test",
            traffic_drop_pct=25.0,
        )
        assert p.suggested_action == "refresh"


class TestAuditReport:
    """Test AuditReport model."""

    def test_empty_report(self):
        """Verify empty audit report."""
        r = AuditReport(generated_at=datetime.now())
        assert r.total_issues == 0

    def test_report_with_findings(self):
        """Verify report counts findings correctly."""
        r = AuditReport(
            generated_at=datetime.now(),
            priority_updates=[
                DecayingPost(url="u1", post_id="1", title="Decaying", traffic_drop_pct=20.0)
            ],
            refresh_candidates=[
                StalePost(url="u2", post_id="2", title="Stale", days_since_update=400, days_since_publish=400)
            ],
            link_opportunities=[
                OrphanPage(url="u3", post_id="3", title="Orphan")
            ],
        )
        assert r.total_issues == 3

    def test_markdown_report(self):
        """Verify markdown formatting works."""
        r = AuditReport(
            generated_at=datetime(2026, 7, 22),
            priority_updates=[
                DecayingPost(
                    url="https://example.com/post",
                    post_id="123",
                    title="Recruitment Post",
                    traffic_drop_pct=35.0,
                )
            ],
            refresh_candidates=[],
            link_opportunities=[],
        )

        md = r.to_markdown()
        assert "# Content Audit Report" in md
        assert "35.0" in md
        assert "Recruitment Post" in md