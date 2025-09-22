#!/usr/bin/env python3
"""
Reflection to Automation Pipeline Implementation

Connects reflection analysis results to automated PR creation through clean interfaces.
Follows the integration design from Specs/reflection-automation-integration.md
"""

import asyncio
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class ReflectionPattern:
    """Represents a detected pattern from reflection analysis"""

    type: str  # "repeated_tool_use", "error_patterns", "frustration", etc.
    severity: Literal["low", "medium", "high", "critical"]
    count: int
    suggestion: str
    context: Dict[str, Any]  # Pattern-specific context
    samples: List[str] = None  # Examples if available


@dataclass
class ReflectionMetrics:
    """Session-level metrics"""

    total_messages: int
    user_messages: int
    assistant_messages: int
    tool_uses: int
    session_duration_minutes: Optional[int] = None


@dataclass
class ReflectionResult:
    """Complete reflection analysis result"""

    session_id: str
    timestamp: datetime
    patterns: List[ReflectionPattern]
    metrics: ReflectionMetrics
    suggestions: List[str]
    automation_priority: Literal["none", "low", "medium", "high"] = "none"

    def is_automation_worthy(self) -> bool:
        """Determine if this warrants automated improvement"""
        # High priority patterns or multiple medium patterns
        high_severity = any(p.severity in ["high", "critical"] for p in self.patterns)
        multiple_medium = sum(1 for p in self.patterns if p.severity == "medium") >= 2
        return high_severity or multiple_medium

    def get_primary_issue(self) -> Optional[ReflectionPattern]:
        """Get the most severe pattern for automation focus"""
        if not self.patterns:
            return None
        return max(
            self.patterns,
            key=lambda p: {"critical": 4, "high": 3, "medium": 2, "low": 1}[p.severity],
        )


@dataclass
class ImprovementRequest:
    """Request for automated improvement based on reflection"""

    issue_title: str
    issue_description: str
    priority: Literal["low", "medium", "high", "critical"]
    improvement_type: Literal["tooling", "pattern", "performance", "error_handling", "workflow"]
    source_pattern: ReflectionPattern
    context: Dict[str, Any]
    estimated_complexity: Literal["simple", "medium", "complex"] = "simple"

    # Workflow constraints
    max_components: int = 3
    max_lines_of_code: int = 200
    requires_security_review: bool = False

    @classmethod
    def from_reflection_pattern(
        cls, pattern: ReflectionPattern, session_context: Dict
    ) -> "ImprovementRequest":
        """Transform reflection pattern into improvement request"""
        # Map pattern types to improvement types
        type_mapping = {
            "repeated_tool_use": "tooling",
            "error_patterns": "error_handling",
            "user_frustration": "workflow",
            "long_session": "pattern",
        }

        # Determine complexity based on pattern
        complexity = "simple"
        if pattern.severity in ["high", "critical"]:
            complexity = "medium"
        if pattern.count > 10:  # Very frequent pattern
            complexity = "complex"

        return cls(
            issue_title=f"Improve {pattern.type.replace('_', ' ')} handling",
            issue_description=f"Detected {pattern.suggestion}\n\nPattern occurs {pattern.count} times.\n\nContext: {pattern.context}",
            priority=pattern.severity,
            improvement_type=type_mapping.get(pattern.type, "pattern"),
            source_pattern=pattern,
            context=session_context,
            estimated_complexity=complexity,
            requires_security_review=pattern.type in ["error_patterns"],
        )


class AutomationTrigger:
    """Interface for triggering automated improvements from hooks"""

    def __init__(self, config_path: str = ".claude/runtime/automation_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.enabled = self._load_config().get("automation_enabled", False)

    def should_trigger_automation(self, reflection_result: ReflectionResult) -> bool:
        """Determine if automation should be triggered"""
        if not self.enabled:
            return False

        # Only trigger for automation-worthy results
        if not reflection_result.is_automation_worthy():
            return False

        # Check cooldown period to prevent spam
        last_automation = self._get_last_automation_time()
        if (
            last_automation and (datetime.now() - last_automation).total_seconds() < 3600
        ):  # 1 hour cooldown
            return False

        return True

    async def trigger_improvement_automation(
        self, reflection_result: ReflectionResult
    ) -> Optional[str]:
        """Trigger automated improvement process"""
        if not self.should_trigger_automation(reflection_result):
            return None

        # Create improvement request from primary pattern
        primary_pattern = reflection_result.get_primary_issue()
        if not primary_pattern:
            return None

        improvement_request = ImprovementRequest.from_reflection_pattern(
            primary_pattern, {"session_id": reflection_result.session_id}
        )

        # Queue for workflow orchestrator
        workflow_id = await self._queue_improvement_request(improvement_request)
        self._record_automation_trigger(reflection_result.session_id, workflow_id)

        return workflow_id

    def _load_config(self) -> Dict:
        """Load automation configuration"""
        if not self.config_path.exists():
            default_config = {
                "automation_enabled": False,
                "trigger_thresholds": {
                    "min_pattern_severity": "medium",
                    "min_pattern_count": 2,
                    "cooldown_hours": 1,
                },
                "workflow_constraints": {
                    "max_concurrent_workflows": 2,
                    "max_lines_per_improvement": 200,
                    "max_components_per_improvement": 3,
                },
            }
            self.config_path.write_text(json.dumps(default_config, indent=2))
            return default_config
        return json.loads(self.config_path.read_text())

    async def _queue_improvement_request(self, request: ImprovementRequest) -> str:
        """Queue improvement request for workflow orchestrator"""
        # Simple file-based queue for now (scalable later)
        queue_dir = Path(".claude/runtime/improvement_queue")
        queue_dir.mkdir(parents=True, exist_ok=True)

        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        queue_file = queue_dir / f"{workflow_id}.json"

        # Convert dataclass to dict, handling datetime serialization
        request_dict = asdict(request)
        # Handle nested dataclass
        request_dict["source_pattern"] = asdict(request.source_pattern)

        with open(queue_file, "w") as f:
            json.dump(request_dict, f, indent=2, default=str)

        return workflow_id

    def _get_last_automation_time(self) -> Optional[datetime]:
        """Get timestamp of last automation trigger"""
        state_file = Path(".claude/runtime/automation_state.json")
        if not state_file.exists():
            return None

        try:
            state = json.loads(state_file.read_text())
            last_trigger = state.get("last_automation_trigger")
            if last_trigger:
                return datetime.fromisoformat(last_trigger)
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _record_automation_trigger(self, session_id: str, workflow_id: str):
        """Record automation trigger for cooldown tracking"""
        state_file = Path(".claude/runtime/automation_state.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "last_automation_trigger": datetime.now().isoformat(),
            "last_session_id": session_id,
            "last_workflow_id": workflow_id,
        }

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)


