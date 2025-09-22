# Reflection to Automation Integration Design

## Overview

Arr matey! This spec charts the course for connecting reflection analysis results to automated PR creation through clean, testable interfaces. We be designin' a pipeline that flows like the tide from analysis to action.

## Current State vs Target State

### Current: Manual Review Chain

```
Reflection Analysis → JSON Files → Manual Review → Manual Improvement
```

### Target: Automated Improvement Pipeline

```
Reflection Analysis → Priority Filter → Automation Trigger → Workflow Agent → GitHub PR
```

## Core Integration Interfaces

### 1. ReflectionResult Data Contract

**Purpose**: Standardized format for reflection analysis output

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal

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
        return max(self.patterns, key=lambda p:
            {"critical": 4, "high": 3, "medium": 2, "low": 1}[p.severity])
```

### 2. ImprovementRequest Data Contract

**Purpose**: Standardized request format for improvement workflow

```python
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
    def from_reflection_pattern(cls, pattern: ReflectionPattern, session_context: Dict) -> "ImprovementRequest":
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
            requires_security_review=pattern.type in ["error_patterns"]
        )
```

### 3. AutomationTrigger Interface

**Purpose**: Clean interface for stop hook to trigger Stage 2 automation

```python
class AutomationTrigger:
    """Interface for triggering automated improvements from hooks"""

    def __init__(self, config_path: str = ".claude/runtime/automation_config.json"):
        self.config_path = Path(config_path)
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
        if last_automation and (datetime.now() - last_automation).total_seconds() < 3600:  # 1 hour cooldown
            return False

        return True

    async def trigger_improvement_automation(self, reflection_result: ReflectionResult) -> Optional[str]:
        """Trigger automated improvement process"""
        if not self.should_trigger_automation(reflection_result):
            return None

        # Create improvement request from primary pattern
        primary_pattern = reflection_result.get_primary_issue()
        if not primary_pattern:
            return None

        improvement_request = ImprovementRequest.from_reflection_pattern(
            primary_pattern,
            {"session_id": reflection_result.session_id}
        )

        # Queue for workflow orchestrator
        workflow_id = await self._queue_improvement_request(improvement_request)
        self._record_automation_trigger(reflection_result.session_id, workflow_id)

        return workflow_id

    def _load_config(self) -> Dict:
        """Load automation configuration"""
        if not self.config_path.exists():
            return {"automation_enabled": False}
        return json.loads(self.config_path.read_text())

    def _queue_improvement_request(self, request: ImprovementRequest) -> str:
        """Queue improvement request for workflow orchestrator"""
        # Simple file-based queue for now (scalable later)
        queue_dir = Path(".claude/runtime/improvement_queue")
        queue_dir.mkdir(parents=True, exist_ok=True)

        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        queue_file = queue_dir / f"{workflow_id}.json"

        with open(queue_file, "w") as f:
            json.dump(asdict(request), f, indent=2, default=str)

        return workflow_id
