"""Pattern extraction module for analyzing claude-trace entries.

This module analyzes claude-trace entries to identify improvement patterns in:
- Code improvements (bug fixes, performance, security)
- Prompt improvements (clarity, context, specificity)
- System fixes (connection, memory, API issues)

Each analyzer focuses on a specific domain with specialized detection logic.
"""

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .jsonl_parser import ParsedEntry


@dataclass
class ImprovementPattern:
    """Represents an identified improvement pattern.

    Attributes:
        id: Unique identifier for the pattern
        type: Main category (code_improvement, prompt_improvement, system_fix)
        subtype: Specific subcategory (bug_fix, performance, clarity, etc.)
        description: Human-readable description of the improvement
        confidence: Confidence score (0.0 to 1.0)
        evidence: List of evidence supporting this pattern
        suggested_action: Recommended action for this improvement
        source_entries: Source trace entries that led to this pattern
        metadata: Additional pattern-specific metadata
    """

    id: str
    type: str
    subtype: str
    description: str
    confidence: float
    evidence: List[str]
    suggested_action: str
    source_entries: List[ParsedEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate pattern fields after initialization."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("id must be a non-empty string")

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access for backward compatibility."""
        return getattr(self, key)

        if not self.type or not isinstance(self.type, str):
            raise ValueError("type must be a non-empty string")

        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary representation.

        Returns:
            Dictionary representation of the pattern
        """
        return {
            "id": self.id,
            "type": self.type,
            "subtype": self.subtype,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "suggested_action": self.suggested_action,
            "metadata": self.metadata,
            "entry_count": len(self.source_entries),
        }


class BaseAnalyzer(ABC):
    """Base class for specialized pattern analyzers."""

    def __init__(self):
        """Initialize base analyzer."""
        self.name = self.__class__.__name__

    @abstractmethod
    def analyze(self, entries: List[ParsedEntry]) -> List[ImprovementPattern]:
        """Analyze entries to extract patterns.

        Args:
            entries: List of parsed entries to analyze

        Returns:
            List of identified improvement patterns
        """
        pass

    def _generate_pattern_id(self, content: str) -> str:
        """Generate unique ID for a pattern based on content.

        Args:
            content: Content to hash for ID generation

        Returns:
            Unique pattern ID
        """
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{self.name.lower()}_{content_hash}"


class CodeImprovementAnalyzer(BaseAnalyzer):
    """Analyzes entries for code improvement patterns.

    Identifies:
    - Bug fixes (syntax errors, logic errors, runtime errors)
    - Performance improvements (optimization, caching, algorithms)
    - Security fixes (vulnerabilities, input validation, access control)
    - Code quality improvements (refactoring, style, documentation)
    """

    def __init__(self):
        super().__init__()
        self.patterns = {
            "bug_fix": re.compile(
                r"\b(?:fix|bug|error|exception|crash|fail|syntax|runtime|logic|null|undefined|index)\b",
                re.IGNORECASE,
            ),
            "performance": re.compile(
                r"\b(?:optimize|performance|speed|faster|slow|cache|algorithm|complexity|efficiency|bottleneck)\b",
                re.IGNORECASE,
            ),
            "security": re.compile(
                r"\b(?:security|vulnerability|exploit|injection|xss|csrf|authentication|authorization|sanitize|validate|escape|secure)\b",
                re.IGNORECASE,
            ),
        }

    def analyze(self, entries: List[ParsedEntry]) -> List[ImprovementPattern]:
        """Analyze entries for code improvement patterns.

        Args:
            entries: List of parsed entries to analyze

        Returns:
            List of identified code improvement patterns
        """
        patterns = []

        for entry in entries:
            # Skip non-completion entries
            if entry.entry_type != "completion":
                continue

            data = entry.data
            text_content = self._extract_text_content(data)

            # Check for each improvement type
            for improvement_type, pattern_regex in self.patterns.items():
                if pattern_regex.search(text_content):
                    pattern = self._create_code_pattern(entry, improvement_type, text_content)
                    if pattern:
                        patterns.append(pattern)

        return self._deduplicate_patterns(patterns)

    def _extract_text_content(self, data: Dict[str, Any]) -> str:
        """Extract relevant text content from entry data.

        Args:
            data: Entry data dictionary

        Returns:
            Combined text content for analysis
        """
        text_parts = []

        # Common fields to analyze
        text_fields = [
            "prompt",
            "completion",
            "code_before",
            "code_after",
            "error_message",
            "fix_applied",
            "description",
        ]

        for field_name in text_fields:
            if field_name in data and isinstance(data[field_name], str):
                text_parts.append(data[field_name])

        return " ".join(text_parts).lower()

    def _create_code_pattern(
        self, entry: ParsedEntry, improvement_type: str, content: str
    ) -> Optional[ImprovementPattern]:
        """Create a code improvement pattern from an entry.

        Args:
            entry: Source entry
            improvement_type: Type of improvement (bug_fix, performance, security)
            content: Text content that matched patterns

        Returns:
            ImprovementPattern or None if pattern creation fails
        """
        try:
            # Generate evidence
            evidence = []
            data = entry.data

            if "code_before" in data and "code_after" in data:
                evidence.append("Before/after code comparison")

            if "performance_gain" in data:
                evidence.append(f"Performance improvement: {data['performance_gain']}")

            if "test_results" in data:
                evidence.append("Test results validation")

            # Generate description based on improvement type and data
            description = self._generate_description(improvement_type, data)

            # Calculate confidence based on evidence quality
            confidence = self._calculate_confidence(improvement_type, data, evidence)

            # Generate suggested action
            suggested_action = self._generate_suggested_action(improvement_type, data)

            pattern = ImprovementPattern(
                id=self._generate_pattern_id(f"{improvement_type}_{content[:100]}"),
                type="code_improvement",
                subtype=improvement_type,
                description=description,
                confidence=confidence,
                evidence=evidence,
                suggested_action=suggested_action,
                source_entries=[entry],
                metadata={
                    "improvement_type": improvement_type,
                    "timestamp": entry.timestamp,
                    "entry_type": entry.entry_type,
                },
            )

            return pattern

        except Exception:
            # Return None if pattern creation fails
            return None

    def _generate_description(self, improvement_type: str, data: Dict[str, Any]) -> str:
        """Generate human-readable description for the improvement.

        Args:
            improvement_type: Type of improvement
            data: Entry data

        Returns:
            Description string
        """
        if improvement_type == "bug_fix":
            if "syntax" in str(data).lower():
                return "Fixed syntax error in code"
            elif "logic" in str(data).lower():
                return "Fixed logic error in code"
            else:
                return "Fixed bug in code"

        elif improvement_type == "performance":
            if "caching" in str(data).lower():
                return "Improved performance using caching"
            elif "algorithm" in str(data).lower():
                return "Optimized algorithm for better performance"
            else:
                return "General performance improvement"

        elif improvement_type == "security":
            if "injection" in str(data).lower():
                return "Fixed security vulnerability (injection)"
            elif "validation" in str(data).lower():
                return "Improved input validation for security"
            else:
                return "Security improvement applied"

        return f"Code improvement: {improvement_type}"

    def _calculate_confidence(
        self, improvement_type: str, data: Dict[str, Any], evidence: List[str]
    ) -> float:
        """Calculate confidence score for the pattern.

        Args:
            improvement_type: Type of improvement
            data: Entry data
            evidence: List of evidence

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.7

        # Boost confidence based on evidence quality
        if "Before/after code comparison" in evidence:
            base_confidence += 0.15

        if "Test results validation" in evidence:
            base_confidence += 0.1

        if "Performance improvement" in str(evidence):
            base_confidence += 0.05

        # Specific data indicators
        if any(key in data for key in ["code_before", "code_after", "fix_applied"]):
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _generate_suggested_action(self, improvement_type: str, data: Dict[str, Any]) -> str:
        """Generate suggested action for the improvement.

        Args:
            improvement_type: Type of improvement
            data: Entry data

        Returns:
            Suggested action string
        """
        if improvement_type == "bug_fix":
            return "Review and apply bug fix to similar code patterns"
        elif improvement_type == "performance":
            return "Evaluate applying performance optimization to similar code"
        elif improvement_type == "security":
            return "Review security fix and apply to similar vulnerabilities"
        else:
            return f"Review and consider applying {improvement_type} improvement"

    def _deduplicate_patterns(self, patterns: List[ImprovementPattern]) -> List[ImprovementPattern]:
        """Remove duplicate patterns based on content similarity.

        Args:
            patterns: List of patterns to deduplicate

        Returns:
            Deduplicated list of patterns
        """
        seen_descriptions = set()
        unique_patterns = []

        for pattern in patterns:
            # Use description and subtype as deduplication key
            dedup_key = f"{pattern.subtype}:{pattern.description}"

            if dedup_key not in seen_descriptions:
                seen_descriptions.add(dedup_key)
                unique_patterns.append(pattern)

        return unique_patterns


class PromptImprovementAnalyzer(BaseAnalyzer):
    """Analyzes entries for prompt improvement patterns.

    Identifies:
    - Clarity improvements (vague to specific prompts)
    - Context improvements (missing to complete context)
    - Specificity improvements (general to detailed requests)
    """

    def __init__(self):
        super().__init__()
        self.patterns = {
            "clarity": re.compile(
                r"\b(?:unclear|vague|confusing|ambiguous|need.*specific|more.*detail|clarification)\b",
                re.IGNORECASE,
            ),
            "context": re.compile(
                r"\b(?:context|background|missing.*information|need.*to.*see|show.*me.*the|provide.*code)\b",
                re.IGNORECASE,
            ),
            "specificity": re.compile(
                r"\b(?:too.*general|more.*specific|exactly.*what|which.*part|what.*kind|be.*precise)\b",
                re.IGNORECASE,
            ),
        }

    def analyze(self, entries: List[ParsedEntry]) -> List[ImprovementPattern]:
        """Analyze entries for prompt improvement patterns.

        Args:
            entries: List of parsed entries to analyze

        Returns:
            List of identified prompt improvement patterns
        """
        patterns = []

        for entry in entries:
            if entry.entry_type != "completion":
                continue

            data = entry.data
            text_content = self._extract_prompt_content(data)

            # Check for prompt improvement indicators
            for improvement_type, pattern_regex in self.patterns.items():
                if pattern_regex.search(text_content):
                    pattern = self._create_prompt_pattern(entry, improvement_type, text_content)
                    if pattern:
                        patterns.append(pattern)

            # Check for explicit improvement indicators
            if self._has_explicit_prompt_improvement(data):
                pattern = self._create_explicit_prompt_pattern(entry, data)
                if pattern:
                    patterns.append(pattern)

        return self._deduplicate_patterns(patterns)

    def _extract_prompt_content(self, data: Dict[str, Any]) -> str:
        """Extract prompt-related content from entry data."""
        text_parts = []
        prompt_fields = [
            "prompt",
            "completion",
            "clarification_request",
            "improved_prompt",
            "follow_up_prompt",
        ]

        for field_name in prompt_fields:
            if field_name in data and isinstance(data[field_name], str):
                text_parts.append(data[field_name])

        return " ".join(text_parts).lower()

    def _has_explicit_prompt_improvement(self, data: Dict[str, Any]) -> bool:
        """Check for explicit prompt improvement indicators."""
        improvement_indicators = [
            "clarification_request",
            "clarification_needed",
            "context_missing",
            "specificity_needed",
            "improved_prompt",
            "follow_up_prompt",
        ]
        return any(key in data for key in improvement_indicators)

    def _create_prompt_pattern(
        self, entry: ParsedEntry, improvement_type: str, content: str
    ) -> Optional[ImprovementPattern]:
        """Create a prompt improvement pattern."""
        try:
            data = entry.data
            evidence = []

            # Gather evidence
            if "improved_prompt" in data:
                evidence.append("Improved prompt example provided")

            if "follow_up_prompt" in data:
                evidence.append("Follow-up prompt shows improvement")

            if any(key in data for key in ["clarification_request", "context_missing"]):
                evidence.append("Explicit improvement need identified")

            description = self._generate_prompt_description(improvement_type, data)
            confidence = self._calculate_prompt_confidence(improvement_type, data, evidence)
            suggested_action = self._generate_prompt_action(improvement_type)

            pattern = ImprovementPattern(
                id=self._generate_pattern_id(f"prompt_{improvement_type}_{content[:50]}"),
                type="prompt_improvement",
                subtype=improvement_type,
                description=description,
                confidence=confidence,
                evidence=evidence,
                suggested_action=suggested_action,
                source_entries=[entry],
                metadata={"improvement_type": improvement_type, "timestamp": entry.timestamp},
            )

            return pattern

        except Exception:
            return None

    def _create_explicit_prompt_pattern(
        self, entry: ParsedEntry, data: Dict[str, Any]
    ) -> Optional[ImprovementPattern]:
        """Create pattern from explicit prompt improvement indicators."""
        try:
            improvement_type = "clarity"
            if "context_missing" in data:
                improvement_type = "context"
            elif "specificity_needed" in data:
                improvement_type = "specificity"

            evidence = ["Explicit improvement indicator found"]
            if "improved_prompt" in data:
                evidence.append("Improved prompt provided")

            pattern = ImprovementPattern(
                id=self._generate_pattern_id(f"explicit_prompt_{improvement_type}"),
                type="prompt_improvement",
                subtype=improvement_type,
                description=f"Prompt {improvement_type} improvement identified",
                confidence=0.85,
                evidence=evidence,
                suggested_action=self._generate_prompt_action(improvement_type),
                source_entries=[entry],
                metadata={"explicit_indicator": True},
            )

            return pattern

        except Exception:
            return None

    def _generate_prompt_description(self, improvement_type: str, data: Dict[str, Any]) -> str:
        """Generate description for prompt improvement."""
        if improvement_type == "clarity":
            return "Prompt clarity improvement: vague to specific request"
        elif improvement_type == "context":
            return "Prompt context improvement: added missing information"
        elif improvement_type == "specificity":
            return "Prompt specificity improvement: general to detailed request"
        else:
            return f"Prompt {improvement_type} improvement"

    def _calculate_prompt_confidence(
        self, improvement_type: str, data: Dict[str, Any], evidence: List[str]
    ) -> float:
        """Calculate confidence for prompt pattern."""
        base_confidence = 0.6

        if "Improved prompt example provided" in evidence:
            base_confidence += 0.2

        if "Explicit improvement need identified" in evidence:
            base_confidence += 0.15

        if len(evidence) > 1:
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _generate_prompt_action(self, improvement_type: str) -> str:
        """Generate suggested action for prompt improvement."""
        actions = {
            "clarity": "Create prompt templates for clearer requests",
            "context": "Develop context-gathering guidelines",
            "specificity": "Create specificity checklists for prompts",
        }
        return actions.get(improvement_type, "Review and improve prompt patterns")

    def _deduplicate_patterns(self, patterns: List[ImprovementPattern]) -> List[ImprovementPattern]:
        """Deduplicate prompt improvement patterns."""
        seen_types = set()
        unique_patterns = []

        for pattern in patterns:
            dedup_key = f"{pattern.subtype}:{pattern.description[:50]}"

            if dedup_key not in seen_types:
                seen_types.add(dedup_key)
                unique_patterns.append(pattern)

        return unique_patterns


class SystemFixAnalyzer(BaseAnalyzer):
    """Analyzes entries for system fix patterns.

    Identifies:
    - Connection fixes (timeouts, retries, network issues)
    - Memory fixes (out of memory, memory leaks, optimization)
    - API fixes (rate limiting, error handling, integration issues)
    """

    def __init__(self):
        super().__init__()
        self.patterns = {
            "connection": re.compile(
                r"\b(?:connection|timeout|retry|network|socket|connect.*fail|timeout.*error|network.*error|exponential.*backoff|retry.*logic)\b",
                re.IGNORECASE,
            ),
            "memory": re.compile(
                r"\b(?:memory|out.*of.*memory|memory.*leak|heap|memory.*usage|memory.*optimization|streaming|garbage.*collection|memory.*limit)\b",
                re.IGNORECASE,
            ),
            "api": re.compile(
                r"\b(?:api|rate.*limit|quota|throttle|api.*error|service.*unavailable|429|rate.*limiting|api.*timeout)\b",
                re.IGNORECASE,
            ),
        }

    def analyze(self, entries: List[ParsedEntry]) -> List[ImprovementPattern]:
        """Analyze entries for system fix patterns.

        Args:
            entries: List of parsed entries to analyze

        Returns:
            List of identified system fix patterns
        """
        patterns = []

        for entry in entries:
            # Focus on error entries and completions with system issues
            if entry.entry_type not in ["error", "completion"]:
                continue

            data = entry.data
            text_content = self._extract_system_content(data)

            # Check for system fix patterns
            for fix_type, pattern_regex in self.patterns.items():
                if pattern_regex.search(text_content):
                    pattern = self._create_system_pattern(entry, fix_type, text_content)
                    if pattern:
                        patterns.append(pattern)

            # Check for explicit system fix indicators
            if self._has_explicit_system_fix(data):
                pattern = self._create_explicit_system_pattern(entry, data)
                if pattern:
                    patterns.append(pattern)

        return self._deduplicate_patterns(patterns)

    def _extract_system_content(self, data: Dict[str, Any]) -> str:
        """Extract system-related content from entry data."""
        text_parts = []
        system_fields = [
            "error_message",
            "error_type",
            "fix_applied",
            "resolution",
            "completion",
            "prompt",
        ]

        for field_name in system_fields:
            if field_name in data and isinstance(data[field_name], str):
                text_parts.append(data[field_name])

        return " ".join(text_parts).lower()

    def _has_explicit_system_fix(self, data: Dict[str, Any]) -> bool:
        """Check for explicit system fix indicators."""
        fix_indicators = [
            "fix_applied",
            "resolution",
            "success",
            "memory_usage_reduced",
            "api_stability_improved",
            "connection_improved",
        ]
        return any(key in data and data[key] for key in fix_indicators)

    def _create_system_pattern(
        self, entry: ParsedEntry, fix_type: str, content: str
    ) -> Optional[ImprovementPattern]:
        """Create a system fix pattern."""
        try:
            data = entry.data
            evidence = []

            # Gather evidence
            if "fix_applied" in data:
                evidence.append(f"Fix applied: {data['fix_applied']}")

            if "success" in data and data["success"]:
                evidence.append("Fix verified successful")

            if entry.entry_type == "error":
                evidence.append("Error entry with resolution")

            # Type-specific evidence
            if fix_type == "memory" and "memory_usage_reduced" in data:
                evidence.append(f"Memory usage reduced: {data['memory_usage_reduced']}")

            if fix_type == "api" and "api_stability_improved" in data:
                evidence.append("API stability improvement verified")

            description = self._generate_system_description(fix_type, data)
            confidence = self._calculate_system_confidence(fix_type, data, evidence)
            suggested_action = self._generate_system_action(fix_type)

            pattern = ImprovementPattern(
                id=self._generate_pattern_id(f"system_{fix_type}_{content[:50]}"),
                type="system_fix",
                subtype=fix_type,
                description=description,
                confidence=confidence,
                evidence=evidence,
                suggested_action=suggested_action,
                source_entries=[entry],
                metadata={
                    "fix_type": fix_type,
                    "timestamp": entry.timestamp,
                    "entry_type": entry.entry_type,
                },
            )

            return pattern

        except Exception:
            return None

    def _create_explicit_system_pattern(
        self, entry: ParsedEntry, data: Dict[str, Any]
    ) -> Optional[ImprovementPattern]:
        """Create pattern from explicit system fix indicators."""
        try:
            # Determine fix type from data
            fix_type = "connection"
            if any(key in data for key in ["memory_usage_reduced", "out_of_memory"]):
                fix_type = "memory"
            elif any(key in data for key in ["api_stability_improved", "rate_limit"]):
                fix_type = "api"

            evidence = ["Explicit system fix indicator found"]
            if "fix_applied" in data:
                evidence.append(f"Fix description: {data['fix_applied']}")

            pattern = ImprovementPattern(
                id=self._generate_pattern_id(f"explicit_system_{fix_type}"),
                type="system_fix",
                subtype=fix_type,
                description=f"System {fix_type} fix applied successfully",
                confidence=0.9,
                evidence=evidence,
                suggested_action=self._generate_system_action(fix_type),
                source_entries=[entry],
                metadata={"explicit_indicator": True},
            )

            return pattern

        except Exception:
            return None

    def _generate_system_description(self, fix_type: str, data: Dict[str, Any]) -> str:
        """Generate description for system fix."""
        descriptions = {
            "connection": "Connection stability fix applied",
            "memory": "Memory usage optimization implemented",
            "api": "API reliability improvement applied",
        }

        base_desc = descriptions.get(fix_type, f"System {fix_type} fix")

        # Add specific details if available
        if "fix_applied" in data:
            return f"{base_desc}: {data['fix_applied'][:100]}"

        return base_desc

    def _calculate_system_confidence(
        self, fix_type: str, data: Dict[str, Any], evidence: List[str]
    ) -> float:
        """Calculate confidence for system fix pattern."""
        base_confidence = 0.7

        if "Fix verified successful" in evidence:
            base_confidence += 0.15

        if any("reduced" in e or "improved" in e for e in evidence):
            base_confidence += 0.1

        if len(evidence) > 2:
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _generate_system_action(self, fix_type: str) -> str:
        """Generate suggested action for system fix."""
        actions = {
            "connection": "Review connection handling patterns and apply fixes",
            "memory": "Audit memory usage patterns and apply optimizations",
            "api": "Review API integration patterns and apply stability fixes",
        }
        return actions.get(fix_type, f"Review {fix_type} patterns and apply fixes")

    def _deduplicate_patterns(self, patterns: List[ImprovementPattern]) -> List[ImprovementPattern]:
        """Deduplicate system fix patterns."""
        seen_fixes = set()
        unique_patterns = []

        for pattern in patterns:
            # Use subtype and key parts of description for deduplication
            dedup_key = f"{pattern.subtype}:{pattern.description[:50]}"

            if dedup_key not in seen_fixes:
                seen_fixes.add(dedup_key)
                unique_patterns.append(pattern)

        return unique_patterns


class PatternExtractor:
    """Main orchestrator for pattern extraction from claude-trace entries.

    Coordinates multiple specialized analyzers to identify improvement patterns
    across different domains: code, prompts, and system fixes.
    """

    def __init__(self):
        """Initialize pattern extractor with specialized analyzers."""
        self.analyzers = [
            CodeImprovementAnalyzer(),
            PromptImprovementAnalyzer(),
            SystemFixAnalyzer(),
        ]

    def extract_patterns(self, entries: List[ParsedEntry]) -> List[ImprovementPattern]:
        """Extract improvement patterns from parsed entries.

        Args:
            entries: List of parsed entries to analyze

        Returns:
            List of identified improvement patterns from all analyzers
        """
        if not entries:
            return []

        all_patterns = []

        # Run each analyzer
        for analyzer in self.analyzers:
            try:
                patterns = analyzer.analyze(entries)
                all_patterns.extend(patterns)
            except Exception:
                # Continue with other analyzers if one fails
                continue

        # Global deduplication across all analyzers
        return self._global_deduplication(all_patterns)

    def _global_deduplication(self, patterns: List[ImprovementPattern]) -> List[ImprovementPattern]:
        """Perform global deduplication across all analyzer results.

        Args:
            patterns: List of patterns from all analyzers

        Returns:
            Deduplicated list of patterns
        """
        seen_patterns = set()
        unique_patterns = []

        for pattern in patterns:
            # Create deduplication key from type, subtype, and description hash
            desc_hash = hashlib.md5(pattern.description.encode()).hexdigest()[:8]
            dedup_key = f"{pattern.type}:{pattern.subtype}:{desc_hash}"

            if dedup_key not in seen_patterns:
                seen_patterns.add(dedup_key)
                unique_patterns.append(pattern)

        return unique_patterns
