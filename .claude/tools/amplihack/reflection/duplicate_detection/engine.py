"""Simple duplicate detection engine for GitHub issues.

Main detection logic that coordinates content hashing and cache management
to identify duplicate issues efficiently.
"""

from typing import Dict, List, Optional

from .cache_manager import GitHubIssueCacheManager, get_cache_manager
from .content_hash import ContentHashGenerator, extract_keywords


class DuplicateDetectionResult:
    """Result object for duplicate detection operations."""

    def __init__(
        self,
        is_duplicate: bool,
        similar_issues: Optional[List[Dict]] = None,
        confidence: float = 0.0,
        reason: str = "",
    ):
        """Initialize detection result."""
        self.is_duplicate = is_duplicate
        self.similar_issues = similar_issues or []
        self.confidence = confidence
        self.reason = reason

    def to_dict(self) -> Dict:
        """Convert result to dictionary format."""
        return {
            "is_duplicate": self.is_duplicate,
            "similar_issues": self.similar_issues,
            "confidence": self.confidence,
            "reason": self.reason,
            "similar_count": len(self.similar_issues),
        }


class DuplicateDetectionEngine:
    """Simple engine for duplicate detection."""

    def __init__(self, cache_manager: Optional[GitHubIssueCacheManager] = None):
        """Initialize the duplicate detection engine."""
        self.cache_manager = cache_manager or get_cache_manager()
        self.hash_generator = ContentHashGenerator()

    def check_for_duplicates(
        self, title: str, body: str, pattern_type: Optional[str] = None, repository: str = "current"
    ) -> DuplicateDetectionResult:
        """Check if the given content is a duplicate of existing issues with optimizations."""
        try:
            # Generate content hashes
            hashes = self.hash_generator.generate_composite_hash(title, body, pattern_type)

            # Check against cached issues (exact hash match)
            similar_issues = self.cache_manager.find_similar_issues(hashes, repository)

            # Simple duplicate check: exact hash match
            is_duplicate = len(similar_issues) > 0
            confidence = 1.0 if is_duplicate else 0.0

            if is_duplicate:
                reason = f"Found {len(similar_issues)} exact duplicate(s)"
            else:
                # Optimized fallback: use keyword pre-filtering for text similarity
                result = self._find_similar_with_optimization(title, body, repository)
                if result:
                    return result
                reason = "No duplicates found"

            return DuplicateDetectionResult(
                is_duplicate=is_duplicate,
                similar_issues=similar_issues,
                confidence=confidence,
                reason=reason,
            )

        except Exception as e:
            return DuplicateDetectionResult(
                is_duplicate=False,
                similar_issues=[],
                confidence=0.0,
                reason=f"Detection failed: {str(e)}",
            )

    def _find_best_text_match(self, title: str, body: str, all_issues: List[Dict]) -> tuple:
        """Find best text similarity match (legacy method - use optimized version)."""
        best_similarity = 0.0
        best_match = None
        new_content = f"{title} {body}"

        for issue in all_issues:
            issue_content = f"{issue.get('title', '')} {issue.get('body', '')}"
            similarity = self.hash_generator.calculate_text_similarity(new_content, issue_content)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = issue

        return best_similarity, best_match

    def _find_similar_with_optimization(
        self, title: str, body: str, repository: str
    ) -> Optional[DuplicateDetectionResult]:
        """Optimized similarity search using keyword pre-filtering."""
        # Extract keywords from new content
        full_content = f"{title} {body}"
        keywords = extract_keywords(full_content)

        if not keywords:
            return None  # No keywords, skip similarity check

        # Use keyword index to find potentially similar issues
        candidates = self.cache_manager.find_potentially_similar_issues(
            keywords, repository, min_keyword_overlap=2
        )

        if not candidates:
            return None  # No candidates found

        # Early exit if too many candidates (performance protection)
        if len(candidates) > 100:
            # Fall back to sampling to avoid performance issues
            import random

            candidates = random.sample(candidates, 100)

        # Check text similarity only on pre-filtered candidates
        best_similarity = 0.0
        best_match = None

        for issue in candidates:
            issue_content = f"{issue.get('title', '')} {issue.get('body', '')}"
            similarity = self.hash_generator.calculate_text_similarity(full_content, issue_content)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = issue

            # Early exit if we find a very high similarity
            if similarity > 0.95:
                break

        # Return result if similarity is high enough
        if best_similarity > 0.8 and best_match is not None:  # High threshold for text similarity
            return DuplicateDetectionResult(
                is_duplicate=True,
                similar_issues=[best_match],
                confidence=best_similarity,
                reason=f"High text similarity ({best_similarity:.1%}) with issue #{best_match.get('issue_id')} (via keyword pre-filtering)",
            )

        return None

    def store_issue(
        self,
        issue_id: str,
        title: str,
        body: str,
        pattern_type: Optional[str] = None,
        priority: str = "medium",
        repository: str = "current",
    ) -> None:
        """Store a new issue in the cache for future duplicate detection."""
        try:
            # Generate hashes
            hashes = self.hash_generator.generate_composite_hash(title, body, pattern_type)

            # Store in cache (will automatically handle keyword indexing)
            self.cache_manager.store_issue(
                issue_id, title, body, hashes, pattern_type, priority, repository
            )
        except Exception:
            # Ignore storage errors
            pass

    def get_performance_stats(self) -> Dict:
        """Get performance statistics for monitoring."""
        cache_stats = self.cache_manager.get_cache_stats()
        return {
            "cache_stats": cache_stats,
            "optimization_features": {
                "keyword_indexing": True,
                "cache_throttling": True,
                "text_similarity_optimization": True,
                "early_exit_conditions": True,
            },
        }

    def clear_cache(self, repository: Optional[str] = None) -> None:
        """Clear the issue cache."""
        self.cache_manager.clear_cache(repository)


# Global engine instance
_detection_engine = None


def get_detection_engine() -> DuplicateDetectionEngine:
    """Get global detection engine instance."""
    global _detection_engine
    if _detection_engine is None:
        _detection_engine = DuplicateDetectionEngine()
    return _detection_engine


def check_duplicate_issue(
    title: str, body: str, pattern_type: Optional[str] = None, repository: str = "current"
) -> DuplicateDetectionResult:
    """Check for duplicate issues using global engine."""
    return get_detection_engine().check_for_duplicates(title, body, pattern_type, repository)


def store_new_issue(
    issue_id: str,
    title: str,
    body: str,
    pattern_type: Optional[str] = None,
    priority: str = "medium",
    repository: str = "current",
) -> None:
    """Store new issue using global engine."""
    get_detection_engine().store_issue(issue_id, title, body, pattern_type, priority, repository)


def get_performance_stats() -> Dict:
    """Get performance statistics using global engine."""
    return get_detection_engine().get_performance_stats()