```

### 4. WorkflowOrchestrator Interface

**Purpose**: Manages the 13-step DEFAULT_WORKFLOW.md process for automated improvements

```python
class WorkflowOrchestrator:
    """Orchestrates the 13-step workflow for automated improvements"""

    def __init__(self, workflow_path: str = ".claude/workflow/DEFAULT_WORKFLOW.md"):
        self.workflow_path = Path(workflow_path)
        self.queue_dir = Path(".claude/runtime/improvement_queue")

    async def process_queue(self) -> List[str]:
        """Process all queued improvement requests"""
        processed_workflows = []

        # Get all queued items
        queue_files = list(self.queue_dir.glob("*.json"))

        for queue_file in queue_files:
            try:
                workflow_id = queue_file.stem
                improvement_request = self._load_improvement_request(queue_file)

                # Execute workflow
                success = await self._execute_workflow(workflow_id, improvement_request)

                if success:
                    processed_workflows.append(workflow_id)
                    queue_file.unlink()  # Remove from queue
                else:
                    # Move to failed queue for manual review
                    self._move_to_failed_queue(queue_file)

            except Exception as e:
                print(f"Error processing {queue_file}: {e}")
                self._move_to_failed_queue(queue_file)

        return processed_workflows

    async def _execute_workflow(self, workflow_id: str, request: ImprovementRequest) -> bool:
        """Execute the 13-step workflow for improvement"""
        try:
            # Create workflow execution context
            context = WorkflowContext(
                workflow_id=workflow_id,
                improvement_request=request,
                log_dir=Path(f".claude/runtime/logs/{workflow_id}")
            )

            # Execute each workflow step
            for step_num in range(1, 14):  # Steps 1-13
                success = await self._execute_workflow_step(step_num, context)
                if not success:
                    context.log(f"Workflow failed at step {step_num}")
                    return False

            context.log("Workflow completed successfully")
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
            # ... etc for all 13 steps
        }

        handler = step_handlers.get(step_num)
        if not handler:
            return False

        return await handler(context)

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
```

### 5. GitHubIntegration Interface

**Purpose**: Clean interface for automated GitHub operations

```python
class GitHubIntegration:
    """Clean interface for GitHub operations"""

    def __init__(self):
        self.gh_available = self._check_gh_cli()

    async def create_issue(self, request: ImprovementRequest) -> Optional[int]:
        """Create GitHub issue from improvement request"""
        if not self.gh_available:
            return None

        issue_body = self._format_issue_body(request)

        # Create issue using gh CLI
        result = await self._run_gh_command([
            "issue", "create",
            "--title", request.issue_title,
            "--body", issue_body,
            "--label", f"priority:{request.priority}",
            "--label", f"type:{request.improvement_type}",
            "--label", "automated"
        ])

        if result.success:
            # Extract issue number from result
            return self._extract_issue_number(result.output)
        return None

    async def create_branch(self, issue_number: int, brief_description: str) -> Optional[str]:
        """Create feature branch for improvement"""
        branch_name = f"feat/issue-{issue_number}-{self._slugify(brief_description)}"

        # Create and checkout branch
        result = await self._run_gh_command([
            "repo", "create-branch", branch_name
        ])

        return branch_name if result.success else None

    async def create_pr(self, context: WorkflowContext) -> Optional[int]:
        """Create pull request with reflection context"""
        if not context.branch_name or not context.github_issue_number:
            return None

        pr_body = self._format_pr_body(context)

        result = await self._run_gh_command([
            "pr", "create",
            "--title", f"Automated improvement: {context.improvement_request.issue_title}",
            "--body", pr_body,
            "--head", context.branch_name,
            "--base", "main"
        ])

        if result.success:
            return self._extract_pr_number(result.output)
        return None

    def _format_pr_body(self, context: WorkflowContext) -> str:
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
```

## Data Flow Pipeline Design

### Complete Integration Flow

```python
class ReflectionAutomationPipeline:
    """Complete pipeline from reflection to PR creation"""

    def __init__(self):
        self.automation_trigger = AutomationTrigger()
        self.workflow_orchestrator = WorkflowOrchestrator()
        self.github_integration = GitHubIntegration()

    async def process_reflection_result(self, reflection_result: ReflectionResult) -> Optional[str]:
        """Process reflection result through complete automation pipeline"""

        # Stage 1: Check if automation should be triggered
        if not self.automation_trigger.should_trigger_automation(reflection_result):
            return None

        # Stage 2: Trigger improvement automation
        workflow_id = await self.automation_trigger.trigger_improvement_automation(reflection_result)
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
```

## Stop Hook Integration

### Enhanced Stop Hook with Automation

```python
# Integration point in stop_azure_continuation.py

