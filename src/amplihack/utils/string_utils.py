"""String utility functions for text processing.

This module provides utilities for converting strings to URL-safe formats
and proper title casing.

Philosophy:
- Ruthless simplicity (stdlib only)
- Single responsibility per function
- Self-contained and regeneratable
- Zero-BS implementation (no stubs or placeholders)

Public API:
    slugify: Convert text to URL-safe slug format
    titlecase: Convert text to proper Title Case (handles articles, acronyms, hyphens)
    SMALL_WORDS: Set of words kept lowercase in titles (customizable)
"""

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to URL-safe slug format.

    Transforms any string into a URL-safe slug by:
    1. Normalizing Unicode (NFD) and converting to ASCII
    2. Converting to lowercase
    3. Replacing whitespace and special chars with hyphens
    4. Consolidating consecutive hyphens
    5. Stripping leading/trailing hyphens

    Args:
        text: Input string with any Unicode characters, special chars, or spaces.

    Returns:
        URL-safe slug with lowercase alphanumeric characters and hyphens.
        Empty string if input contains no valid characters.

    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("Café")
        'cafe'
        >>> slugify("Rock & Roll")
        'rock-roll'
    """
    # Normalize Unicode and convert to ASCII
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    # Lowercase and remove quotes (preserve contractions)
    text = ascii_text.lower()
    text = re.sub(r"[\'\"]+", "", text)

    # Replace whitespace and separators with hyphens
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[_/\\@!&.,;:()\[\]{}<>?#$%^*+=|`~]+", "-", text)

    # Keep only alphanumeric and hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)

    # Consolidate hyphens and strip edges
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# Small words kept lowercase in titles unless first/last word
# Customize by importing and modifying this set
SMALL_WORDS = {
    # Articles
    "a",
    "an",
    "the",
    # Coordinating conjunctions
    "and",
    "but",
    "or",
    "nor",
    "for",
    "yet",
    "so",
    # Short prepositions
    "at",
    "by",
    "in",
    "of",
    "on",
    "to",
    "up",
    "as",
    "if",
    "en",
    "per",
    "via",
}


def titlecase(s: str) -> str:
    """Convert string to proper Title Case.

    Transforms text following standard title case conventions:
    1. Capitalize first and last words always
    2. Capitalize words not in SMALL_WORDS
    3. Preserve acronyms (consecutive uppercase letters, 2+ chars)
    4. Handle hyphenated words (capitalize each part)
    5. Capitalize word after colon

    Args:
        s: Input string to convert to title case.

    Returns:
        String converted to proper title case.
        Empty string if input is empty.

    Examples:
        >>> titlecase("the quick brown fox")
        'The Quick Brown Fox'
        >>> titlecase("war and peace")
        'War and Peace'
        >>> titlecase("NASA launches new satellite")
        'NASA Launches New Satellite'
        >>> titlecase("self-driving cars")
        'Self-Driving Cars'
        >>> titlecase("python: a beginner's guide")
        "Python: A Beginner's Guide"
        >>> titlecase("THE LORD OF THE RINGS")
        'The Lord of the Rings'
        >>> titlecase("a tale of two cities")
        'A Tale of Two Cities'

    Note:
        - SMALL_WORDS can be imported and customized for domain-specific needs
        - Acronyms are detected as 2+ consecutive uppercase letters
        - Works with Unicode text after ASCII normalization
    """
    if not s:
        return ""

    words = s.split()
    result = []

    # Check if entire input is all caps - if so, don't preserve any "acronyms"
    all_caps_input = s.isupper()

    for i, word in enumerate(words):
        is_first = i == 0
        is_last = i == len(words) - 1
        after_colon = i > 0 and words[i - 1].endswith(":")

        # Handle hyphenated words
        if "-" in word:
            parts = word.split("-")
            capitalized_parts = []
            for part in parts:
                if not all_caps_input and _is_acronym(part):
                    capitalized_parts.append(part)
                else:
                    capitalized_parts.append(part.capitalize())
            result.append("-".join(capitalized_parts))
            continue

        # Preserve acronyms (2+ consecutive uppercase) only if not all-caps input
        if not all_caps_input and _is_acronym(word):
            result.append(word)
            continue

        # First word, last word, or after colon: always capitalize
        if is_first or is_last or after_colon:
            result.append(word.capitalize())
            continue

        # Small words stay lowercase
        if word.lower() in SMALL_WORDS:
            result.append(word.lower())
            continue

        # Default: capitalize
        result.append(word.capitalize())

    return " ".join(result)


def _is_acronym(word: str) -> bool:
    """Check if word is an acronym (2-5 uppercase letters, not a common word).

    Acronyms are typically short (2-5 chars) all-caps abbreviations like
    NASA, FBI, API. Words longer than 5 chars in all caps are likely just
    shouted text, not acronyms.
    """
    # Strip punctuation for check
    clean = re.sub(r"[^\w]", "", word)
    # Must be 2-5 chars, all uppercase, and all alphabetic
    return 2 <= len(clean) <= 5 and clean.isupper() and clean.isalpha()


__all__ = ["slugify", "titlecase", "SMALL_WORDS"]
