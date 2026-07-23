"""
Event-driven architecture for workflow tracing.

ARCHITECTURAL DECISION: Event-Driven Architecture
-------------------------------------------------
Based on Honest Code Review recommendation to decouple and trace workflows.

This module provides:
1. Domain events for all major operations (publish, update, delete)
2. Correlation IDs to trace full workflow
3. Event publisher for loose coupling
4. Ready for future event bus/sink integration

Enables:
- Publish → SEO → Schema → Index (traced sequence)
- Identify → Refresh → Re-publish (refresh pipeline)
- Analyze → Suggest → Apply (link building pipeline)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid

from config import get_logger

logger = get_logger("core", "events")


class EventType(Enum):
    """Types of domain events."""

    # Publishing events
    POST_PUBLISHED = "post.published"
    POST_UPDATED = "post.updated"
    POST_DELETED = "post.deleted"
    POST_SCHEDULED = "post.scheduled"

    # SEO events
    SEO_ANALYZED = "seo.analyzed"
    SEO_SCORE_UPDATED = "seo.score_updated"

    # Analytics events
    TRAFFIC_SPIKE = "traffic.spike"
    RANK_DROPPED = "rank.dropped"
    CONTENT_STALE = "content.stale"

    # AI events
    CONTENT_GENERATED = "content.generated"
    CONTENT_BRIEF_CREATED = "content.brief_created"
    KEYWORDS_EXTRACTED = "keywords.extracted"


@dataclass
class DomainEvent:
    """A domain event that tracks platform operations."""

    type: EventType
    payload: dict
    timestamp: datetime
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DomainEvent":
        """Create event from dictionary."""
        return cls(
            type=EventType(data["type"]),
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data["correlation_id"],
        )


class EventPublisher:
    """
    Publish and track domain events.

    Usage:
        publisher = EventPublisher()
        event = publisher.publish(
            EventType.POST_PUBLISHED,
            {"post_id": "123", "url": "..."},
            correlation_id="abc-123"
        )
    """

    def __init__(self) -> None:
        """Initialize event publisher."""
        self._events: list[DomainEvent] = []

    def publish(
        self,
        event_type: EventType,
        payload: dict,
        correlation_id: Optional[str] = None,
    ) -> DomainEvent:
        """
        Publish a domain event.

        Args:
            event_type: Type of event
            payload: Event data
            correlation_id: Optional correlation ID (generated if not provided)

        Returns:
            The published event
        """
        event = DomainEvent(
            type=event_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

        self._events.append(event)
        self._log_event(event)

        return event

    def emit(self, event: DomainEvent) -> None:
        """Emit an already-constructed event."""
        self._events.append(event)
        self._log_event(event)

    def _log_event(self, event: DomainEvent) -> None:
        """Log event for debugging."""
        logger.info(
            "Event published",
            type=event.type.value,
            correlation_id=event.correlation_id,
            payload_keys=list(event.payload.keys()),
        )

    def get_events_by_type(self, event_type: EventType) -> list[DomainEvent]:
        """Get all events of a specific type."""
        return [e for e in self._events if e.type == event_type]

    def get_events_by_correlation(self, correlation_id: str) -> list[DomainEvent]:
        """Get all events in a workflow by correlation ID."""
        return [e for e in self._events if e.correlation_id == correlation_id]

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()


# Global publisher instance
_publisher: EventPublisher | None = None


def get_publisher() -> EventPublisher:
    """Get or create global event publisher."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


# Convenience functions
def emit_post_published(post_id: str, url: str, correlation_id: Optional[str] = None) -> DomainEvent:
    """Emit POST_PUBLISHED event."""
    return get_publisher().publish(
        EventType.POST_PUBLISHED,
        {"post_id": post_id, "url": url},
        correlation_id,
    )


def emit_seo_analyzed(post_id: str, score: float, correlation_id: Optional[str] = None) -> DomainEvent:
    """Emit SEO_ANALYZED event."""
    return get_publisher().publish(
        EventType.SEO_ANALYZED,
        {"post_id": post_id, "score": score},
        correlation_id,
    )


def emit_traffic_spike(post_id: str, pct_increase: float, correlation_id: Optional[str] = None) -> DomainEvent:
    """Emit TRAFFIC_SPIKE event."""
    return get_publisher().publish(
        EventType.TRAFFIC_SPIKE,
        {"post_id": post_id, "pct_increase": pct_increase},
        correlation_id,
    )