def enhanced_should_continue(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Enhanced continuation logic with automation integration"""

    # Original continuation logic
    basic_continue = should_continue(messages)  # Existing function

    if basic_continue:
        return {"decision": "continue", "reason": "basic_continuation"}

    # NEW: Check for reflection-based automation
    reflection_result = analyze_session_for_automation(messages)

    if reflection_result and reflection_result.is_automation_worthy():
        # Trigger Stage 2 automation
        pipeline = ReflectionAutomationPipeline()
        workflow_id = asyncio.run(pipeline.process_reflection_result(reflection_result))

        if workflow_id:
            return {
                "decision": "continue",
                "reason": "automation_triggered",
                "instructions": f"Starting automated improvement workflow {workflow_id}. Analyzing detected patterns and creating improvement plan.",
                "workflow_id": workflow_id
            }

    return {"decision": "stop", "reason": "no_continuation_needed"}

def analyze_session_for_automation(messages: List[Dict]) -> Optional[ReflectionResult]:
    """Quick reflection analysis for automation decisions"""
    reflector = SessionReflector()
    analysis = reflector.analyze_session(messages)

    if analysis.get("skipped"):
        return None

    # Convert to ReflectionResult format
    patterns = []
    for pattern_data in analysis.get("patterns", []):
        pattern = ReflectionPattern(
            type=pattern_data["type"],
            severity=_determine_severity(pattern_data),
            count=pattern_data.get("count", 1),
            suggestion=pattern_data.get("suggestion", ""),
            context=pattern_data
        )
        patterns.append(pattern)

    return ReflectionResult(
        session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now(),
        patterns=patterns,
        metrics=ReflectionMetrics(**analysis["metrics"]),
        suggestions=analysis.get("suggestions", [])
    )
```

## Configuration and Control

### Automation Configuration

```json
// .claude/runtime/automation_config.json
{
  "automation_enabled": true,
  "trigger_thresholds": {
    "min_pattern_severity": "medium",
    "min_pattern_count": 2,
    "cooldown_hours": 1
  },
  "workflow_constraints": {
    "max_concurrent_workflows": 2,
    "max_lines_per_improvement": 200,
    "max_components_per_improvement": 3
  },
  "github_integration": {
    "auto_create_issues": true,
    "auto_create_branches": true,
    "auto_create_prs": true,
    "require_manual_merge": true
  }
}
```

## Error Handling and Resilience

### Graceful Degradation

```python
class ResilientAutomationPipeline(ReflectionAutomationPipeline):
    """Enhanced pipeline with robust error handling"""

    async def process_reflection_result(self, reflection_result: ReflectionResult) -> Optional[str]:
        """Process with graceful degradation"""
        try:
            return await super().process_reflection_result(reflection_result)
        except GitHubUnavailableError:
            # Fallback: Save for manual processing
            self._save_for_manual_processing(reflection_result)
            return "manual_queue"
        except WorkflowExecutionError as e:
            # Fallback: Create issue only, skip automation
            issue_num = await self._create_issue_only(reflection_result)
            return f"issue_only_{issue_num}" if issue_num else None
        except Exception as e:
            # Log and continue gracefully
            self._log_error(f"Automation pipeline failed: {e}")
            return None

    def _save_for_manual_processing(self, result: ReflectionResult):
        """Save reflection result for manual review"""
        manual_dir = Path(".claude/runtime/manual_review")
        manual_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manual_file = manual_dir / f"reflection_{timestamp}.json"

        with open(manual_file, "w") as f:
            json.dump(asdict(result), f, indent=2, default=str)
```

## Testing Strategy

### Integration Test Framework

```python
class TestReflectionAutomationIntegration:
    """Test the complete integration pipeline"""

    @pytest.fixture
    def mock_reflection_result(self):
        return ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[
                ReflectionPattern(
                    type="repeated_tool_use",
                    severity="high",
                    count=5,
                    suggestion="Consider creating a script",
                    context={"tool": "bash", "commands": ["ls", "grep", "awk"]}
                )
            ],
            metrics=ReflectionMetrics(
                total_messages=50,
                user_messages=25,
                assistant_messages=25,
                tool_uses=15
            ),
            suggestions=["Create automation script for repeated commands"]
        )

    async def test_complete_pipeline_flow(self, mock_reflection_result):
        """Test the complete flow from reflection to PR"""
        pipeline = ReflectionAutomationPipeline()

        # Should trigger automation
        workflow_id = await pipeline.process_reflection_result(mock_reflection_result)
        assert workflow_id is not None

        # Verify queue file created
        queue_file = Path(f".claude/runtime/improvement_queue/{workflow_id}.json")
        assert queue_file.exists()

        # Verify improvement request format
        with open(queue_file) as f:
            request_data = json.load(f)

        assert request_data["improvement_type"] == "tooling"
        assert request_data["priority"] == "high"
        assert "repeated_tool_use" in request_data["issue_description"]

    def test_automation_trigger_thresholds(self, mock_reflection_result):
        """Test automation trigger logic"""
        trigger = AutomationTrigger()

        # High severity should trigger
        assert trigger.should_trigger_automation(mock_reflection_result)

        # Low severity should not trigger
        mock_reflection_result.patterns[0].severity = "low"
        assert not trigger.should_trigger_automation(mock_reflection_result)
```

## Integration Points Summary

### Clean Interface Contracts

1. **ReflectionResult → ImprovementRequest**: Standardized data transformation
2. **AutomationTrigger**: Clean integration point for stop hook
3. **WorkflowOrchestrator**: Manages 13-step process automation
4. **GitHubIntegration**: Handles all GitHub operations
5. **ReflectionAutomationPipeline**: Orchestrates complete flow

### Key Design Principles Applied

- **Separation of Concerns**: Each interface has one responsibility
- **Testability**: All components can be tested in isolation
- **Graceful Degradation**: Failures don't break the system
- **Configuration-Driven**: Behavior controlled via config files
- **Async-First**: Non-blocking operations where possible

### Future Extensibility

- Plugin architecture for custom automation triggers
- Support for multiple workflow templates
- Integration with additional git hosting services
- Machine learning for pattern recognition improvement

This design provides clean, testable integration points while maintaining the ruthless simplicity philosophy. Each interface can be implemented and tested independently, with clear contracts between components.
