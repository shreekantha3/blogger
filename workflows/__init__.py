"""
Workflows module for orchestrating complex content operations.

ARCHITECTURAL DECISION: Workflow Orchestration
----------------------------------------------
This module provides:
1. Content refresh pipelines (highest ROI activity)
2. New content pipelines (SERP → brief → human approval → AI → publish)
3. Link building pipelines (find orphans → suggest links → update)

Each workflow is traced via DomainEvents for debugging and optimization.
"""

from workflows.content_refresh_pipeline import ContentRefreshPipeline, run_refresh_audit

__all__ = [
    "ContentRefreshPipeline",
    "run_refresh_audit",
]