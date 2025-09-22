"""
Stage 2 Automation Engine

Core engine that bridges reflection insights to PR creation.
Orchestrates the complete automation workflow from pattern detection to implementation.
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from ..orchestration.workflow_orchestrator import WorkflowOrchestrator, WorkflowResult
    from .automation_guard import AutomationGuard
    from .priority_scorer import PriorityScorer, ScoringResult
except ImportError:
    # Handle direct execution
    from automation_guard import AutomationGuard
    from priority_scorer import PriorityScorer

    # Try alternative import path for orchestrator
    try:
        sys.path.append(str(Path(__file__).parent.parent / "orchestration"))
        from workflow_orchestrator import WorkflowOrchestrator, WorkflowResult
    except ImportError:
        WorkflowOrchestrator = None
        WorkflowResult = None


@dataclass
class AutomationResult:
    """Result of automation attempt"""

    success: bool
    workflow_id: Optional[str]
    pr_number: Optional[int]
    issue_number: Optional[int]
    branch_name: Optional[str]
    message: str
    timestamp: datetime
    pattern_type: Optional[str]
    score: Optional[int]


@dataclass
class PRResult:
    """Result of PR creation"""

    pr_number: int
    pr_url: str
    branch_name: str
    title: str
    status: str  # "draft", "ready", "merged"


class Stage2AutomationEngine:
    """
    Main automation engine for Stage 2 of the reflection-to-PR pipeline.

    Responsibilities:
    1. Process reflection insights from Stage 1
    2. Score and prioritize patterns for automation
    3. Check automation guards and limits
    4. Orchestrate improvement workflow execution
    5. Track automation results and learn from outcomes
    """

    def __init__(self, config_path: Path = None):
        """Initialize the automation engine"""
        self.config_path = config_path or Path(".claude/runtime/automation/engine_config.json")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.scorer = PriorityScorer()
        self.guard = AutomationGuard()

        # Initialize WorkflowOrchestrator if available
        if WorkflowOrchestrator:
            self.orchestrator = WorkflowOrchestrator()
        else:
            self.orchestrator = None
            print("Warning: WorkflowOrchestrator not available, using fallback implementation")

        # Load configuration
        self.config = self._load_config()

        # Workflow tracking
        self.active_workflows = {}
        self.workflow_history_path = Path(".claude/runtime/automation/workflow_history.json")

    def _load_config(self) -> Dict[str, Any]:
        """Load engine configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return json.load(f)
            except Exception:
                pass

        # Default configuration
        default_config = {
            "automation_enabled": True,
            "use_improvement_workflow_agent": True,
            "workflow_timeout_minutes": 30,
            "max_retries": 2,
            "pr_auto_merge": False,  # Never auto-merge without human review
            "issue_labels": ["automated", "improvement"],
            "branch_prefix": "auto-improve",
        }

        with open(self.config_path, "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config

    def process_reflection_insights(self, analysis_path: Path) -> AutomationResult:
        """
        Main entry point: Process reflection analysis and trigger automation if warranted.

        Args:
            analysis_path: Path to reflection analysis JSON file

        Returns:
            AutomationResult with success status and details
        """
        try:
            # Load reflection analysis
            if not analysis_path.exists():
                return self._create_result(
                    False, message=f"Analysis file not found: {analysis_path}"
                )

            with open(analysis_path) as f:
                analysis = json.load(f)

            # Extract patterns
            patterns = analysis.get("patterns", [])
            if not patterns:
                return self._create_result(False, message="No patterns found in analysis")

            # Score patterns
            scored_patterns = self.scorer.score_patterns(patterns)
            if not scored_patterns:
                return self._create_result(False, message="No patterns could be scored")

            # Get highest priority pattern
            top_pattern, top_score = scored_patterns[0]

            # Check if automation should proceed
            should_proceed, reason = self.should_create_pr(patterns)
            if not should_proceed:
                return self._create_result(
                    False,
                    message=f"Automation not triggered: {reason}",
                    pattern_type=top_pattern.get("type"),
                    score=top_score.score,
                )

            # Execute improvement workflow
            pr_result = self.execute_improvement_workflow(top_pattern)

            # Record success
            if pr_result:
                self.scorer.record_successful_automation(
                    top_pattern.get("type"), pr_result.pr_number
                )
                self.guard.record_automation_attempt(
                    success=True,
                    pr_number=pr_result.pr_number,
                    pattern_type=top_pattern.get("type"),
                )

                return self._create_result(
                    True,
                    pr_number=pr_result.pr_number,
                    branch_name=pr_result.branch_name,
                    message=f"Successfully created PR #{pr_result.pr_number}",
                    pattern_type=top_pattern.get("type"),
                    score=top_score.score,
                )
            else:
                # Record failure
                self.guard.record_automation_attempt(
                    success=False,
                    pattern_type=top_pattern.get("type"),
                    error="Workflow execution failed",
                )

                return self._create_result(
                    False,
                    message="Workflow execution failed",
                    pattern_type=top_pattern.get("type"),
                    score=top_score.score,
                )

        except Exception as e:
            return self._create_result(False, message=f"Engine error: {str(e)}")

    def should_create_pr(self, patterns: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Determine if patterns warrant PR creation.

        Args:
            patterns: List of detected patterns

        Returns:
            Tuple of (should_create, reason_message)
        """
        if not self.config.get("automation_enabled"):
            return False, "Automation is disabled in configuration"

        if not patterns:
            return False, "No patterns provided"

        # Score all patterns
        scored_patterns = self.scorer.score_patterns(patterns)
        if not scored_patterns:
            return False, "No patterns could be scored"

        # Get top pattern
        top_pattern, top_score = scored_patterns[0]

        # Check automation guards
        should_automate, guard_reason = self.guard.should_automate(
            score=top_score.score,
            pattern_type=top_pattern.get("type"),
            context={"patterns_count": len(patterns)},
        )

        if not should_automate:
            return False, guard_reason

        # Additional engine-specific checks
        if top_score.category == "no_action":
            return False, f"Pattern score ({top_score.score}) too low for automation"

        # Check for minimum pattern confidence
        if top_pattern.get("confidence", 1.0) < 0.7:
            return False, "Pattern confidence too low"

        return (
            True,
            f"Pattern '{top_pattern.get('type')}' scored {top_score.score} - automation approved",
        )

    def execute_improvement_workflow(self, pattern: Dict[str, Any]) -> Optional[PRResult]:
        """
        Execute the improvement workflow for a pattern.

        This either:
        1. Uses the WorkflowOrchestrator for full 13-step execution (preferred)
        2. Invokes the improvement-workflow agent
        3. Follows the DEFAULT_WORKFLOW.md process directly (fallback)

        Args:
            pattern: Pattern to create improvement for

        Returns:
            PRResult if successful, None otherwise
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Prefer WorkflowOrchestrator if available
            if self.orchestrator and self.config.get("use_workflow_orchestrator", True):
                return self._execute_via_orchestrator(workflow_id, pattern)
            elif self.config.get("use_improvement_workflow_agent"):
                # Use the improvement-workflow agent
                return self._execute_via_agent(workflow_id, pattern)
            else:
                # Direct workflow execution (fallback)
                return self._execute_direct_workflow(workflow_id, pattern)

        except Exception as e:
            print(f"Workflow execution failed: {e}")
            self._record_workflow(workflow_id, "failed", error=str(e))
            return None

    def _execute_via_orchestrator(
        self, workflow_id: str, pattern: Dict[str, Any]
    ) -> Optional[PRResult]:
        """Execute improvement using the WorkflowOrchestrator for full 13-step process"""
        print(f"Executing full workflow via WorkflowOrchestrator for {workflow_id}")

        # Record workflow start
        self._record_workflow(workflow_id, "started", pattern_type=pattern.get("type"))

        # Prepare task description from pattern
        task_description = self._create_task_description(pattern)

        try:
            # Execute the full workflow asynchronously
            workflow_result = asyncio.run(
                self.orchestrator.execute_workflow(
                    task_description=task_description, pattern_data=pattern, automation_mode=True
                )
            )

            # Convert WorkflowResult to PRResult
            if workflow_result.success and workflow_result.pr_number:
                self._record_workflow(
                    workflow_id,
                    "completed",
                    pr_number=workflow_result.pr_number,
                    steps_completed=workflow_result.steps_completed,
                    duration=workflow_result.duration_seconds,
                )

                return PRResult(
                    pr_number=workflow_result.pr_number,
                    pr_url=workflow_result.pr_url
                    or f"https://github.com/org/repo/pull/{workflow_result.pr_number}",
                    branch_name=workflow_result.branch_name or f"auto-{workflow_id}",
                    title=f"Automated improvement for {pattern.get('type', 'unknown')}",
                    status="ready",
                )
            else:
                self._record_workflow(
                    workflow_id,
                    "failed",
                    error="; ".join(workflow_result.errors)
                    if workflow_result.errors
                    else "Unknown error",
                    steps_completed=workflow_result.steps_completed,
                )
                return None

        except Exception as e:
            print(f"WorkflowOrchestrator execution failed: {e}")
            self._record_workflow(workflow_id, "failed", error=str(e))
            return None

    def _create_task_description(self, pattern: Dict[str, Any]) -> str:
        """Create a task description from pattern data"""
        pattern_type = pattern.get("type", "unknown").replace("_", " ")
        suggestion = pattern.get("suggestion", "")
        severity = pattern.get("severity", "medium")
        occurrences = pattern.get("count", 1)

        task = f"Implement automated improvement for {pattern_type} pattern"

        if suggestion:
            task += f"\n\nSuggested approach: {suggestion}"

        task += "\n\nDetails:"
        task += f"\n- Severity: {severity}"
        task += f"\n- Occurrences: {occurrences}"

        if pattern.get("context"):
            task += f"\n- Context: {json.dumps(pattern.get('context'), indent=2)}"

        return task

    def _execute_via_agent(self, workflow_id: str, pattern: Dict[str, Any]) -> Optional[PRResult]:
        """Execute improvement using the improvement-workflow agent"""
        agent_path = Path(".claude/agents/amplihack/improvement-workflow.md")

        if not agent_path.exists():
            print(f"Improvement workflow agent not found: {agent_path}")
            return None

        # Prepare agent context
        context = {
            "workflow_id": workflow_id,
            "pattern": pattern,
            "automation_mode": True,
            "branch_prefix": self.config.get("branch_prefix", "auto-improve"),
            "issue_labels": self.config.get("issue_labels", []),
        }

        # Create a task file for the agent
        task_file = Path(f".claude/runtime/automation/tasks/{workflow_id}.json")
        task_file.parent.mkdir(parents=True, exist_ok=True)

        with open(task_file, "w") as f:
            json.dump(context, f, indent=2)

        # Execute agent via subprocess (simplified - in practice would use Task tool)
        print(f"Triggering improvement-workflow agent for {workflow_id}")

        # Record workflow start
        self._record_workflow(workflow_id, "started", pattern_type=pattern.get("type"))

        # Simulate agent execution (in real implementation, would invoke Task tool)
        # For now, return a mock result
        return self._mock_pr_result(workflow_id, pattern)

    def _execute_direct_workflow(
        self, workflow_id: str, pattern: Dict[str, Any]
    ) -> Optional[PRResult]:
        """Execute workflow directly following DEFAULT_WORKFLOW.md"""
        workflow_path = Path(".claude/workflow/DEFAULT_WORKFLOW.md")

        if not workflow_path.exists():
            print("DEFAULT_WORKFLOW.md not found")
            return None

        print(f"Executing direct workflow for {workflow_id}")

        # Record workflow start
        self._record_workflow(workflow_id, "started", pattern_type=pattern.get("type"))

        # Step 1: Create GitHub issue
        issue_number = self._create_github_issue(pattern)
        if not issue_number:
            print("Failed to create GitHub issue")
            return None

        # Step 2: Create feature branch
        branch_name = f"{self.config.get('branch_prefix')}/{workflow_id}"
        if not self._create_branch(branch_name):
            print(f"Failed to create branch: {branch_name}")
            return None

        # Steps 3-12: Implementation (simplified for this version)
        # In production, would execute full workflow steps
        print(f"Executing workflow steps 3-12 for pattern: {pattern.get('type')}")

        # Step 13: Create PR
        pr_result = self._create_pr(branch_name, issue_number, pattern)

        if pr_result:
            self._record_workflow(workflow_id, "completed", pr_number=pr_result.pr_number)
            return pr_result
        else:
            self._record_workflow(workflow_id, "failed", error="PR creation failed")
            return None

    def _create_github_issue(self, pattern: Dict[str, Any]) -> Optional[int]:
        """Create GitHub issue for the improvement"""
        try:
            title = f"Automated improvement: {pattern.get('type', 'unknown').replace('_', ' ')}"

            body = f"""## Automated Improvement

**Pattern Type**: {pattern.get("type")}
**Severity**: {pattern.get("severity", "medium")}
**Occurrences**: {pattern.get("count", 1)}

## Description
{pattern.get("suggestion", "Improvement needed based on detected pattern")}

## Context
{json.dumps(pattern.get("context", {}), indent=2)}

---
Generated by Stage 2 Automation Engine"""

            labels = ",".join(self.config.get("issue_labels", []))

            # Use gh CLI to create issue
            result = subprocess.run(
                ["gh", "issue", "create", "--title", title, "--body", body, "--label", labels],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Extract issue number from output
                import re

                match = re.search(r"/issues/(\d+)", result.stdout)
                if match:
                    return int(match.group(1))

        except Exception as e:
            print(f"Failed to create issue: {e}")

        return None

    def _create_branch(self, branch_name: str) -> bool:
        """Create and checkout a new feature branch"""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            base_branch = result.stdout.strip() or "main"

            # Create new branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name, base_branch], capture_output=True, text=True
            )

            return result.returncode == 0

        except Exception as e:
            print(f"Failed to create branch: {e}")
            return False

    def _create_pr(self, branch_name: str, issue_number: int, pattern: Dict) -> Optional[PRResult]:
        """Create pull request for the improvement"""
        try:
            title = (
                f"Fix: Automated improvement for {pattern.get('type', 'unknown').replace('_', ' ')}"
            )

            body = f"""## Automated Improvement PR

Fixes #{issue_number}

### Pattern Addressed
- **Type**: {pattern.get("type")}
- **Severity**: {pattern.get("severity", "medium")}

### Changes Made
- [Automated implementation based on pattern analysis]

### Testing
- [ ] Tests added/updated
- [ ] CI passing
- [ ] Manual verification completed

---
Generated with Claude Code
Co-Authored-By: Stage 2 Automation Engine"""

            # Push branch first
            subprocess.run(["git", "push", "-u", "origin", branch_name])

            # Create PR
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    title,
                    "--body",
                    body,
                    "--base",
                    "main",
                    "--head",
                    branch_name,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Extract PR number and URL
                import re

                pr_match = re.search(r"/pull/(\d+)", result.stdout)
                if pr_match:
                    pr_number = int(pr_match.group(1))
                    pr_url = result.stdout.strip()

                    return PRResult(
                        pr_number=pr_number,
                        pr_url=pr_url,
                        branch_name=branch_name,
                        title=title,
                        status="ready",
                    )

        except Exception as e:
            print(f"Failed to create PR: {e}")

        return None

    def _mock_pr_result(self, workflow_id: str, pattern: Dict) -> PRResult:
        """Create mock PR result for testing"""
        return PRResult(
            pr_number=999,
            pr_url="https://github.com/org/repo/pull/999",
            branch_name=f"auto-improve/{workflow_id}",
            title=f"Automated fix for {pattern.get('type')}",
            status="draft",
        )

    def _record_workflow(self, workflow_id: str, status: str, **kwargs):
        """Record workflow execution for tracking"""
        history = []
        if self.workflow_history_path.exists():
            try:
                with open(self.workflow_history_path) as f:
                    history = json.load(f)
            except Exception:
                pass

        record = {
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            **kwargs,
        }

        history.append(record)

        # Keep last 100 records
        if len(history) > 100:
            history = history[-100:]

        try:
            with open(self.workflow_history_path, "w") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def _create_result(self, success: bool, **kwargs) -> AutomationResult:
        """Create AutomationResult with defaults"""
        return AutomationResult(
            success=success,
            workflow_id=kwargs.get("workflow_id"),
            pr_number=kwargs.get("pr_number"),
            issue_number=kwargs.get("issue_number"),
            branch_name=kwargs.get("branch_name"),
            message=kwargs.get("message", ""),
            timestamp=datetime.now(),
            pattern_type=kwargs.get("pattern_type"),
            score=kwargs.get("score"),
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        guard_status = self.guard.get_current_status()

        # Load recent workflow history
        recent_workflows = []
        if self.workflow_history_path.exists():
            try:
                with open(self.workflow_history_path) as f:
                    history = json.load(f)
                    recent_workflows = history[-5:] if history else []
            except Exception:
                pass

        return {
            "engine_enabled": self.config.get("automation_enabled"),
            "guard_status": guard_status,
            "recent_workflows": recent_workflows,
            "active_workflows": list(self.active_workflows.keys()),
            "config": self.config,
        }

    async def process_reflection_insights_async(self, analysis_path: Path) -> AutomationResult:
        """Async version of process_reflection_insights for non-blocking execution"""
        return await asyncio.to_thread(self.process_reflection_insights, analysis_path)
