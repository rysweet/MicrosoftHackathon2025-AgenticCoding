"""Simple content hashing for duplicate detection.

Provides basic content normalization and SHA-256 hashing for duplicate issue detection.
"""

import hashlib
import re
from functools import lru_cache
from typing import Dict, Optional, Set


class ContentHashGenerator:
    """Simple content hash generator for duplicate detection."""

    def __init__(self):
        """Initialize the hash generator."""
        pass

    @lru_cache(maxsize=512)
    def normalize_content(self, content: str) -> str:
        """Basic content normalization with caching.

        Args:
            content: Raw content to normalize

        Returns:
            Normalized content string
        """
        if not isinstance(content, str):
            content = str(content)

        # Basic normalization: lowercase and normalize whitespace
        normalized = content.lower()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of normalized content.

        Args:
            content: Content to hash

        Returns:
            SHA-256 hash as hexadecimal string
        """
        normalized = self.normalize_content(content)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def generate_composite_hash(
        self, title: str, body: str, pattern_type: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate single content hash for duplicate detection.

        Args:
            title: Issue title
            body: Issue body content
            pattern_type: Optional pattern type for categorization

        Returns:
            Dictionary containing content hash
        """
        # Combine title and body for full content hash
        full_content = f"{title}\n{body}"
        if pattern_type:
            full_content = f"{pattern_type}\n{full_content}"

        return {"content_hash": self.generate_content_hash(full_content)}

    def calculate_similarity_score(self, hash1: Dict[str, str], hash2: Dict[str, str]) -> float:
        """Calculate similarity between content hashes.

        Args:
            hash1: First hash dictionary
            hash2: Second hash dictionary

        Returns:
            1.0 if hashes match, 0.0 otherwise
        """
        if "content_hash" in hash1 and "content_hash" in hash2:
            return 1.0 if hash1["content_hash"] == hash2["content_hash"] else 0.0
        return 0.0

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Optimized text similarity using word overlap with early exits.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Early exit for identical strings
        if text1 == text2:
            return 1.0

        # Early exit for very different lengths (optimization)
        len1, len2 = len(text1), len(text2)
        if len1 == 0 and len2 == 0:
            return 1.0
        if len1 == 0 or len2 == 0:
            return 0.0

        # Early exit if length difference is too large
        max_len = max(len1, len2)
        min_len = min(len1, len2)
        if max_len > min_len * 3:  # If one is 3x longer, likely very different
            return 0.0

        norm1 = self.normalize_content(text1)
        norm2 = self.normalize_content(text2)

        # Early exit for identical normalized content
        if norm1 == norm2:
            return 1.0

        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        # Quick check: if no common words at all, return 0
        if words1.isdisjoint(words2):
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def is_duplicate(self, hash1: Dict[str, str], hash2: Dict[str, str]) -> bool:
        """Simple duplicate detection via hash comparison.

        Args:
            hash1: First hash dictionary
            hash2: Second hash dictionary

        Returns:
            True if content hashes match exactly
        """
        return self.calculate_similarity_score(hash1, hash2) == 1.0

    def extract_keywords(self, text: str, max_keywords: int = 10) -> Set[str]:
        """Extract key words from text for fast similarity pre-filtering.

        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return

        Returns:
            Set of key words
        """
        normalized = self.normalize_content(text)
        words = normalized.split()

        # Filter out common words and short words
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
            "may",
            "might",
            "this",
            "that",
            "these",
            "those",
        }

        keywords = {word for word in words if len(word) > 2 and word not in stop_words}

        # Return most common words (simplified - just return first N)
        return set(list(keywords)[:max_keywords])


# Global instance for convenience
_hash_generator = ContentHashGenerator()


def generate_content_hash(content: str) -> str:
    """Generate content hash using global generator."""
    return _hash_generator.generate_content_hash(content)


def generate_composite_hash(
    title: str, body: str, pattern_type: Optional[str] = None
) -> Dict[str, str]:
    """Generate composite hash using global generator."""
    return _hash_generator.generate_composite_hash(title, body, pattern_type)


def is_duplicate_content(hash1: Dict[str, str], hash2: Dict[str, str]) -> bool:
    """Check if content is duplicate using global generator."""
    return _hash_generator.is_duplicate(hash1, hash2)


def extract_keywords(text: str, max_keywords: int = 10) -> Set[str]:
    """Extract keywords using global generator."""
    return _hash_generator.extract_keywords(text, max_keywords)