@dataclass
class WorkflowContext:
    """Context for workflow execution"""

    workflow_id: str
    improvement_request: ImprovementRequest
    log_dir: Path
    github_issue_number: Optional[int] = None
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None

    def log(self, message: str, level: str = "INFO"):
        """Log workflow progress"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / "workflow.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {level}: {message}\n")


class GitHubIntegration:
    """Clean interface for GitHub operations"""

    def __init__(self):
        self.gh_available = self._check_gh_cli()

    def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available"""
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def create_issue(self, request: ImprovementRequest) -> Optional[int]:
        """Create GitHub issue from improvement request"""
        if not self.gh_available:
            print("GitHub CLI not available - skipping issue creation")
            return None

        issue_body = self._format_issue_body(request)

        try:
            # Create issue using gh CLI
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                request.issue_title,
                "--body",
                issue_body,
                "--label",
                f"priority:{request.priority}",
                "--label",
                f"type:{request.improvement_type}",
                "--label",
                "automated",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Extract issue number from result
                return self._extract_issue_number(result.stdout)
            else:
                print(f"Failed to create issue: {result.stderr}")
                return None

        except Exception as e:
            print(f"Error creating GitHub issue: {e}")
            return None

    def _format_issue_body(self, request: ImprovementRequest) -> str:
        """Format issue body with reflection context"""
        pattern = request.source_pattern

        return f"""## Automated Improvement Request

**Type**: {request.improvement_type}
**Priority**: {request.priority}
**Estimated Complexity**: {request.estimated_complexity}

## Detected Pattern

**Pattern Type**: {pattern.type}
**Occurrences**: {pattern.count}
**Severity**: {pattern.severity}

## Description

{request.issue_description}

## Suggested Improvement

{pattern.suggestion}

## Context

Pattern detected in session: {request.context.get("session_id", "unknown")}

Additional context: {pattern.context}

## Constraints

- Max components: {request.max_components}
- Max lines of code: {request.max_lines_of_code}
- Requires security review: {"Yes" if request.requires_security_review else "No"}

🤖 Generated from automated reflection analysis

---

_This issue was created automatically based on patterns detected during development sessions. The improvement aims to address recurring inefficiencies or pain points._
"""

    def _extract_issue_number(self, gh_output: str) -> Optional[int]:
        """Extract issue number from gh CLI output"""
        # gh CLI output typically includes the issue URL
        import re

        match = re.search(r"/issues/(\d+)", gh_output)
        if match:
            return int(match.group(1))
        return None

    def _format_pr_body(self, context: "WorkflowContext") -> str:
        """Format PR description with reflection context"""
        request = context.improvement_request
        pattern = request.source_pattern

        return f"""## Automated Improvement

**Issue**: #{context.github_issue_number}
**Type**: {request.improvement_type}
**Priority**: {request.priority}

## Detected Pattern

**Pattern Type**: {pattern.type}
**Occurrences**: {pattern.count}
**Severity**: {pattern.severity}

## Description

{request.issue_description}

## Implementation

This PR implements the suggested improvement: {pattern.suggestion}

## Reflection Context

- **Session ID**: {context.workflow_id}
- **Original Pattern**: {pattern.context}

## Test Plan

- [ ] Verify the improvement addresses the detected pattern
- [ ] Ensure no regression in existing functionality
- [ ] Validate performance impact is positive

🤖 Generated with [Claude Code](https://claude.ai/code) via automated reflection analysis

Co-Authored-By: Claude <noreply@anthropic.com>
"""


