"""
Automation Guard for Stage 2 Engine

Prevents runaway automation and enforces safety limits.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class AutomationGuard:
    """
    Guards against excessive automation and enforces safety limits.

    Tracks automation history and enforces:
    - Daily PR limits
    - Cooldown periods between automations
    - Score thresholds for automation
    - Blacklist for problematic patterns
    """

    # Default safety limits
    DAILY_LIMITS = {
        "max_prs_per_day": 3,
        "max_prs_per_week": 10,
        "max_failed_attempts": 5,
        "cooldown_hours": 4,
        "min_score_threshold": 60,
        "critical_override_threshold": 150,
    }

    # Patterns to never automate
    BLACKLIST_PATTERNS = [
        "database_migration",  # Too risky
        "authentication_change",  # Security sensitive
        "payment_processing",  # Financial risk
        "user_data_handling",  # Privacy sensitive
        "deployment_config",  # Infrastructure risk
    ]

    def __init__(self, config_path: Path = None, state_path: Path = None):
        """Initialize guard with config and state tracking"""
        self.config_path = config_path or Path(".claude/runtime/automation/guard_config.json")
        self.state_path = state_path or Path(".claude/runtime/automation/guard_state.json")

        # Ensure directories exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        # Load configuration and state
        self.config = self._load_config()
        self.state = self._load_state()

        # Check for environment overrides
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load guard configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    config = self.DAILY_LIMITS.copy()
                    config.update(user_config)
                    return config
            except Exception:
                pass

        # Create default config
        with open(self.config_path, "w") as f:
            json.dump(self.DAILY_LIMITS, f, indent=2)
        return self.DAILY_LIMITS.copy()

    def _load_state(self) -> Dict[str, Any]:
        """Load guard state tracking"""
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    return json.load(f)
            except Exception:
                pass

        # Initialize empty state
        return {
            "daily_pr_count": 0,
            "weekly_pr_count": 0,
            "last_pr_timestamp": None,
            "failed_attempts": 0,
            "automation_history": [],
            "last_reset_date": datetime.now().date().isoformat(),
        }

    def _apply_env_overrides(self):
        """Apply environment variable overrides for CI/testing"""
        if os.getenv("AUTOMATION_DISABLED") == "true":
            self.config["max_prs_per_day"] = 0

        if os.getenv("AUTOMATION_TEST_MODE") == "true":
            # Relax limits for testing
            self.config["cooldown_hours"] = 0
            self.config["min_score_threshold"] = 0

    def should_automate(
        self, score: int, pattern_type: str = None, context: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """
        Determine if automation should proceed based on guards.

        Args:
            score: Priority score from PriorityScorer
            pattern_type: Type of pattern being considered
            context: Additional context for decision

        Returns:
            Tuple of (should_automate, reason_message)
        """
        # Update state if needed
        self._check_reset_counters()

        # Check 1: Blacklist
        if pattern_type in self.BLACKLIST_PATTERNS:
            return False, f"Pattern type '{pattern_type}' is blacklisted for safety"

        # Check 2: Score threshold
        min_threshold = self.config["min_score_threshold"]
        if score < min_threshold:
            # Allow critical override
            if score >= self.config["critical_override_threshold"]:
                pass  # Critical priority overrides threshold
            else:
                return False, f"Score {score} below minimum threshold {min_threshold}"

        # Check 3: Daily limit
        daily_limit = self.config["max_prs_per_day"]
        if self.state["daily_pr_count"] >= daily_limit:
            return False, f"Daily PR limit ({daily_limit}) reached"

        # Check 4: Weekly limit
        weekly_limit = self.config["max_prs_per_week"]
        if self.state["weekly_pr_count"] >= weekly_limit:
            return False, f"Weekly PR limit ({weekly_limit}) reached"

        # Check 5: Cooldown period
        if not self._check_cooldown():
            hours = self.config["cooldown_hours"]
            return False, f"Cooldown period ({hours} hours) not elapsed since last PR"

        # Check 6: Failed attempts limit
        max_failed = self.config["max_failed_attempts"]
        if self.state["failed_attempts"] >= max_failed:
            return False, f"Too many failed attempts ({max_failed}), manual intervention required"

        # Check 7: Context-specific guards
        if context:
            context_check = self._check_context_guards(context)
            if not context_check[0]:
                return context_check

        # All checks passed
        return True, "All automation guards passed"

    def _check_reset_counters(self):
        """Reset daily/weekly counters if needed"""
        now = datetime.now()
        last_reset = datetime.fromisoformat(self.state["last_reset_date"])

        # Reset daily counter
        if now.date() > last_reset.date():
            self.state["daily_pr_count"] = 0
            self.state["last_reset_date"] = now.date().isoformat()

        # Reset weekly counter (Monday reset)
        if now.isocalendar()[1] != last_reset.isocalendar()[1]:
            self.state["weekly_pr_count"] = 0

        self._save_state()

    def _check_cooldown(self) -> bool:
        """Check if cooldown period has elapsed"""
        last_pr = self.state.get("last_pr_timestamp")
        if not last_pr:
            return True

        last_pr_time = datetime.fromisoformat(last_pr)
        cooldown_hours = self.config["cooldown_hours"]
        elapsed = datetime.now() - last_pr_time

        return elapsed >= timedelta(hours=cooldown_hours)

    def _check_context_guards(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply context-specific guard rules"""

        # Don't automate during business hours (optional)
        if context.get("respect_business_hours"):
            now = datetime.now()
            if 9 <= now.hour < 17 and now.weekday() < 5:  # Mon-Fri 9-5
                return False, "Automation paused during business hours"

        # Check for user override
        if context.get("user_approved") is False:
            return False, "User has not approved automation for this session"

        # Check for CI environment
        if context.get("ci_environment") and not self.config.get("allow_ci_automation"):
            return False, "Automation disabled in CI environment"

        return True, "Context checks passed"

    def record_automation_attempt(
        self,
        success: bool,
        pr_number: Optional[int] = None,
        pattern_type: str = None,
        error: str = None,
    ):
        """
        Record an automation attempt for tracking.

        Args:
            success: Whether the automation succeeded
            pr_number: PR number if created
            pattern_type: Type of pattern automated
            error: Error message if failed
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "pr_number": pr_number,
            "pattern_type": pattern_type,
            "error": error,
        }

        # Update counters
        if success:
            self.state["daily_pr_count"] += 1
            self.state["weekly_pr_count"] += 1
            self.state["last_pr_timestamp"] = datetime.now().isoformat()
            self.state["failed_attempts"] = 0  # Reset on success
        else:
            self.state["failed_attempts"] += 1

        # Add to history
        self.state["automation_history"].append(record)

        # Keep only last 50 records
        if len(self.state["automation_history"]) > 50:
            self.state["automation_history"] = self.state["automation_history"][-50:]

        self._save_state()

    def get_current_status(self) -> Dict[str, Any]:
        """Get current guard status for monitoring"""
        self._check_reset_counters()

        return {
            "automation_enabled": self.config["max_prs_per_day"] > 0,
            "daily_prs_remaining": self.config["max_prs_per_day"] - self.state["daily_pr_count"],
            "weekly_prs_remaining": self.config["max_prs_per_week"] - self.state["weekly_pr_count"],
            "in_cooldown": not self._check_cooldown(),
            "failed_attempts": self.state["failed_attempts"],
            "last_pr_timestamp": self.state.get("last_pr_timestamp"),
            "config": self.config,
        }

    def reset_failed_attempts(self):
        """Manually reset failed attempts counter"""
        self.state["failed_attempts"] = 0
        self._save_state()

    def update_config(self, updates: Dict[str, Any]):
        """Update guard configuration"""
        self.config.update(updates)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def _save_state(self):
        """Save current state to disk"""
        try:
            with open(self.state_path, "w") as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception:
            pass  # Non-critical, ignore save failures

    def emergency_stop(self):
        """Emergency stop - disable all automation"""
        self.config["max_prs_per_day"] = 0
        self.config["max_prs_per_week"] = 0
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
        print("EMERGENCY STOP: All automation disabled")

    def resume_automation(self):
        """Resume automation after emergency stop"""
        self.config = self.DAILY_LIMITS.copy()
        self.state["failed_attempts"] = 0
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
        self._save_state()
        print("Automation resumed with default limits")
