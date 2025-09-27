"""Deduplication engine for preventing duplicate GitHub issue creation.

This module provides multi-layer duplicate detection through:
- Content similarity checking (description, evidence matching)
- Temporal deduplication (time-based filtering)
- Existing issue checking (GitHub API integration)
- Pattern fingerprinting for exact duplicates

The engine uses a conservative approach - when in doubt, it prevents duplication
to avoid creating redundant GitHub issues.
"""

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

# Optional imports for GitHub integration
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    requests = None  # type: ignore
    HAS_REQUESTS = False

from .pattern_extractor import ImprovementPattern


@dataclass
class DuplicationResult:
    """Result of duplication checking.

    Attributes:
        is_duplicate: Whether the pattern is a duplicate
        duplication_type: Type of duplication detected
        reason: Human-readable explanation
        confidence: Confidence in duplication detection (0.0 to 1.0)
        similar_pattern_id: ID of similar pattern if found
        metadata: Additional detection metadata
    """

    is_duplicate: bool
    duplication_type: str
    reason: str
    confidence: float
    similar_pattern_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate result fields after initialization."""
        if self.is_duplicate and not self.duplication_type:
            raise ValueError("duplication_type must be provided when is_duplicate=True")

        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary representation of the result
        """
        return {
            "is_duplicate": self.is_duplicate,
            "duplication_type": self.duplication_type,
            "reason": self.reason,
            "confidence": self.confidence,
            "similar_pattern_id": self.similar_pattern_id,
            "metadata": self.metadata,
        }


class DuplicationChecker(ABC):
    """Base class for specialized duplication checkers."""

    def __init__(self):
        """Initialize base checker."""
        self.name = self.__class__.__name__

    @abstractmethod
    def check_duplication(
        self, pattern: ImprovementPattern, existing_patterns: List[ImprovementPattern]
    ) -> DuplicationResult:
        """Check if pattern is a duplicate.

        Args:
            pattern: Pattern to check for duplication
            existing_patterns: List of existing patterns to compare against

        Returns:
            DuplicationResult indicating whether pattern is duplicate
        """
        pass