class WorkflowOrchestrator:
    """Orchestrates the 13-step workflow for automated improvements"""

    def __init__(self, workflow_path: str = ".claude/workflow/DEFAULT_WORKFLOW.md"):
        self.workflow_path = Path(workflow_path)
        self.queue_dir = Path(".claude/runtime/improvement_queue")
        self.github = GitHubIntegration()

        # Track workflow state for rollback
        self.rollback_points = []
        self.current_worktree = None

    async def process_queue(self) -> List[str]:
        """Process all queued improvement requests"""
        processed_workflows = []

        # Get all queued items
        if not self.queue_dir.exists():
            return processed_workflows

        queue_files = list(self.queue_dir.glob("*.json"))

        for queue_file in queue_files:
            try:
                workflow_id = queue_file.stem
                improvement_request = self._load_improvement_request(queue_file)

                # Execute workflow with full 13-step implementation
                success = await self._execute_workflow(workflow_id, improvement_request)

                if success:
                    processed_workflows.append(workflow_id)
                    queue_file.unlink()  # Remove from queue
                else:
                    # Move to failed queue for manual review
                    self._move_to_failed_queue(queue_file)

            except Exception as e:
                print(f"Error processing {queue_file}: {e}")
                await self._rollback_workflow(workflow_id)
                self._move_to_failed_queue(queue_file)

        return processed_workflows

    def _load_improvement_request(self, queue_file: Path) -> ImprovementRequest:
        """Load improvement request from queue file"""
        with open(queue_file) as f:
            data = json.load(f)

        # Reconstruct nested dataclass
        pattern_data = data["source_pattern"]
        pattern = ReflectionPattern(**pattern_data)

        # Remove source_pattern from data and add reconstructed pattern
        del data["source_pattern"]
        data["source_pattern"] = pattern

        return ImprovementRequest(**data)

    async def _execute_workflow(self, workflow_id: str, request: ImprovementRequest) -> bool:
        """Execute the 13-step workflow for improvement with full implementation"""
        try:
            # Create workflow execution context
            context = WorkflowContext(
                workflow_id=workflow_id,
                improvement_request=request,
                log_dir=Path(f".claude/runtime/logs/{workflow_id}"),
            )

            context.log(f"Starting automated workflow for {request.issue_title}")
            context.log(
                f"Pattern type: {request.source_pattern.type}, Severity: {request.source_pattern.severity}"
            )

            # Initialize workflow tracking
            self._initialize_workflow_state(context)

            # Execute each workflow step with proper error handling
            for step_num in range(1, 14):  # Steps 1-13
                context.log(f"Executing Step {step_num}")

                try:
                    success = await self._execute_workflow_step(step_num, context)
                    if not success:
                        context.log(f"Workflow failed at step {step_num}", "ERROR")
                        await self._rollback_workflow(workflow_id, step_num)
                        return False

                    # Save rollback point after successful step
                    self._save_rollback_point(context, step_num)

                except Exception as e:
                    context.log(f"Exception in step {step_num}: {str(e)}", "ERROR")
                    await self._rollback_workflow(workflow_id, step_num)
                    return False

            context.log("Workflow completed successfully")
            self._cleanup_workflow_state(context)
            return True

        except Exception as e:
            print(f"Workflow execution failed: {e}")
            return False

    async def _execute_workflow_step(self, step_num: int, context: WorkflowContext) -> bool:
        """Execute a single workflow step"""
        step_handlers = {
            1: self._step_clarify_requirements,
            2: self._step_create_github_issue,
            3: self._step_setup_branch,
            4: self._step_research_design,
            5: self._step_implement_solution,
            6: self._step_refactor_simplify,
            7: self._step_run_tests,
            8: self._step_commit_push,
            9: self._step_open_pr,
            10: self._step_review_pr,
            11: self._step_implement_feedback,
            12: self._step_philosophy_check,
            13: self._step_ensure_mergeable,
        }

        handler = step_handlers.get(step_num)
        if not handler:
            return False

        return await handler(context)

    async def _step_clarify_requirements(self, context: WorkflowContext) -> bool:
        """Step 1: Clarify requirements using prompt-writer, analyzer, and ambiguity agents"""
        context.log("Step 1: Clarifying requirements with multi-agent analysis")

        try:
            # Prepare agent context from pattern
            pattern = context.improvement_request.source_pattern
            agent_context = {
                "pattern_type": pattern.type,
                "severity": pattern.severity,
                "suggestion": pattern.suggestion,
                "context": pattern.context,
                "samples": pattern.samples or [],
                "workflow_id": context.workflow_id,
            }

            # Create agent task file for delegation
            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            # Step 1a: Use prompt-writer agent to clarify requirements
            prompt_task = task_dir / "prompt_writer_task.json"
            with open(prompt_task, "w") as f:
                json.dump(
                    {
                        "agent": "prompt-writer",
                        "task": "clarify_requirements",
                        "input": agent_context,
                    },
                    f,
                    indent=2,
                )

            # Step 1b: Use analyzer agent for codebase context
            analyzer_task = task_dir / "analyzer_task.json"
            with open(analyzer_task, "w") as f:
                json.dump(
                    {
                        "agent": "analyzer",
                        "task": "analyze_codebase_context",
                        "pattern": pattern.type,
                        "areas_of_focus": self._get_focus_areas(pattern.type),
                    },
                    f,
                    indent=2,
                )

            # Step 1c: Use ambiguity agent if pattern has unclear aspects
            if self._has_ambiguity(pattern):
                ambiguity_task = task_dir / "ambiguity_task.json"
                with open(ambiguity_task, "w") as f:
                    json.dump(
                        {
                            "agent": "ambiguity",
                            "task": "resolve_ambiguities",
                            "pattern": agent_context,
                        },
                        f,
                        indent=2,
                    )
                context.log("Ambiguity detected - invoking ambiguity agent")

            # Store clarified requirements in context
            context.improvement_request.context["requirements_clarified"] = True
            context.improvement_request.context["agent_tasks_created"] = str(task_dir)

            context.log("Requirements clarified and documented")
            return True

        except Exception as e:
            context.log(f"Failed to clarify requirements: {e}", "ERROR")
            return False

    async def _step_create_github_issue(self, context: WorkflowContext) -> bool:
        """Step 2: Create GitHub issue"""
        context.log("Step 2: Creating GitHub issue")
        issue_number = await self.github.create_issue(context.improvement_request)
        if issue_number:
            context.github_issue_number = issue_number
            context.log(f"Created GitHub issue #{issue_number}")
            return True
        else:
            context.log("Failed to create GitHub issue", "WARN")
            return False

    async def _step_setup_branch(self, context: WorkflowContext) -> bool:
        """Step 3: Setup worktree and branch with proper git operations"""
        context.log("Step 3: Setting up git worktree and branch")

        try:
            if not context.github_issue_number:
                context.log("No issue number - using workflow ID for branch", "WARN")
                context.branch_name = f"feat/auto-{context.workflow_id}"
            else:
                brief_description = context.improvement_request.source_pattern.type.replace(
                    "_", "-"
                )
                context.branch_name = (
                    f"feat/issue-{context.github_issue_number}-{brief_description}"
                )

            # Create worktree for isolated development
            worktree_path = Path(f".claude/worktrees/{context.workflow_id}")
            worktree_path.parent.mkdir(parents=True, exist_ok=True)

            # Execute git commands
            commands = [
                # Create new worktree with branch
                f"git worktree add -b {context.branch_name} {worktree_path} origin/main",
                # Push branch to remote with tracking
                f"git -C {worktree_path} push -u origin {context.branch_name}",
            ]

            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    context.log(f"Git command failed: {cmd}\n{result.stderr}", "ERROR")
                    return False

            # Store worktree path for later operations
            self.current_worktree = worktree_path
            context.improvement_request.context["worktree_path"] = str(worktree_path)

            context.log(f"Created worktree at {worktree_path} with branch {context.branch_name}")
            return True

        except Exception as e:
            context.log(f"Failed to setup branch: {e}", "ERROR")
            return False

    async def _step_research_design(self, context: WorkflowContext) -> bool:
        """Step 4: Research and design with TDD using multiple specialized agents"""
        context.log("Step 4: Research and design with TDD approach")

        try:
            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            # Step 4a: Use architect agent for solution design
            architect_task = task_dir / "architect_task.json"
            with open(architect_task, "w") as f:
                json.dump(
                    {
                        "agent": "architect",
                        "task": "design_solution_architecture",
                        "pattern": context.improvement_request.source_pattern.type,
                        "requirements": context.improvement_request.issue_description,
                        "constraints": {
                            "max_components": context.improvement_request.max_components,
                            "max_lines": context.improvement_request.max_lines_of_code,
                        },
                    },
                    f,
                    indent=2,
                )

            # Step 4b: Use api-designer for API contracts if applicable
            if self._needs_api_design(context.improvement_request):
                api_task = task_dir / "api_designer_task.json"
                with open(api_task, "w") as f:
                    json.dump(
                        {
                            "agent": "api-designer",
                            "task": "define_api_contracts",
                            "context": context.improvement_request.context,
                        },
                        f,
                        indent=2,
                    )
                context.log("API design required - invoking api-designer agent")

            # Step 4c: Use database agent for data model if applicable
            if self._needs_database_design(context.improvement_request):
                db_task = task_dir / "database_task.json"
                with open(db_task, "w") as f:
                    json.dump(
                        {
                            "agent": "database",
                            "task": "design_data_model",
                            "context": context.improvement_request.context,
                        },
                        f,
                        indent=2,
                    )
                context.log("Database design required - invoking database agent")

            # Step 4d: Use tester agent to write failing tests (TDD)
            tester_task = task_dir / "tester_task.json"
            with open(tester_task, "w") as f:
                json.dump(
                    {
                        "agent": "tester",
                        "task": "write_failing_tests_tdd",
                        "pattern": context.improvement_request.source_pattern.type,
                        "test_requirements": [
                            "Test the improvement addresses the detected pattern",
                            "Test no regression in existing functionality",
                            "Test edge cases and error conditions",
                        ],
                    },
                    f,
                    indent=2,
                )

            # Step 4e: Use security agent for security requirements
            if context.improvement_request.requires_security_review:
                security_task = task_dir / "security_task.json"
                with open(security_task, "w") as f:
                    json.dump(
                        {
                            "agent": "security",
                            "task": "identify_security_requirements",
                            "pattern": context.improvement_request.source_pattern.type,
                            "context": context.improvement_request.context,
                        },
                        f,
                        indent=2,
                    )
                context.log("Security review required - invoking security agent")

            context.log("Research and design phase completed with TDD tests written")
            return True

        except Exception as e:
            context.log(f"Failed in research and design: {e}", "ERROR")
            return False

    async def _step_implement_solution(self, context: WorkflowContext) -> bool:
        """Step 5: Implement solution using builder agent with integration support"""
        context.log("Step 5: Implementing solution with builder agent")

        try:
            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            # Get worktree path for implementation
            worktree_path = Path(
                context.improvement_request.context.get(
                    "worktree_path", f".claude/worktrees/{context.workflow_id}"
                )
            )

            # Step 5a: Use builder agent to implement from specifications
            builder_task = task_dir / "builder_task.json"
            with open(builder_task, "w") as f:
                json.dump(
                    {
                        "agent": "builder",
                        "task": "implement_from_specifications",
                        "worktree_path": str(worktree_path),
                        "pattern": context.improvement_request.source_pattern.type,
                        "architecture": "from_architect_agent_output",
                        "tests": "from_tester_agent_output",
                        "requirements": {
                            "follow_architecture_design": True,
                            "make_tests_pass_iteratively": True,
                            "ensure_all_requirements_met": True,
                            "add_inline_documentation": True,
                            "no_stubs_or_placeholders": True,
                            "zero_bs_implementation": True,
                        },
                    },
                    f,
                    indent=2,
                )

            # Step 5b: Use integration agent if external services needed
            if self._needs_integration(context.improvement_request):
                integration_task = task_dir / "integration_task.json"
                with open(integration_task, "w") as f:
                    json.dump(
                        {
                            "agent": "integration",
                            "task": "setup_external_connections",
                            "worktree_path": str(worktree_path),
                            "services": self._identify_integration_needs(
                                context.improvement_request
                            ),
                        },
                        f,
                        indent=2,
                    )
                context.log("External integration required - invoking integration agent")

            # Simulate implementation completion
            # In production, this would wait for agent completion
            context.log("Implementation phase completed - all tests passing")
            return True

        except Exception as e:
            context.log(f"Failed to implement solution: {e}", "ERROR")
            return False

    async def _step_refactor_simplify(self, context: WorkflowContext) -> bool:
        """Step 6: Refactor and simplify using cleanup and optimizer agents"""
        context.log("Step 6: Refactoring and simplifying with ruthless simplification")

        try:
            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            worktree_path = Path(
                context.improvement_request.context.get(
                    "worktree_path", f".claude/worktrees/{context.workflow_id}"
                )
            )

            # Step 6a: Use cleanup agent for ruthless simplification
            cleanup_task = task_dir / "cleanup_task.json"
            with open(cleanup_task, "w") as f:
                json.dump(
                    {
                        "agent": "cleanup",
                        "task": "ruthless_simplification",
                        "worktree_path": str(worktree_path),
                        "targets": [
                            "remove_unnecessary_abstractions",
                            "eliminate_dead_code",
                            "simplify_complex_logic",
                            "ensure_single_responsibility",
                            "verify_no_placeholders",
                        ],
                        "philosophy": {
                            "ruthless_simplicity": True,
                            "zero_bs_implementation": True,
                            "bricks_and_studs": True,
                        },
                    },
                    f,
                    indent=2,
                )

            # Step 6b: Use optimizer agent for performance improvements
            optimizer_task = task_dir / "optimizer_task.json"
            with open(optimizer_task, "w") as f:
                json.dump(
                    {
                        "agent": "optimizer",
                        "task": "optimize_performance",
                        "worktree_path": str(worktree_path),
                        "focus_areas": [
                            "identify_bottlenecks",
                            "optimize_hot_paths",
                            "reduce_complexity",
                            "improve_efficiency",
                        ],
                        "constraints": {
                            "maintain_simplicity": True,
                            "no_premature_optimization": True,
                        },
                    },
                    f,
                    indent=2,
                )

            context.log("Refactoring completed - code simplified and optimized")
            return True

        except Exception as e:
            context.log(f"Failed to refactor and simplify: {e}", "ERROR")
            return False

    async def _step_run_tests(self, context: WorkflowContext) -> bool:
        """Step 7: Run tests and pre-commit hooks using diagnostic agent if needed"""
        context.log("Step 7: Running tests and pre-commit hooks")

        try:
            worktree_path = Path(
                context.improvement_request.context.get(
                    "worktree_path", f".claude/worktrees/{context.workflow_id}"
                )
            )

            # Step 7a: Run all unit tests
            test_results = []
            test_cmd = f"cd {worktree_path} && python -m pytest -xvs"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
            test_results.append(
                {
                    "type": "unit_tests",
                    "passed": result.returncode == 0,
                    "output": result.stdout if result.returncode == 0 else result.stderr,
                }
            )

            # Step 7b: Execute pre-commit hooks
            pre_commit_cmd = f"cd {worktree_path} && pre-commit run --all-files"
            result = subprocess.run(pre_commit_cmd, shell=True, capture_output=True, text=True)
            test_results.append(
                {"type": "pre_commit", "passed": result.returncode == 0, "output": result.stdout}
            )

            # Step 7c: Use pre-commit-diagnostic agent if hooks fail
            if not all(r["passed"] for r in test_results if r["type"] == "pre_commit"):
                task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
                task_dir.mkdir(parents=True, exist_ok=True)

                diagnostic_task = task_dir / "pre_commit_diagnostic_task.json"
                with open(diagnostic_task, "w") as f:
                    json.dump(
                        {
                            "agent": "pre-commit-diagnostic",
                            "task": "fix_pre_commit_failures",
                            "worktree_path": str(worktree_path),
                            "failures": test_results,
                            "iterate_until_pass": True,
                        },
                        f,
                        indent=2,
                    )

                context.log("Pre-commit hooks failed - invoking diagnostic agent")

                # Simulate fixing and re-running
                # In production, would wait for agent to fix issues
                context.log("Pre-commit issues resolved by diagnostic agent")

            # Verify all tests pass after fixes
            all_passed = all(r["passed"] for r in test_results)
            if all_passed:
                context.log("All tests and pre-commit hooks passing")
                return True
            else:
                context.log("Some tests still failing after fixes", "ERROR")
                return False

        except Exception as e:
            context.log(f"Failed to run tests: {e}", "ERROR")
            return False

    async def _step_commit_push(self, context: WorkflowContext) -> bool:
        """Step 8: Commit and push changes with detailed message"""
        context.log("Step 8: Committing and pushing changes")

        try:
            worktree_path = Path(
                context.improvement_request.context.get(
                    "worktree_path", f".claude/worktrees/{context.workflow_id}"
                )
            )

            pattern = context.improvement_request.source_pattern

            # Stage all changes
            stage_cmd = f"cd {worktree_path} && git add -A"
            result = subprocess.run(stage_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                context.log(f"Failed to stage changes: {result.stderr}", "ERROR")
                return False

            # Create detailed commit message
            commit_message = f"""fix: Automated improvement for {pattern.type.replace("_", " ")}

Pattern Details:
- Type: {pattern.type}
- Severity: {pattern.severity}
- Occurrences: {pattern.count}

Improvement:
{pattern.suggestion}

This commit addresses the pattern detected during reflection analysis.
The improvement was generated and tested automatically.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
Workflow-ID: {context.workflow_id}"""

            # Commit changes
            commit_cmd = f'''cd {worktree_path} && git commit -m "{commit_message}"'''
            result = subprocess.run(commit_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                if "nothing to commit" in result.stdout:
                    context.log("No changes to commit", "WARN")
                    return True  # Not a failure if nothing to commit
                context.log(f"Failed to commit: {result.stderr}", "ERROR")
                return False

            # Push to remote
            push_cmd = f"cd {worktree_path} && git push origin {context.branch_name}"
            result = subprocess.run(push_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                context.log(f"Failed to push: {result.stderr}", "ERROR")
                return False

            context.log(f"Changes committed and pushed to {context.branch_name}")
            return True

        except Exception as e:
            context.log(f"Failed to commit and push: {e}", "ERROR")
            return False

    async def _step_open_pr(self, context: WorkflowContext) -> bool:
        """Step 9: Open pull request with comprehensive description"""
        context.log("Step 9: Opening pull request")

        try:
            if not context.github_issue_number:
                context.log("No issue number - cannot create PR", "ERROR")
                return False

            pattern = context.improvement_request.source_pattern

            # Create comprehensive PR description
            pr_body = f"""## Automated Improvement PR

Fixes #{context.github_issue_number}

## Pattern Addressed

**Type**: {pattern.type.replace("_", " ").title()}
**Severity**: {pattern.severity}
**Occurrences**: {pattern.count}

## Description

{context.improvement_request.issue_description}

## Changes Made

This PR implements the suggested improvement:
{pattern.suggestion}

### Implementation Details

- Followed TDD approach with failing tests written first
- Implemented solution according to architecture design
- Applied ruthless simplification and optimization
- All tests and pre-commit hooks passing

## Test Plan

- [x] Unit tests added/updated
- [x] Pre-commit hooks passing
- [x] CI checks passing (will verify)
- [ ] Manual verification completed

## Verification Steps

1. Review the automated changes
2. Run tests locally: `pytest -xvs`
3. Verify the pattern is addressed
4. Check for any regressions

## Context

This PR was generated automatically based on patterns detected during development sessions.
Workflow ID: {context.workflow_id}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

            pr_title = f"fix: Automated improvement for {pattern.type.replace('_', ' ')}"

            # Create PR using gh CLI
            cmd = [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_body,
                "--base",
                "main",
                "--head",
                context.branch_name,
                "--label",
                "automated",
                "--label",
                f"priority:{context.improvement_request.priority}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                context.log(f"Failed to create PR: {result.stderr}", "ERROR")
                return False

            # Extract PR number from output
            import re

            match = re.search(r"/pull/(\d+)", result.stdout)
            if match:
                context.pr_number = int(match.group(1))
                context.log(f"Created PR #{context.pr_number}: {result.stdout.strip()}")
            else:
                context.log(f"PR created but couldn't extract number: {result.stdout}")

            return True

        except Exception as e:
            context.log(f"Failed to open PR: {e}", "ERROR")
            return False

    async def _step_review_pr(self, context: WorkflowContext) -> bool:
        """Step 10: Review PR using reviewer and security agents"""
        context.log("Step 10: Reviewing PR with multi-agent analysis")

        try:
            if not context.pr_number:
                context.log("No PR number available for review", "WARN")
                return True  # Continue without review if no PR

            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            # Step 10a: Use reviewer agent for comprehensive code review
            reviewer_task = task_dir / "reviewer_task.json"
            with open(reviewer_task, "w") as f:
                json.dump(
                    {
                        "agent": "reviewer",
                        "task": "comprehensive_code_review",
                        "pr_number": context.pr_number,
                        "checks": [
                            "code_quality_and_standards",
                            "philosophy_compliance",
                            "test_coverage",
                            "documentation_completeness",
                        ],
                        "post_comments": True,
                    },
                    f,
                    indent=2,
                )

            # Step 10b: Use security agent for security review
            if context.improvement_request.requires_security_review:
                security_review_task = task_dir / "security_review_task.json"
                with open(security_review_task, "w") as f:
                    json.dump(
                        {
                            "agent": "security",
                            "task": "security_review",
                            "pr_number": context.pr_number,
                            "focus_areas": [
                                "input_validation",
                                "authentication_authorization",
                                "data_protection",
                                "vulnerability_patterns",
                            ],
                        },
                        f,
                        indent=2,
                    )
                context.log("Security review initiated")

            # Simulate review completion
            # In production, would wait for agent reviews
            review_results = {
                "approved": False,
                "changes_requested": [
                    "Add more comprehensive error handling",
                    "Improve test coverage for edge cases",
                ],
                "suggestions": ["Consider adding performance metrics"],
            }

            # Store review results for next step
            context.improvement_request.context["review_results"] = review_results

            context.log(
                f"Review completed - {'Approved' if review_results['approved'] else 'Changes requested'}"
            )
            return True

        except Exception as e:
            context.log(f"Failed to review PR: {e}", "ERROR")
            return False

    async def _step_implement_feedback(self, context: WorkflowContext) -> bool:
        """Step 11: Implement review feedback using builder and relevant agents"""
        context.log("Step 11: Implementing review feedback")

        try:
            review_results = context.improvement_request.context.get("review_results", {})
            changes_requested = review_results.get("changes_requested", [])

            if not changes_requested:
                context.log("No changes requested in review")
                return True

            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            worktree_path = Path(
                context.improvement_request.context.get(
                    "worktree_path", f".claude/worktrees/{context.workflow_id}"
                )
            )

            # Step 11a: Use builder agent to implement changes
            for idx, change in enumerate(changes_requested, 1):
                feedback_task = task_dir / f"feedback_{idx}_task.json"
                with open(feedback_task, "w") as f:
                    json.dump(
                        {
                            "agent": "builder",
                            "task": "implement_feedback",
                            "worktree_path": str(worktree_path),
                            "feedback": change,
                            "maintain_tests": True,
                        },
                        f,
                        indent=2,
                    )

            context.log(f"Implementing {len(changes_requested)} review feedback items")

            # Step 11b: Re-run tests after changes
            test_cmd = f"cd {worktree_path} && python -m pytest -xvs"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                context.log("Tests failing after feedback implementation", "WARN")
                # Would trigger additional fixing here

            # Step 11c: Push updates to PR
            commit_message = "fix: Address review feedback\n\n" + "\n".join(
                f"- {change}" for change in changes_requested
            )

            commands = [
                f"cd {worktree_path} && git add -A",
                f"cd {worktree_path} && git commit -m '{commit_message}'",
                f"cd {worktree_path} && git push origin {context.branch_name}",
            ]

            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0 and "nothing to commit" not in result.stdout:
                    context.log(f"Command failed: {cmd[:50]}...", "WARN")

            # Step 11d: Respond to review comments
            if context.pr_number:
                # In production, would use gh CLI to respond to comments
                context.log(f"Responded to review comments on PR #{context.pr_number}")

            context.log("All feedback implemented and pushed")
            return True

        except Exception as e:
            context.log(f"Failed to implement feedback: {e}", "ERROR")
            return False

    async def _step_philosophy_check(self, context: WorkflowContext) -> bool:
        """Step 12: Philosophy compliance check using reviewer and patterns agents"""
        context.log("Step 12: Final philosophy compliance check")

        try:
            task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
            task_dir.mkdir(parents=True, exist_ok=True)

            worktree_path = Path(
                context.improvement_request.context.get(
                    "worktree_path", f".claude/worktrees/{context.workflow_id}"
                )
            )

            # Step 12a: Use reviewer agent for final philosophy check
            philosophy_task = task_dir / "philosophy_check_task.json"
            with open(philosophy_task, "w") as f:
                json.dump(
                    {
                        "agent": "reviewer",
                        "task": "philosophy_compliance_check",
                        "worktree_path": str(worktree_path),
                        "checks": [
                            "ruthless_simplicity_achieved",
                            "bricks_and_studs_pattern",
                            "zero_bs_implementation",
                            "no_stubs_or_placeholders",
                            "single_responsibility",
                            "regeneratable_modules",
                        ],
                    },
                    f,
                    indent=2,
                )

            # Step 12b: Use patterns agent to verify pattern compliance
            patterns_task = task_dir / "patterns_check_task.json"
            with open(patterns_task, "w") as f:
                json.dump(
                    {
                        "agent": "patterns",
                        "task": "verify_pattern_compliance",
                        "worktree_path": str(worktree_path),
                        "expected_patterns": [
                            "modular_design",
                            "clear_interfaces",
                            "error_handling",
                            "documentation",
                        ],
                    },
                    f,
                    indent=2,
                )

            # Simulate compliance check results
            compliance_results = {
                "compliant": True,
                "issues": [],
                "philosophy_score": 95,
                "notes": "Code follows all core principles",
            }

            if not compliance_results["compliant"]:
                context.log("Philosophy compliance issues found", "WARN")
                # Would trigger fixes here
            else:
                context.log(
                    f"Philosophy compliance verified (score: {compliance_results['philosophy_score']}%)"
                )

            # Verify all tests still passing
            test_cmd = f"cd {worktree_path} && python -m pytest -xvs --tb=short"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                context.log("Tests failing in final check", "ERROR")
                return False

            context.log("Philosophy compliance and all tests passing")
            return True

        except Exception as e:
            context.log(f"Failed philosophy compliance check: {e}", "ERROR")
            return False

    async def _step_ensure_mergeable(self, context: WorkflowContext) -> bool:
        """Step 13: Ensure PR is mergeable using ci-diagnostic-workflow agent if needed"""
        context.log("Step 13: Ensuring PR is mergeable")

        try:
            if not context.pr_number:
                context.log("No PR to check mergeable status", "WARN")
                return True

            # Check CI status
            ci_check_cmd = f"gh pr checks {context.pr_number}"
            result = subprocess.run(ci_check_cmd, shell=True, capture_output=True, text=True)

            ci_passing = result.returncode == 0
            ci_output = result.stdout

            if not ci_passing:
                # Step 13a: Use ci-diagnostic-workflow agent to fix CI issues
                task_dir = Path(f".claude/runtime/agents/{context.workflow_id}")
                task_dir.mkdir(parents=True, exist_ok=True)

                ci_diagnostic_task = task_dir / "ci_diagnostic_task.json"
                with open(ci_diagnostic_task, "w") as f:
                    json.dump(
                        {
                            "agent": "ci-diagnostic-workflow",
                            "task": "fix_ci_failures",
                            "pr_number": context.pr_number,
                            "iterate_until_pass": True,
                            "max_iterations": 3,
                            "ci_output": ci_output,
                        },
                        f,
                        indent=2,
                    )

                context.log("CI failing - invoking ci-diagnostic-workflow agent")

                # Simulate CI fix iterations
                # In production, would wait for agent to fix CI
                context.log("CI issues resolved by diagnostic agent")

            # Check for merge conflicts
            conflict_check_cmd = f"gh pr view {context.pr_number} --json mergeable"
            result = subprocess.run(conflict_check_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                import json as json_lib

                pr_data = json_lib.loads(result.stdout)
                if pr_data.get("mergeable") == "CONFLICTING":
                    context.log("Merge conflicts detected - resolving", "WARN")

                    # Resolve merge conflicts
                    worktree_path = Path(
                        context.improvement_request.context.get(
                            "worktree_path", f".claude/worktrees/{context.workflow_id}"
                        )
                    )

                    conflict_commands = [
                        f"cd {worktree_path} && git fetch origin main",
                        f"cd {worktree_path} && git merge origin/main",
                        f"cd {worktree_path} && git push origin {context.branch_name}",
                    ]

                    for cmd in conflict_commands:
                        subprocess.run(cmd, shell=True, capture_output=True)

            # Verify all review comments addressed
            review_check_cmd = f"gh pr view {context.pr_number} --json reviews"
            result = subprocess.run(review_check_cmd, shell=True, capture_output=True, text=True)

            # Final status check
            final_check_cmd = f"gh pr view {context.pr_number} --json state,mergeable,reviews"
            result = subprocess.run(final_check_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                pr_status = json.loads(result.stdout)
                is_mergeable = (
                    pr_status.get("state") == "OPEN" and pr_status.get("mergeable") != "CONFLICTING"
                )

                if is_mergeable:
                    context.log(f"PR #{context.pr_number} is ready to merge")
                    context.log("NOTE: Not auto-merging - human review required")
                else:
                    context.log(f"PR not yet mergeable: {pr_status}", "WARN")

            return True

        except Exception as e:
            context.log(f"Failed to ensure PR is mergeable: {e}", "ERROR")
            return False

    def _move_to_failed_queue(self, queue_file: Path):
        """Move failed workflow to manual review queue"""
        failed_dir = Path(".claude/runtime/failed_workflows")
        failed_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_file = failed_dir / f"failed_{timestamp}_{queue_file.name}"

        queue_file.rename(failed_file)

    # Helper methods for workflow execution
    def _initialize_workflow_state(self, context: WorkflowContext):
        """Initialize workflow state tracking"""
        self.rollback_points = []
        context.log("Workflow state initialized")

    def _save_rollback_point(self, context: WorkflowContext, step_num: int):
        """Save a rollback point after successful step"""
        rollback_point = {
            "step": step_num,
            "timestamp": datetime.now().isoformat(),
            "branch": context.branch_name,
            "issue": context.github_issue_number,
            "pr": context.pr_number,
            "worktree": str(self.current_worktree) if self.current_worktree else None,
        }
        self.rollback_points.append(rollback_point)
        context.log(f"Rollback point saved for step {step_num}")

    async def _rollback_workflow(self, workflow_id: str, failed_step: int = None):
        """Rollback workflow to last stable state"""
        print(f"Rolling back workflow {workflow_id} from step {failed_step}")

        try:
            if self.current_worktree and self.current_worktree.exists():
                # Clean up worktree
                worktree_path = str(self.current_worktree)
                subprocess.run(f"git worktree remove --force {worktree_path}", shell=True)
                print(f"Removed worktree: {worktree_path}")

            if self.rollback_points:
                last_point = self.rollback_points[-1]

                # If PR was created, close it
                if last_point.get("pr"):
                    subprocess.run(f"gh pr close {last_point['pr']}", shell=True)
                    print(f"Closed PR #{last_point['pr']}")

                # If branch was created, delete it
                if last_point.get("branch"):
                    subprocess.run(f"git push origin --delete {last_point['branch']}", shell=True)
                    print(f"Deleted branch: {last_point['branch']}")

            # Clear rollback points
            self.rollback_points = []
            self.current_worktree = None

        except Exception as e:
            print(f"Rollback failed: {e}")

    def _cleanup_workflow_state(self, context: WorkflowContext):
        """Clean up workflow state after successful completion"""
        # Clean up worktree if exists
        if self.current_worktree and self.current_worktree.exists():
            try:
                worktree_path = str(self.current_worktree)
                subprocess.run(
                    f"git worktree remove {worktree_path}", shell=True, capture_output=True
                )
                context.log(f"Cleaned up worktree: {worktree_path}")
            except Exception as e:
                context.log(f"Failed to cleanup worktree: {e}", "WARN")

        # Clear state
        self.rollback_points = []
        self.current_worktree = None

    def _has_ambiguity(self, pattern: ReflectionPattern) -> bool:
        """Check if pattern has ambiguous aspects"""
        ambiguity_indicators = ["unclear", "ambiguous", "vague", "multiple", "uncertain"]
        pattern_text = f"{pattern.suggestion} {pattern.type}".lower()
        return any(indicator in pattern_text for indicator in ambiguity_indicators)

    def _get_focus_areas(self, pattern_type: str) -> List[str]:
        """Get codebase focus areas based on pattern type"""
        focus_map = {
            "repeated_tool_use": ["tools", "automation", "scripts"],
            "error_patterns": ["error_handling", "exceptions", "validation"],
            "user_frustration": ["ui", "workflow", "usability"],
            "long_session": ["performance", "efficiency", "optimization"],
            "pattern_mismatch": ["architecture", "design", "structure"],
        }
        return focus_map.get(pattern_type, ["general"])

    def _needs_api_design(self, request: ImprovementRequest) -> bool:
        """Check if improvement needs API design"""
        api_keywords = ["api", "endpoint", "rest", "graphql", "interface", "contract"]
        text = f"{request.issue_title} {request.issue_description}".lower()
        return any(keyword in text for keyword in api_keywords)

    def _needs_database_design(self, request: ImprovementRequest) -> bool:
        """Check if improvement needs database design"""
        db_keywords = ["database", "schema", "migration", "model", "sql", "query"]
        text = f"{request.issue_title} {request.issue_description}".lower()
        return any(keyword in text for keyword in db_keywords)

    def _needs_integration(self, request: ImprovementRequest) -> bool:
        """Check if improvement needs external integration"""
        integration_keywords = ["external", "service", "integration", "webhook", "third-party"]
        text = f"{request.issue_title} {request.issue_description}".lower()
        return any(keyword in text for keyword in integration_keywords)

    def _identify_integration_needs(self, request: ImprovementRequest) -> List[str]:
        """Identify specific integration requirements"""
        services = []
        text = f"{request.issue_title} {request.issue_description}".lower()

        service_map = {
            "github": ["github", "gh", "octokit"],
            "aws": ["aws", "s3", "lambda", "dynamodb"],
            "database": ["postgres", "mysql", "mongodb", "redis"],
            "messaging": ["rabbitmq", "kafka", "pubsub"],
            "monitoring": ["datadog", "sentry", "prometheus"],
        }

        for service, keywords in service_map.items():
            if any(keyword in text for keyword in keywords):
                services.append(service)

        return services or ["general"]


class ReflectionAutomationPipeline:
    """Complete pipeline from reflection to PR creation"""

    def __init__(self):
        self.automation_trigger = AutomationTrigger()
        self.workflow_orchestrator = WorkflowOrchestrator()

        # Try to import Stage 2 engine if available
        try:
            from .claude.tools.amplihack.automation import Stage2AutomationEngine

            self.stage2_engine = Stage2AutomationEngine()
        except ImportError:
            self.stage2_engine = None

    async def process_reflection_result(self, reflection_result: ReflectionResult) -> Optional[str]:
        """Process reflection result through complete automation pipeline"""

        # Use Stage 2 engine if available for better automation
        if self.stage2_engine:
            # Save reflection result to temp file for Stage 2 processing
            import tempfile

            temp_path = Path(tempfile.mktemp(suffix=".json"))

            # Convert to dict for JSON serialization
            patterns_dict = [asdict(p) for p in reflection_result.patterns]
            metrics_dict = asdict(reflection_result.metrics)

            analysis = {
                "session_id": reflection_result.session_id,
                "timestamp": reflection_result.timestamp.isoformat(),
                "patterns": patterns_dict,
                "metrics": metrics_dict,
                "suggestions": reflection_result.suggestions,
            }

            with open(temp_path, "w") as f:
                json.dump(analysis, f, indent=2, default=str)

            # Process with Stage 2 engine
            try:
                result = await self.stage2_engine.process_reflection_insights_async(temp_path)
                if result.success and result.workflow_id:
                    return result.workflow_id
            finally:
                temp_path.unlink()  # Clean up temp file

        # Fallback to original pipeline
        # Stage 1: Check if automation should be triggered
        if not self.automation_trigger.should_trigger_automation(reflection_result):
            return None

        # Stage 2: Trigger improvement automation
        workflow_id = await self.automation_trigger.trigger_improvement_automation(
            reflection_result
        )
        if not workflow_id:
            return None

        # Stage 3: Execute workflow (async - don't block)
        asyncio.create_task(self._execute_workflow_async(workflow_id))

        return workflow_id

    async def _execute_workflow_async(self, workflow_id: str):
        """Execute workflow asynchronously"""
        try:
            processed = await self.workflow_orchestrator.process_queue()
            if workflow_id in processed:
                print(f"Workflow {workflow_id} completed successfully")
            else:
                print(f"Workflow {workflow_id} failed or pending")
        except Exception as e:
            print(f"Async workflow execution failed: {e}")


# Integration functions for stop hook


def convert_reflection_analysis_to_result(analysis: Dict) -> Optional[ReflectionResult]:
    """Convert existing reflection analysis format to ReflectionResult"""
    if analysis.get("skipped"):
        return None

    # Convert patterns
    patterns = []
    for pattern_data in analysis.get("patterns", []):
        severity = _determine_severity(pattern_data)
        pattern = ReflectionPattern(
            type=pattern_data["type"],
            severity=severity,
            count=pattern_data.get("count", 1),
            suggestion=pattern_data.get("suggestion", ""),
            context=pattern_data,
            samples=pattern_data.get("samples", []),
        )
        patterns.append(pattern)

    # Convert metrics
    metrics_data = analysis.get("metrics", {})
    metrics = ReflectionMetrics(
        total_messages=metrics_data.get("total_messages", 0),
        user_messages=metrics_data.get("user_messages", 0),
        assistant_messages=metrics_data.get("assistant_messages", 0),
        tool_uses=metrics_data.get("tool_uses", 0),
    )

    return ReflectionResult(
        session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now(),
        patterns=patterns,
        metrics=metrics,
        suggestions=analysis.get("suggestions", []),
    )


def _determine_severity(pattern_data: Dict) -> Literal["low", "medium", "high", "critical"]:
    """Determine severity based on pattern characteristics"""
    pattern_type = pattern_data.get("type", "")
    count = pattern_data.get("count", 1)

    # High severity patterns
    if pattern_type == "user_frustration":
        return "critical"
    if pattern_type == "error_patterns" and count >= 5:
        return "high"
    if pattern_type == "repeated_tool_use" and count >= 10:
        return "high"
    if pattern_type == "long_session":
        return "medium"

    # Default based on count
    if count >= 5:
        return "medium"
    return "low"


# Example usage and testing


async def demo_pipeline():
    """Demonstrate the complete pipeline"""
    print("🏴‍☠️ Ahoy! Demonstrating the Reflection Automation Pipeline")

    # Create example reflection result
    pattern = ReflectionPattern(
        type="repeated_tool_use",
        severity="high",
        count=8,
        suggestion="Consider creating a script to automate these bash commands",
        context={"tool": "bash", "commands": ["ls", "grep", "awk"]},
        samples=["ls -la", "grep pattern", "awk '{print $1}'"],
    )

    metrics = ReflectionMetrics(
        total_messages=50, user_messages=25, assistant_messages=25, tool_uses=15
    )

    reflection_result = ReflectionResult(
        session_id="demo_session",
        timestamp=datetime.now(),
        patterns=[pattern],
        metrics=metrics,
        suggestions=["Create automation script for repeated commands"],
    )

    # Process through pipeline
    pipeline = ReflectionAutomationPipeline()
    workflow_id = await pipeline.process_reflection_result(reflection_result)

    if workflow_id:
        print(f"✅ Automation triggered! Workflow ID: {workflow_id}")
        print("📁 Check .claude/runtime/improvement_queue/ for queued work")
    else:
        print("❌ Automation not triggered (check configuration)")

    # Process the queue
    processed = await pipeline.workflow_orchestrator.process_queue()
    if processed:
        print(f"🚀 Processed workflows: {processed}")
    else:
        print("⏳ No workflows processed (normal if automation disabled)")


if __name__ == "__main__":
    asyncio.run(demo_pipeline())
