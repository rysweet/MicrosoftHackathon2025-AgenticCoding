"""Simple issue cache for duplicate detection.

Basic in-memory caching of GitHub issue metadata for duplicate detection.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set


class GitHubIssueCacheManager:
    """Simple cache manager for GitHub issue metadata."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the cache manager.

        Args:
            cache_dir: Directory for cache files (default: ~/.amplihack/cache)
        """
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".amplihack" / "cache" / "github_issues"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "issue_cache.json"

        # Simple in-memory cache
        self._memory_cache: Dict[str, Dict] = {}

        # Performance optimizations
        self._dirty = False  # Track if cache needs saving
        self._last_save_time = 0.0
        self._save_interval = 5.0  # Save at most every 5 seconds
        self._max_cache_size = 10000  # Limit cache size

        # Keyword index for fast similarity pre-filtering
        self._keyword_index: Dict[str, Set[str]] = {}  # keyword -> set of issue_ids

        # Load existing cache
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._memory_cache = data
        except (json.JSONDecodeError, OSError):
            # If cache is corrupted, start fresh
            self._memory_cache = {}

    def _save_cache(self, force: bool = False) -> None:
        """Save cache to disk with throttling.

        Args:
            force: Force save even if interval hasn't elapsed
        """
        if not self._dirty and not force:
            return

        current_time = time.time()
        if not force and (current_time - self._last_save_time) < self._save_interval:
            return  # Too soon to save again

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, indent=2)
            self._dirty = False
            self._last_save_time = current_time
        except OSError:
            # Ignore save errors
            pass

    def _generate_cache_key(self, issue_id: str, repository: str = "current") -> str:
        """Generate cache key from issue ID and repository."""
        return f"{repository}:{issue_id}"

    def store_issue(
        self,
        issue_id: str,
        title: str,
        body: str,
        hashes: Dict[str, str],
        pattern_type: Optional[str] = None,
        priority: str = "medium",
        repository: str = "current",
    ) -> None:
        """Store issue metadata in cache."""
        # Limit cache size
        if len(self._memory_cache) >= self._max_cache_size:
            self._evict_oldest_entries()

        cache_key = self._generate_cache_key(issue_id, repository)

        entry = {
            "issue_id": str(issue_id),
            "title": str(title),
            "body": str(body),
            "hashes": hashes,
            "pattern_type": pattern_type,
            "priority": str(priority),
            "repository": str(repository),
            "timestamp": time.time(),  # For LRU eviction
        }

        self._memory_cache[cache_key] = entry
        self._update_keyword_index(cache_key, title, body)
        self._dirty = True
        self._save_cache()  # Will be throttled automatically

    def get_issue(self, issue_id: str, repository: str = "current") -> Optional[Dict]:
        """Retrieve issue metadata from cache."""
        cache_key = self._generate_cache_key(issue_id, repository)
        return self._memory_cache.get(cache_key)

    def find_similar_issues(
        self, hashes: Dict[str, str], repository: str = "current"
    ) -> List[Dict]:
        """Find issues with similar content hashes."""
        similar_issues = []

        for entry in self._memory_cache.values():
            # Filter by repository
            if entry.get("repository") != repository:
                continue

            entry_hashes = entry.get("hashes", {})

            # Check for hash matches
            for hash_type, hash_value in hashes.items():
                if hash_type in entry_hashes and entry_hashes[hash_type] == hash_value:
                    similar_issues.append(entry.copy())
                    break

        return similar_issues

    def find_potentially_similar_issues(
        self, keywords: Set[str], repository: str = "current", min_keyword_overlap: int = 2
    ) -> List[Dict]:
        """Find issues with keyword overlap for faster similarity pre-filtering.

        Args:
            keywords: Set of keywords to match against
            repository: Repository to search in
            min_keyword_overlap: Minimum number of overlapping keywords

        Returns:
            List of potentially similar issues
        """
        candidate_ids = set()

        # Find issues with overlapping keywords
        for keyword in keywords:
            if keyword in self._keyword_index:
                candidate_ids.update(self._keyword_index[keyword])

        # Filter candidates by keyword overlap count and repository
        potential_issues = []
        for issue_id in candidate_ids:
            cache_key = self._generate_cache_key(issue_id, repository)
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if entry.get("repository") == repository:
                    # Count keyword overlaps
                    entry_keywords = entry.get("keywords", set())
                    overlap_count = len(keywords.intersection(entry_keywords))
                    if overlap_count >= min_keyword_overlap:
                        potential_issues.append(entry.copy())

        return potential_issues

    def get_all_issues(self, repository: str = "current") -> List[Dict]:
        """Get all cached issues for a repository."""
        return [
            entry.copy()
            for entry in self._memory_cache.values()
            if entry.get("repository") == repository
        ]

    def clear_cache(self, repository: Optional[str] = None) -> None:
        """Clear cache entries."""
        if repository:
            # Clear specific repository
            keys_to_remove = [
                key
                for key, entry in self._memory_cache.items()
                if entry.get("repository") == repository
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
        else:
            # Clear all
            self._memory_cache.clear()
            self._keyword_index.clear()

        self._dirty = True
        self._save_cache(force=True)

    def _evict_oldest_entries(self, keep_ratio: float = 0.8) -> None:
        """Evict oldest entries to keep cache size manageable.

        Args:
            keep_ratio: Ratio of entries to keep (0.8 = keep 80%, evict 20%)
        """
        if not self._memory_cache:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self._memory_cache.items(), key=lambda x: x[1].get("timestamp", 0))

        keep_count = int(len(sorted_entries) * keep_ratio)
        entries_to_remove = sorted_entries[:-keep_count] if keep_count > 0 else sorted_entries

        for key, _ in entries_to_remove:
            del self._memory_cache[key]

        # Rebuild keyword index after eviction
        self._rebuild_keyword_index()
        self._dirty = True

    def _update_keyword_index(self, cache_key: str, title: str, body: str) -> None:
        """Update keyword index for an issue."""
        from .content_hash import extract_keywords

        issue_id = cache_key.split(":", 1)[1]  # Extract issue_id from cache_key
        full_text = f"{title} {body}"
        keywords = extract_keywords(full_text)

        # Store keywords in the entry
        if cache_key in self._memory_cache:
            self._memory_cache[cache_key]["keywords"] = keywords

        # Update index
        for keyword in keywords:
            if keyword not in self._keyword_index:
                self._keyword_index[keyword] = set()
            self._keyword_index[keyword].add(issue_id)

    def _rebuild_keyword_index(self) -> None:
        """Rebuild the keyword index from scratch."""
        self._keyword_index.clear()

        for cache_key, entry in self._memory_cache.items():
            if "keywords" in entry:
                issue_id = cache_key.split(":", 1)[1]
                for keyword in entry["keywords"]:
                    if keyword not in self._keyword_index:
                        self._keyword_index[keyword] = set()
                    self._keyword_index[keyword].add(issue_id)

    def get_cache_stats(self) -> Dict:
        """Get basic cache statistics."""
        return {
            "total_entries": len(self._memory_cache),
            "cache_dir": str(self.cache_dir),
            "keyword_index_size": len(self._keyword_index),
            "total_keywords": sum(len(issues) for issues in self._keyword_index.values()),
            "dirty": self._dirty,
            "last_save_time": self._last_save_time,
        }


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> GitHubIssueCacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = GitHubIssueCacheManager()
    return _cache_manager


def store_issue_cache(
    issue_id: str,
    title: str,
    body: str,
    hashes: Dict[str, str],
    pattern_type: Optional[str] = None,
    priority: str = "medium",
    repository: str = "current",
) -> None:
    """Store issue in cache using global manager."""
    get_cache_manager().store_issue(
        issue_id, title, body, hashes, pattern_type, priority, repository
    )


def find_similar_cached_issues(hashes: Dict[str, str], repository: str = "current") -> List[Dict]:
    """Find similar issues using global manager."""
    return get_cache_manager().find_similar_issues(hashes, repository)
