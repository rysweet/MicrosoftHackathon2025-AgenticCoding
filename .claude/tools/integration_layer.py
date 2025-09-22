#!/usr/bin/env python3
"""
Integration Layer for Reflection Analysis and Automated PR Creation

This module provides clean interfaces between reflection analysis and automation components,
following integration patterns with loose coupling and graceful degradation.
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AutomationResult:
    """Result of automation trigger attempt"""

    success: bool
    workflow_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry


@dataclass
class WorkflowResult:
    """Result of workflow execution"""

    success: bool
    workflow_id: str
    github_issue: Optional[int] = None
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class PRResult:
    """Result of PR creation"""

    success: bool
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None


class CircuitBreaker:
    """Circuit breaker pattern for automation failures"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure = None
        self.is_open = False

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.is_open:
            if time.time() - self.last_failure > self.timeout:
                logger.info("Circuit breaker: Attempting to close")
                self.is_open = False
                self.failure_count = 0
            else:
                raise Exception(
                    f"Circuit breaker is open. Retry after {self.timeout - (time.time() - self.last_failure):.0f}s"
                )

        try:
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )
            self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure = time.time()
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            raise


class RateLimiter:
    """Rate limiter for automation triggers"""

    def __init__(self, max_calls: int = 3, window_seconds: int = 3600):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = []

    def is_allowed(self) -> bool:
        """Check if call is allowed within rate limit"""
        now = time.time()
        # Remove old calls outside window
        self.calls = [
            call_time for call_time in self.calls if now - call_time < self.window_seconds
        ]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def time_until_reset(self) -> int:
        """Time in seconds until rate limit resets"""
        if not self.calls:
            return 0
        oldest_call = min(self.calls)
        return max(0, int(self.window_seconds - (time.time() - oldest_call)))


class ReflectionTrigger:
    """Enhanced reflection trigger with automation criteria checking"""

    def __init__(self, config_path: str = ".claude/runtime/integration_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("circuit_breaker_threshold", 5),
            timeout=self.config.get("circuit_breaker_timeout", 300),
        )
        self.rate_limiter = RateLimiter(
            max_calls=self.config.get("rate_limit_calls", 3),
            window_seconds=self.config.get("rate_limit_window", 3600),
        )

    def check_automation_criteria(self, analysis: Dict) -> bool:
        """Check if reflection analysis meets automation criteria"""
        try:
            # Skip if reflection was disabled
            if analysis.get("skipped"):
                logger.info("Automation criteria check skipped - reflection disabled")
                return False

            # Check rate limiting first
            if not self.rate_limiter.is_allowed():
                time_until_reset = self.rate_limiter.time_until_reset()
                logger.warning(f"Rate limit exceeded. Reset in {time_until_reset}s")
                return False

            patterns = analysis.get("patterns", [])
            if not patterns:
                logger.info("No patterns detected - automation not triggered")
                return False

            # Calculate automation priority score
            score = self._calculate_priority_score(patterns)
            threshold = self.config.get("automation_threshold", 7)

            logger.info(f"Automation priority score: {score} (threshold: {threshold})")

            if score >= threshold:
                logger.info("Automation criteria met")
                return True
            else:
                logger.info("Automation criteria not met")
                return False

        except Exception as e:
            logger.error(f"Error checking automation criteria: {e}")
            return False

    async def trigger_stage2_automation(self, patterns: List[Dict]) -> AutomationResult:
        """Trigger Stage 2 automation with circuit breaker protection"""
        try:
            # Use circuit breaker for protection
            result = await self.circuit_breaker.call(self._execute_automation_trigger, patterns)
            return result
        except Exception as e:
            error_msg = f"Automation trigger failed: {e}"
            logger.error(error_msg)

            # Return failure with retry information
            retry_after = None
            if self.circuit_breaker.is_open:
                retry_after = int(
                    self.circuit_breaker.timeout - (time.time() - self.circuit_breaker.last_failure)
                )

            return AutomationResult(success=False, error=error_msg, retry_after=retry_after)

    async def _execute_automation_trigger(self, patterns: List[Dict]) -> AutomationResult:
        """Execute the actual automation trigger"""
        from .reflection_automation_pipeline import (
            ReflectionAutomationPipeline,
            convert_reflection_analysis_to_result,
        )

        # Convert patterns to reflection analysis format
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "patterns": patterns,
            "metrics": {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "tool_uses": 0,
            },
            "suggestions": [],
        }

        reflection_result = convert_reflection_analysis_to_result(analysis)
        if not reflection_result:
            return AutomationResult(success=False, error="Failed to convert reflection analysis")

        # Trigger the automation pipeline
        pipeline = ReflectionAutomationPipeline()
        workflow_id = await pipeline.process_reflection_result(reflection_result)

        if workflow_id:
            self._record_automation_success(workflow_id, patterns)
            return AutomationResult(
                success=True,
                workflow_id=workflow_id,
                message=f"Automation triggered successfully - workflow {workflow_id}",
            )
        else:
            return AutomationResult(success=False, error="Pipeline did not trigger automation")

    def _calculate_priority_score(self, patterns: List[Dict]) -> int:
        """Calculate priority score for automation decision"""
        score = 0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            count = pattern.get("count", 1)

            # Base scores by pattern type
            type_scores = {
                "user_frustration": 10,  # Critical - always automate
                "error_patterns": 7,  # High priority
                "repeated_tool_use": 6,  # Medium-high priority
                "long_session": 5,  # Medium priority
                "repeated_reads": 4,  # Lower priority
            }

            base_score = type_scores.get(pattern_type, 2)

            # Multiply by frequency (capped at 3x)
            frequency_multiplier = min(3.0, 1.0 + (count - 1) * 0.2)
            pattern_score = int(base_score * frequency_multiplier)

            score += pattern_score
            logger.debug(
                f"Pattern {pattern_type}: base={base_score}, freq={frequency_multiplier}, score={pattern_score}"
            )

        return score

    def _load_config(self) -> Dict:
        """Load integration configuration with defaults"""
        default_config = {
            "automation_enabled": True,
            "automation_threshold": 7,
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 300,
            "rate_limit_calls": 3,
            "rate_limit_window": 3600,
            "duplicate_prevention_window": 1800,  # 30 minutes
            "max_concurrent_workflows": 2,
        }

        if not self.config_path.exists():
            self.config_path.write_text(json.dumps(default_config, indent=2))
            return default_config

        try:
            config = json.loads(self.config_path.read_text())
            # Merge with defaults for missing keys
            return {**default_config, **config}
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading config, using defaults: {e}")
            return default_config

    def _record_automation_success(self, workflow_id: str, patterns: List[Dict]):
        """Record successful automation trigger"""
        history_file = Path(".claude/runtime/automation_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "pattern_count": len(patterns),
            "pattern_types": [p.get("type") for p in patterns],
        }

        try:
            if history_file.exists():
                history = json.loads(history_file.read_text())
            else:
                history = []

            history.append(entry)

            # Keep only last 100 entries
            history = history[-100:]

            history_file.write_text(json.dumps(history, indent=2))
            logger.info(f"Recorded automation trigger: {workflow_id}")

        except Exception as e:
            logger.error(f"Failed to record automation history: {e}")


