"""
Priority Scorer for Automation Engine

Scores reflection patterns to determine automation priority.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class ScoringResult:
    """Result of pattern scoring"""

    score: int
    category: str
    reasoning: str
    factors: Dict[str, int]


class PriorityScorer:
    """
    Scores patterns based on impact and automation value.

    Higher scores indicate patterns that should be automated first.
    """

    # Weight matrix for different pattern types and characteristics
    PRIORITY_WEIGHTS = {
        # Pattern types with their base scores
        "user_frustration": 80,  # High priority - direct user pain
        "security_vulnerability": 100,  # Critical - security always highest
        "repeated_tool_use": 60,  # Medium - automation opportunity
        "error_patterns": 70,  # High - reliability issues
        "long_session": 40,  # Low-medium - efficiency opportunity
        "performance_bottleneck": 65,  # Medium-high - system health
        "workflow_inefficiency": 55,  # Medium - process improvement
        "missing_feature": 50,  # Medium - functionality gap
        "documentation_gap": 30,  # Low - nice to have
    }

    # Severity multipliers
    SEVERITY_MULTIPLIERS = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}

    # Frequency impact (occurrences)
    FREQUENCY_THRESHOLDS = [
        (20, 50),  # 20+ occurrences: +50 points
        (10, 30),  # 10-19 occurrences: +30 points
        (5, 15),  # 5-9 occurrences: +15 points
        (3, 5),  # 3-4 occurrences: +5 points
    ]

    # Impact scope multipliers
    SCOPE_MULTIPLIERS = {
        "system_wide": 1.5,  # Affects entire system
        "module": 1.2,  # Affects major module
        "component": 1.0,  # Affects single component
        "edge_case": 0.7,  # Edge case scenario
    }

    def __init__(self, history_path: Path = None):
        """Initialize scorer with optional history tracking"""
        self.history_path = history_path or Path(".claude/runtime/automation/scoring_history.json")
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self):
        """Load historical scoring data for learning"""
        if self.history_path.exists():
            try:
                with open(self.history_path) as f:
                    self.history = json.load(f)
            except Exception:
                self.history = {"scores": [], "successful_automations": []}
        else:
            self.history = {"scores": [], "successful_automations": []}

    def score_pattern(self, pattern: Dict[str, Any]) -> ScoringResult:
        """
        Score a single pattern based on multiple factors.

        Args:
            pattern: Pattern dict with type, severity, count, context

        Returns:
            ScoringResult with score, category, reasoning
        """
        factors = {}

        # 1. Base score from pattern type
        pattern_type = pattern.get("type", "unknown")
        base_score = self.PRIORITY_WEIGHTS.get(pattern_type, 25)
        factors["base_type"] = base_score

        # 2. Apply severity multiplier
        severity = pattern.get("severity", "medium")
        severity_mult = self.SEVERITY_MULTIPLIERS.get(severity, 1.0)
        severity_adjusted = int(base_score * severity_mult)
        factors["severity_adjustment"] = severity_adjusted - base_score

        # 3. Add frequency bonus
        count = pattern.get("count", 1)
        frequency_bonus = 0
        for threshold, bonus in self.FREQUENCY_THRESHOLDS:
            if count >= threshold:
                frequency_bonus = bonus
                break
        factors["frequency_bonus"] = frequency_bonus

        # 4. Apply scope multiplier
        context = pattern.get("context", {})
        scope = context.get("scope", "component")
        scope_mult = self.SCOPE_MULTIPLIERS.get(scope, 1.0)

        # 5. Check for urgent indicators
        urgent_bonus = 0
        if "blocking" in str(context).lower():
            urgent_bonus += 30
        if "critical_path" in str(context).lower():
            urgent_bonus += 25
        if pattern.get("user_messages_affected", 0) > 5:
            urgent_bonus += 20
        factors["urgency_bonus"] = urgent_bonus

        # 6. Consider recent similar patterns (avoid redundancy)
        recency_penalty = self._calculate_recency_penalty(pattern_type)
        factors["recency_penalty"] = -recency_penalty

        # Calculate final score
        total_score = int(
            (severity_adjusted + frequency_bonus + urgent_bonus - recency_penalty) * scope_mult
        )

        # Ensure score is within bounds [0, 200]
        total_score = max(0, min(200, total_score))

        # Determine category
        category = self._categorize_score(total_score)

        # Generate reasoning
        reasoning = self._generate_reasoning(pattern, factors, total_score)

        # Record in history
        self._record_scoring(pattern_type, total_score, factors)

        return ScoringResult(
            score=total_score, category=category, reasoning=reasoning, factors=factors
        )

    def score_patterns(self, patterns: List[Dict[str, Any]]) -> List[Tuple[Dict, ScoringResult]]:
        """
        Score multiple patterns and return sorted by priority.

        Args:
            patterns: List of pattern dicts

        Returns:
            List of (pattern, score) tuples sorted by score descending
        """
        scored = []
        for pattern in patterns:
            score_result = self.score_pattern(pattern)
            scored.append((pattern, score_result))

        # Sort by score descending
        scored.sort(key=lambda x: x[1].score, reverse=True)
        return scored

    def _calculate_recency_penalty(self, pattern_type: str) -> int:
        """Calculate penalty if similar pattern was recently automated"""
        penalty = 0

        # Check recent automations in history
        recent_window = 24 * 3600  # 24 hours in seconds
        now = datetime.now().timestamp()

        for automation in self.history.get("successful_automations", []):
            if automation.get("pattern_type") == pattern_type:
                timestamp = automation.get("timestamp", 0)
                age = now - timestamp

                if age < recent_window:
                    # More recent = higher penalty
                    hours_ago = age / 3600
                    penalty = int(30 * (1 - hours_ago / 24))  # Max 30 point penalty
                    break

        return penalty

    def _categorize_score(self, score: int) -> str:
        """Categorize score into priority levels"""
        if score >= 150:
            return "critical_priority"
        elif score >= 100:
            return "high_priority"
        elif score >= 60:
            return "medium_priority"
        elif score >= 30:
            return "low_priority"
        else:
            return "no_action"

    def _generate_reasoning(self, pattern: Dict, factors: Dict, total_score: int) -> str:
        """Generate human-readable reasoning for the score"""
        reasons = []

        pattern_type = pattern.get("type", "unknown")
        severity = pattern.get("severity", "medium")
        count = pattern.get("count", 1)

        # Explain base score
        reasons.append(
            f"Pattern type '{pattern_type}' has base priority {factors.get('base_type', 0)}"
        )

        # Explain severity impact
        if severity != "medium":
            reasons.append(
                f"Severity '{severity}' adjusts score by {factors.get('severity_adjustment', 0)}"
            )

        # Explain frequency
        if count > 1:
            reasons.append(
                f"Occurs {count} times, adding {factors.get('frequency_bonus', 0)} points"
            )

        # Explain urgency
        if factors.get("urgency_bonus", 0) > 0:
            reasons.append(f"Urgent indicators add {factors['urgency_bonus']} points")

        # Explain recency penalty
        if factors.get("recency_penalty", 0) < 0:
            reasons.append(
                f"Recent similar automation reduces score by {abs(factors['recency_penalty'])}"
            )

        # Add conclusion
        category = self._categorize_score(total_score)
        reasons.append(f"Total score {total_score} indicates {category.replace('_', ' ')}")

        return " | ".join(reasons)

    def _record_scoring(self, pattern_type: str, score: int, factors: Dict):
        """Record scoring decision for learning"""
        record = {
            "timestamp": datetime.now().timestamp(),
            "pattern_type": pattern_type,
            "score": score,
            "factors": factors,
        }

        self.history["scores"].append(record)

        # Keep only last 100 scores
        if len(self.history["scores"]) > 100:
            self.history["scores"] = self.history["scores"][-100:]

        # Save to disk
        try:
            with open(self.history_path, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass  # Non-critical, ignore save failures

    def record_successful_automation(self, pattern_type: str, pr_number: int):
        """Record when an automation successfully creates a PR"""
        record = {
            "timestamp": datetime.now().timestamp(),
            "pattern_type": pattern_type,
            "pr_number": pr_number,
        }

        self.history["successful_automations"].append(record)

        # Keep only last 50 automations
        if len(self.history["successful_automations"]) > 50:
            self.history["successful_automations"] = self.history["successful_automations"][-50:]

        # Save to disk
        try:
            with open(self.history_path, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass  # Non-critical
