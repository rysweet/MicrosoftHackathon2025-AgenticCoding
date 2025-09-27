"""Simple duplicate detection system for GitHub issues.

This package provides basic duplicate detection capabilities for the reflection system.

Key Features:
- Content normalization and SHA-256 hashing
- Simple in-memory cache with disk persistence
- Basic duplicate detection

Public Interface:
- check_duplicate_issue: Main function to check for duplicates
- store_new_issue: Store new issues in cache
- DuplicateDetectionResult: Result object with similarity details
"""

from .cache_manager import (
    GitHubIssueCacheManager,
    get_cache_manager,
)
from .content_hash import (
    ContentHashGenerator,
    generate_composite_hash,
    generate_content_hash,
)
from .engine import (
    DuplicateDetectionEngine,
    DuplicateDetectionResult,
    check_duplicate_issue,
    get_detection_engine,
    get_performance_stats,
    store_new_issue,
)

# Version information
__version__ = "1.0.0"
__author__ = "Microsoft Hackathon 2025 - Agentic Coding Team"

# Public API
__all__ = [
    # Main functions
    "check_duplicate_issue",
    "store_new_issue",
    "get_performance_stats",
    # Classes
    "DuplicateDetectionResult",
    "DuplicateDetectionEngine",
    "GitHubIssueCacheManager",
    "ContentHashGenerator",
    # Access functions
    "get_detection_engine",
    "get_cache_manager",
    # Utility functions
    "generate_content_hash",
    "generate_composite_hash",
]