class WorkflowIntegration:
    """Integration with improvement-workflow agent and 13-step process"""

    def __init__(self):
        self.workflow_path = Path(".claude/workflow/DEFAULT_WORKFLOW.md")
        self.circuit_breaker = CircuitBreaker()

    async def execute_improvement_workflow(self, task_description: str) -> WorkflowResult:
        """Execute improvement workflow with robust error handling"""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()

        try:
            result = await self.circuit_breaker.call(
                self._execute_workflow_steps, workflow_id, task_description
            )

            duration = time.time() - start_time
            return WorkflowResult(
                success=True,
                workflow_id=workflow_id,
                github_issue=result.get("github_issue"),
                branch_name=result.get("branch_name"),
                pr_number=result.get("pr_number"),
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Workflow execution failed: {e}")
            return WorkflowResult(
                success=False, workflow_id=workflow_id, error=str(e), duration_seconds=duration
            )

    async def _execute_workflow_steps(self, workflow_id: str, task_description: str) -> Dict:
        """Execute the actual workflow steps"""
        # This is a simplified implementation
        # In a full implementation, this would:
        # 1. Parse the DEFAULT_WORKFLOW.md
        # 2. Execute each step using appropriate agents
        # 3. Handle step failures and rollbacks
        # 4. Track progress and log decisions

        log_dir = Path(f".claude/runtime/logs/{workflow_id}")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Log workflow start
        self._log_workflow_step(log_dir, "START", f"Beginning workflow for: {task_description}")

        # Simulate workflow execution (replace with actual implementation)
        await asyncio.sleep(0.1)  # Simulate work

        # For demonstration, return mock results
        result = {
            "github_issue": None,  # Would create actual issue
            "branch_name": None,  # Would create actual branch
            "pr_number": None,  # Would create actual PR
        }

        self._log_workflow_step(log_dir, "COMPLETE", "Workflow completed successfully")
        return result

    def _log_workflow_step(self, log_dir: Path, step: str, message: str):
        """Log workflow step with timestamp"""
        log_file = log_dir / "workflow_steps.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {step}: {message}\n")

    async def create_github_pr(self, workflow_result: WorkflowResult) -> PRResult:
        """Create GitHub PR from workflow result"""
        if not workflow_result.success:
            return PRResult(success=False, error="Cannot create PR from failed workflow")

        try:
            # Check if gh CLI is available
            if not self._check_gh_cli():
                return PRResult(success=False, error="GitHub CLI not available")

            # For demonstration - in real implementation would create actual PR
            pr_number = None  # await self._create_actual_pr(workflow_result)
            pr_url = f"https://github.com/repo/pull/{pr_number}" if pr_number else None

            return PRResult(
                success=bool(pr_number),
                pr_number=pr_number,
                pr_url=pr_url,
                error="PR creation not implemented in demo" if not pr_number else None,
            )

        except Exception as e:
            logger.error(f"PR creation failed: {e}")
            return PRResult(success=False, error=str(e))

    def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available"""
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False


class DuplicatePrevention:
    """Prevent duplicate PR creation for similar patterns"""

    def __init__(self, window_minutes: int = 30):
        self.window_minutes = window_minutes
        self.state_file = Path(".claude/runtime/duplicate_prevention.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def is_duplicate(self, patterns: List[Dict]) -> bool:
        """Check if similar patterns were recently processed"""
        try:
            if not self.state_file.exists():
                return False

            state = json.loads(self.state_file.read_text())
            recent_cutoff = datetime.now() - timedelta(minutes=self.window_minutes)

            # Check recent automations
            for entry in state.get("recent_automations", []):
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > recent_cutoff:
                    # Check pattern similarity
                    if self._patterns_similar(patterns, entry.get("patterns", [])):
                        logger.info(
                            f"Duplicate pattern detected within {self.window_minutes} minutes"
                        )
                        return True

            return False

        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return False

    def record_automation(self, patterns: List[Dict], workflow_id: str):
        """Record automation to prevent duplicates"""
        try:
            if self.state_file.exists():
                state = json.loads(self.state_file.read_text())
            else:
                state = {"recent_automations": []}

            # Add new entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "workflow_id": workflow_id,
                "patterns": patterns,
            }

            state["recent_automations"].append(entry)

            # Clean old entries
            recent_cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
            state["recent_automations"] = [
                e
                for e in state["recent_automations"]
                if datetime.fromisoformat(e["timestamp"]) > recent_cutoff
            ]

            self.state_file.write_text(json.dumps(state, indent=2))

        except Exception as e:
            logger.error(f"Error recording automation: {e}")

    def _patterns_similar(self, patterns1: List[Dict], patterns2: List[Dict]) -> bool:
        """Check if two pattern sets are similar"""
        if len(patterns1) != len(patterns2):
            return False

        types1 = sorted([p.get("type", "") for p in patterns1])
        types2 = sorted([p.get("type", "") for p in patterns2])

        return types1 == types2


class IntegrationLayer:
    """Main integration layer orchestrating all components"""

    def __init__(self):
        self.reflection_trigger = ReflectionTrigger()
        self.workflow_integration = WorkflowIntegration()
        self.duplicate_prevention = DuplicatePrevention()

    async def process_reflection_analysis(self, analysis: Dict) -> Optional[AutomationResult]:
        """Main entry point for processing reflection analysis"""
        try:
            logger.info("Processing reflection analysis for automation")

            # Check automation criteria
            if not self.reflection_trigger.check_automation_criteria(analysis):
                logger.info("Automation criteria not met")
                return None

            patterns = analysis.get("patterns", [])

            # Check for duplicates
            if self.duplicate_prevention.is_duplicate(patterns):
                logger.info("Duplicate patterns detected - skipping automation")
                return AutomationResult(
                    success=False,
                    error="Duplicate patterns detected",
                    message="Similar automation was recently triggered",
                )

            # Trigger automation
            result = await self.reflection_trigger.trigger_stage2_automation(patterns)

            # Record successful automation
            if result.success and result.workflow_id:
                self.duplicate_prevention.record_automation(patterns, result.workflow_id)
                logger.info(f"Automation successful: {result.workflow_id}")

            return result

        except Exception as e:
            logger.error(f"Integration layer error: {e}")
            return AutomationResult(success=False, error=f"Integration layer failed: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of integration components"""
        return {
            "circuit_breaker_open": self.reflection_trigger.circuit_breaker.is_open,
            "rate_limit_remaining": (
                self.reflection_trigger.rate_limiter.max_calls
                - len(self.reflection_trigger.rate_limiter.calls)
            ),
            "rate_limit_reset_seconds": self.reflection_trigger.rate_limiter.time_until_reset(),
            "workflow_integration_available": True,
            "github_cli_available": self.workflow_integration._check_gh_cli(),
        }


# Example usage and testing functions


async def test_integration_layer():
    """Test the integration layer with sample data"""
    print("🧪 Testing Integration Layer")

    integration = IntegrationLayer()

    # Test health status
    health = integration.get_health_status()
    print(f"Health Status: {json.dumps(health, indent=2)}")

    # Test with sample reflection analysis
    sample_analysis = {
        "timestamp": datetime.now().isoformat(),
        "patterns": [
            {
                "type": "repeated_tool_use",
                "tool": "bash",
                "count": 8,
                "suggestion": "Consider creating a script to automate these bash commands",
            },
            {
                "type": "error_patterns",
                "count": 5,
                "suggestion": "Investigate root cause and add better error handling",
            },
        ],
        "metrics": {
            "total_messages": 50,
            "user_messages": 25,
            "assistant_messages": 25,
            "tool_uses": 15,
        },
        "suggestions": ["Create automation script", "Improve error handling"],
    }

    # Process the analysis
    result = await integration.process_reflection_analysis(sample_analysis)

    if result:
        print(f"✅ Automation Result: {result}")
    else:
        print("❌ No automation triggered")

    return result


if __name__ == "__main__":
    asyncio.run(test_integration_layer())
