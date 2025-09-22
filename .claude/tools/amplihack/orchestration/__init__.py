"""
Orchestration Module

Provides workflow orchestration capabilities for the automated improvement pipeline.
"""

from .workflow_orchestrator import (
    WorkflowContext,
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowStep,
    execute_workflow_sync,
)

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowResult",
    "WorkflowContext",
    "WorkflowStep",
    "execute_workflow_sync",
]

__version__ = "1.0.0"
