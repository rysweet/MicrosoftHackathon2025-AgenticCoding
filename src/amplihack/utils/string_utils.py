"""String utility functions for text processing.

This module provides utilities for string transformation including
slug generation and case conversion.

Philosophy:
- Ruthless simplicity (stdlib only)
- Single responsibility per function
- Self-contained and regeneratable
- Zero-BS implementation (no stubs or placeholders)

Public API:
    slugify: Convert text to URL-safe slug format
    titlecase: Convert string to Title Case
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


def titlecase(text: str) -> str:
    """Convert string to Title Case.

    Capitalizes the first letter of each word, lowercasing the rest.
    Word boundaries include whitespace, punctuation, and numbers.

    Args:
        text: String to convert.

    Returns:
        Title-cased string with spacing and punctuation preserved.

    Raises:
        TypeError: If text is not a string.

    Note:
        Word boundaries are detected for ASCII letters (a-z, A-Z) only.
        Non-ASCII letters are lowercased but don't trigger capitalization.

    Examples:
        >>> titlecase("hello world")
        'Hello World'
        >>> titlecase("hello-world")
        'Hello-World'
        >>> titlecase("it's")
        "It'S"
    """
    if not isinstance(text, str):
        raise TypeError(f"titlecase() argument must be str, not {type(text).__name__}")

    if not text:
        return text

    # Pattern: match any letter preceded by start or non-letter
    # Then lowercase everything and capitalize matches
    result = text.lower()
    return re.sub(r"(^|[^a-zA-Z])([a-zA-Z])", lambda m: m.group(1) + m.group(2).upper(), result)


__all__ = ["slugify", "titlecase"]