class ContentSimilarityChecker(DuplicationChecker):
    """Checks for content-based duplication using similarity metrics.

    Uses multiple similarity algorithms:
    - Description text similarity (SequenceMatcher)
    - Evidence overlap analysis
    - Keyword matching for technical terms
    - Type/subtype consistency checking
    """

    def __init__(self, similarity_threshold: float = 0.8):
        super().__init__()
        self.similarity_threshold = similarity_threshold

    def check_duplication(
        self, pattern: ImprovementPattern, existing_patterns: List[ImprovementPattern]
    ) -> DuplicationResult:
        """Check content-based duplication against existing patterns.

        Args:
            pattern: Pattern to check
            existing_patterns: Existing patterns to compare against

        Returns:
            DuplicationResult with similarity analysis
        """
        if not existing_patterns:
            return DuplicationResult(
                is_duplicate=False,
                duplication_type="none",
                reason="No existing patterns to compare",
                confidence=0.0,
            )

        # Check against each existing pattern
        for existing_pattern in existing_patterns:
            similarity_score = self._calculate_similarity(pattern, existing_pattern)

            if similarity_score >= (self.similarity_threshold - 1e-10):
                return DuplicationResult(
                    is_duplicate=True,
                    duplication_type="content_similarity",
                    reason=f"High content similarity ({similarity_score:.2f}) with existing pattern",
                    confidence=similarity_score,
                    similar_pattern_id=existing_pattern.id,
                    metadata={
                        "similarity_score": similarity_score,
                        "comparison_pattern_id": existing_pattern.id,
                    },
                )

        # No significant similarity found
        return DuplicationResult(
            is_duplicate=False,
            duplication_type="none",
            reason="No similar content found",
            confidence=0.0,
        )

    def _calculate_similarity(
        self, pattern1: ImprovementPattern, pattern2: ImprovementPattern
    ) -> float:
        """Calculate comprehensive similarity score between two patterns.

        Args:
            pattern1: First pattern
            pattern2: Second pattern

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Must be same type and subtype to be considered similar
        if pattern1.type != pattern2.type or pattern1.subtype != pattern2.subtype:
            return 0.0

        # Simple description similarity
        return self._text_similarity(pattern1.description, pattern2.description)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0

        # Normalize text for comparison
        normalized1 = self._normalize_text(text1)
        normalized2 = self._normalize_text(text2)

        matcher = SequenceMatcher(None, normalized1, normalized2)
        return matcher.ratio()

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


class TemporalDeduplicationChecker(DuplicationChecker):
    """Checks for temporal duplication - patterns too close in time.

    Prevents creating multiple issues for the same type of improvement
    within a short time window, which often indicates the same underlying
    issue being detected multiple times.
    """

    def __init__(self, time_window_minutes: int = 60):
        """Initialize temporal checker.

        Args:
            time_window_minutes: Time window in minutes to check for duplicates
        """
        super().__init__()
        self.time_window = timedelta(minutes=time_window_minutes)

    def check_duplication(
        self, pattern: ImprovementPattern, existing_patterns: List[ImprovementPattern]
    ) -> DuplicationResult:
        """Check temporal duplication against existing patterns.

        Args:
            pattern: Pattern to check
            existing_patterns: Existing patterns to compare against

        Returns:
            DuplicationResult with temporal analysis
        """
        pattern_time = self._extract_timestamp(pattern)
        if not pattern_time:
            return DuplicationResult(
                is_duplicate=False,
                duplication_type="none",
                reason="No timestamp available for temporal comparison",
                confidence=0.0,
            )

        # Check against existing patterns of same type/subtype
        for existing_pattern in existing_patterns:
            if (
                pattern.type == existing_pattern.type
                and pattern.subtype == existing_pattern.subtype
            ):
                existing_time = self._extract_timestamp(existing_pattern)
                if existing_time:
                    time_diff = abs(pattern_time - existing_time)

                    if time_diff <= self.time_window:
                        return DuplicationResult(
                            is_duplicate=True,
                            duplication_type="temporal",
                            reason=f"Similar pattern found within {time_diff} time window",
                            confidence=1.0
                            - (time_diff.total_seconds() / self.time_window.total_seconds()),
                            similar_pattern_id=existing_pattern.id,
                            metadata={
                                "time_difference_minutes": time_diff.total_seconds() / 60,
                                "time_window_minutes": self.time_window.total_seconds() / 60,
                            },
                        )

        return DuplicationResult(
            is_duplicate=False,
            duplication_type="none",
            reason="No temporal duplicates found",
            confidence=0.0,
        )

    def _extract_timestamp(self, pattern: ImprovementPattern) -> Optional[datetime]:
        """Extract timestamp from pattern metadata or source entries.

        Args:
            pattern: Pattern to extract timestamp from

        Returns:
            Datetime object or None if no timestamp found
        """
        # Try metadata first
        if "timestamp" in pattern.metadata:
            try:
                return datetime.fromisoformat(pattern.metadata["timestamp"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Try source entries
        if pattern.source_entries:
            try:
                entry_timestamp = pattern.source_entries[0].timestamp
                return datetime.fromisoformat(entry_timestamp.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return None


class ExistingIssueChecker(DuplicationChecker):
    """Checks for duplication against existing GitHub issues.

    Queries the GitHub API to find similar existing issues and prevents
    creating duplicates. Uses conservative rate limiting and error handling.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        repo_owner: str = "",
        repo_name: str = "",
        similarity_threshold: float = 0.7,
    ):
        """Initialize GitHub issue checker.

        Args:
            github_token: GitHub API token (optional, reduces rate limits)
            repo_owner: Repository owner
            repo_name: Repository name
            similarity_threshold: Minimum similarity to consider duplicate
        """
        super().__init__()
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.similarity_threshold = similarity_threshold

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Seconds between requests

        # GitHub API base URL
        self.api_base = "https://api.github.com"

    def check_duplication(
        self, pattern: ImprovementPattern, existing_patterns: List[ImprovementPattern]
    ) -> DuplicationResult:
        """Check for duplication against existing GitHub issues.

        Args:
            pattern: Pattern to check
            existing_patterns: Not used for GitHub checking

        Returns:
            DuplicationResult with GitHub issue analysis
        """
        if not HAS_REQUESTS:
            return DuplicationResult(
                is_duplicate=False,
                duplication_type="none",
                reason="GitHub API checking unavailable (requests module not installed)",
                confidence=0.0,
            )

        if not self.repo_owner or not self.repo_name:
            return DuplicationResult(
                is_duplicate=False,
                duplication_type="none",
                reason="No GitHub repository configured",
                confidence=0.0,
            )

        try:
            # Rate limiting
            self._enforce_rate_limit()

            # Search for similar issues
            similar_issues = self._search_similar_issues(pattern)

            if similar_issues:
                # Find best match
                best_match = max(similar_issues, key=lambda x: x["similarity_score"])

                if best_match["similarity_score"] >= self.similarity_threshold:
                    return DuplicationResult(
                        is_duplicate=True,
                        duplication_type="existing_issue",
                        reason=f"Similar GitHub issue #{best_match['number']} found",
                        confidence=best_match["similarity_score"],
                        metadata={
                            "github_issue_number": best_match["number"],
                            "github_issue_title": best_match["title"],
                            "similarity_score": best_match["similarity_score"],
                        },
                    )

            return DuplicationResult(
                is_duplicate=False,
                duplication_type="none",
                reason="No similar GitHub issues found",
                confidence=0.0,
            )

        except Exception as e:
            # Conservative approach: don't consider as duplicate if we can't check
            return DuplicationResult(
                is_duplicate=False,
                duplication_type="none",
                reason=f"GitHub API check failed: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _search_similar_issues(self, pattern: ImprovementPattern) -> List[Dict[str, Any]]:
        """Search for similar issues using GitHub API.

        Args:
            pattern: Pattern to search for

        Returns:
            List of similar issues with similarity scores
        """
        # Create search query from pattern description
        search_terms = self._extract_search_terms(pattern.description)
        query = " ".join(search_terms[:5])  # Limit to avoid query length issues

        # GitHub API search endpoint
        search_url = f"{self.api_base}/search/issues"
        params = {
            "q": f"{query} repo:{self.repo_owner}/{self.repo_name} type:issue",
            "per_page": 10,  # Limit results for performance
        }

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        if not HAS_REQUESTS or requests is None:
            raise RuntimeError("requests module is required for GitHub integration")
        response = requests.get(search_url, params=params, headers=headers, timeout=10)

        if response.status_code == 429:  # Rate limited
            raise Exception("GitHub API rate limit exceeded")

        response.raise_for_status()

        search_results = response.json()
        similar_issues = []

        for issue in search_results.get("items", []):
            similarity_score = self._calculate_issue_similarity(pattern, issue)
            if similarity_score > 0.3:  # Only consider reasonably similar issues
                similar_issues.append(
                    {
                        "number": issue["number"],
                        "title": issue["title"],
                        "body": issue.get("body", ""),
                        "state": issue["state"],
                        "similarity_score": similarity_score,
                    }
                )

        return similar_issues

    def _extract_search_terms(self, description: str) -> List[str]:
        """Extract meaningful search terms from description.

        Args:
            description: Pattern description

        Returns:
            List of search terms
        """
        # Remove common words and extract meaningful terms
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
        }

        words = re.findall(r"\w+", description.lower())
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]

        return meaningful_words

    def _calculate_issue_similarity(
        self, pattern: ImprovementPattern, issue: Dict[str, Any]
    ) -> float:
        """Calculate similarity between pattern and GitHub issue.

        Args:
            pattern: Pattern to compare
            issue: GitHub issue data

        Returns:
            Similarity score between 0.0 and 1.0
        """
        issue_text = f"{issue['title']} {issue.get('body', '')}"
        pattern_text = f"{pattern.description} {' '.join(pattern.evidence)}"

        # Simple text similarity
        matcher = SequenceMatcher(None, pattern_text.lower(), issue_text.lower())
        return matcher.ratio()

    def _enforce_rate_limit(self):
        """Enforce rate limiting for GitHub API requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class DeduplicationEngine:
    """Main orchestrator for multi-layer duplication detection.

    Coordinates multiple duplication checkers to provide comprehensive
    duplicate detection with configurable thresholds and conservative
    error handling.
    """

    def __init__(
        self, github_token: Optional[str] = None, repo_owner: str = "", repo_name: str = ""
    ):
        """Initialize deduplication engine.

        Args:
            github_token: GitHub API token for issue checking
            repo_owner: Repository owner for GitHub checks
            repo_name: Repository name for GitHub checks
        """
        self.checkers = [
            ContentSimilarityChecker(similarity_threshold=0.8),
            TemporalDeduplicationChecker(time_window_minutes=60),
            ExistingIssueChecker(
                github_token=github_token,
                repo_owner=repo_owner,
                repo_name=repo_name,
                similarity_threshold=0.7,
            ),
        ]

        # Internal state for tracking
        self.processed_patterns: List[ImprovementPattern] = []
        self.duplication_stats = {"total_checked": 0, "duplicates_found": 0, "by_type": {}}

    def is_duplicate(self, pattern: ImprovementPattern) -> DuplicationResult:
        """Check if pattern is a duplicate using all available checkers.

        Args:
            pattern: Pattern to check for duplication

        Returns:
            DuplicationResult with comprehensive analysis
        """
        self.duplication_stats["total_checked"] += 1

        # Run each checker - stop at first positive detection
        for checker in self.checkers:
            try:
                result = checker.check_duplication(pattern, self.processed_patterns)

                if result.is_duplicate:
                    self.duplication_stats["duplicates_found"] += 1
                    duplication_type = result.duplication_type
                    self.duplication_stats["by_type"][duplication_type] = (
                        self.duplication_stats["by_type"].get(duplication_type, 0) + 1
                    )
                    return result

            except Exception:
                # Continue with other checkers if one fails
                continue

        # No duplication detected - add to processed patterns
        self.processed_patterns.append(pattern)

        return DuplicationResult(
            is_duplicate=False,
            duplication_type="none",
            reason="No duplication detected by any checker",
            confidence=0.0,
        )

    def get_deduplication_report(self) -> Dict[str, Any]:
        """Get comprehensive deduplication statistics.

        Returns:
            Dictionary with deduplication report
        """
        return {
            "total_patterns_checked": self.duplication_stats["total_checked"],
            "duplicates_found": self.duplication_stats["duplicates_found"],
            "unique_patterns": len(self.processed_patterns),
            "duplication_types": dict(self.duplication_stats["by_type"]),
            "deduplication_rate": (
                self.duplication_stats["duplicates_found"]
                / max(self.duplication_stats["total_checked"], 1)
            ),
        }

    def reset_cache(self):
        """Reset internal caches and state."""
        self.processed_patterns.clear()
        self.duplication_stats = {"total_checked": 0, "duplicates_found": 0, "by_type": {}}
