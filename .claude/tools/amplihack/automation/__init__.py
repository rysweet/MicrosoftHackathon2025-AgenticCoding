"""
Stage 2 Automation Engine Module

Bridges reflection insights to automated PR creation through intelligent
pattern prioritization and workflow orchestration.
"""

from .automation_guard import AutomationGuard
from .priority_scorer import PriorityScorer
from .stage2_engine import AutomationResult, PRResult, Stage2AutomationEngine

__all__ = [
    "Stage2AutomationEngine",
    "AutomationResult",
    "PRResult",
    "PriorityScorer",
    "AutomationGuard",
]
