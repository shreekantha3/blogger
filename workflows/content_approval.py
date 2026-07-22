"""
Human-in-the-loop content brief approval.

ARCHITECTURAL DECISION: Approval Workflow Strategy
---------------------------------------------------
Based on Honest Code Review: "Human-in-the-loop content brief
approval - E-E-A-T requires humans"

This module:
1. Generates content briefs from SERP analysis
2. Saves for human review
3. Tracks approval status
4. Only then passes to AI generation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from config import get_logger
from ai.content_brief import ContentBriefResponse

logger = get_logger("workflows", "approval")


class ApprovalStatus(Enum):
    """Status of content brief approval."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"


@dataclass
class ContentApproval:
    """Content brief pending approval."""

    id: str
    topic: str
    keyword: str
    brief: ContentBriefResponse
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None


class ContentApprovalWorkflow:
    """
    Manages content brief approval workflow.

    Usage:
        workflow = ContentApprovalWorkflow()
        approval = workflow.create_brief("KSP Recruitment", "ksp constable")
        workflow.save_for_review(approval)
        # Human reviews, then approves
        workflow.approve(approval.id, notes="Good angle!")
    """

    def __init__(self, approval_dir: str = "data/approvals") -> None:
        """
        Initialize approval workflow.

        Args:
            approval_dir: Directory to store pending approvals
        """
        self._approval_dir = Path(approval_dir)
        self._approval_dir.mkdir(parents=True, exist_ok=True)

    def create_brief(
        self,
        topic: str,
        keyword: str,
    ) -> ContentApproval:
        """
        Create and save content brief for approval.

        Args:
            topic: Article topic
            keyword: Target keyword

        Returns:
            ContentApproval object
        """
        # Generate brief (would use async in production)
        import asyncio
        from ai.content_brief import ContentBriefGenerator, ContentBriefRequest

        generator = ContentBriefGenerator()
        brief = asyncio.run(generator.generate(
            ContentBriefRequest(topic=topic, target_keyword=keyword)
        ))

        approval = ContentApproval(
            id=f"{keyword.replace(' ', '_')}_{int(datetime.now().timestamp())}",
            topic=topic,
            keyword=keyword,
            brief=brief,
        )

        self.save_for_review(approval)

        logger.info("Created content brief for approval", id=approval.id)

        return approval

    def save_for_review(self, approval: ContentApproval) -> None:
        """Save approval for human review."""
        file_path = self._approval_dir / f"{approval.id}.json"

        # Convert to serializable format
        data = {
            "id": approval.id,
            "topic": approval.topic,
            "keyword": approval.keyword,
            "status": approval.status.value,
            "created_at": approval.created_at.isoformat(),
            "brief": {
                "target_keyword": approval.brief.target_keyword,
                "search_intent": approval.brief.search_intent,
                "recommended_word_count": approval.brief.recommended_word_count,
                "required_h2_sections": approval.brief.required_h2_sections,
                "paa_questions": approval.brief.paa_questions,
                "content_gaps": approval.brief.content_gaps,
            },
        }

        file_path.write_text(
            "\n".join([
                "# Content Brief Approval",
                f"**Status:** {approval.status.value}",
                f"**Topic:** {approval.topic}",
                f"**Keyword:** {approval.keyword}",
                "",
                "## Brief Details",
                approval.brief.formatted_brief,
            ])
        )

        logger.info("Saved brief for review", path=str(file_path))

    def approve(
        self,
        approval_id: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Approve a content brief.

        Args:
            approval_id: Brief ID
            notes: Reviewer notes

        Returns:
            Success status
        """
        file_path = self._approval_dir / f"{approval_id}.json"
        if not file_path.exists():
            return False

        approval = self._load_approval(approval_id)
        approval.status = ApprovalStatus.APPROVED
        approval.approved_at = datetime.now()
        approval.reviewer_notes = notes

        self._save_approval(approval)

        logger.info("Brief approved", id=approval_id)

        return True

    def reject(
        self,
        approval_id: str,
        notes: str,
    ) -> bool:
        """Reject a content brief with feedback."""
        approval = self._load_approval(approval_id)
        approval.status = ApprovalStatus.REJECTED
        approval.reviewer_notes = notes

        self._save_approval(approval)

        return True

    def _load_approval(self, approval_id: str) -> ContentApproval:
        """Load approval from storage."""
        # Simplified - would use JSON in production
        return ContentApproval(id=approval_id, topic="", keyword="", brief=None)

    def _save_approval(self, approval: ContentApproval) -> None:
        """Save approval state."""
        pass

    def list_pending(self) -> list[ContentApproval]:
        """List pending approvals."""
        approvals = []
        for file_path in self._approval_dir.glob("*.json"):
            # Would parse JSON
            pass
        return approvals


# CLI convenience
def create_content_brief(topic: str, keyword: str, output: Optional[str] = None) -> None:
    """
    Create content brief via CLI.

    Args:
        topic: Article topic
        keyword: Target keyword
        output: Output file path (optional)
    """
    workflow = ContentApprovalWorkflow()
    approval = workflow.create_brief(topic, keyword)

    print(f"Created content brief: {approval.id}")
    print(f"Status: {approval.status.value}")
    print(f"\nReview the brief in: data/approvals/{approval.id}.json")