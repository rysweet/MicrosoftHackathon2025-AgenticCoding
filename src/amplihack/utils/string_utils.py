"""String utility functions for text processing.

This module provides utilities for converting strings to URL-safe formats.

Philosophy:
- Ruthless simplicity (stdlib only)
- Single responsibility per function
- Self-contained and regeneratable
- Zero-BS implementation (no stubs or placeholders)

Public API:
    slugify: Convert text to URL-safe slug format
    titlecase: Convert text to Title Case
    titlecase_safe: Type-safe wrapper with None/type coercion handling
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
    """Convert text to Title Case.

    Uses Python's built-in str.title() method.

    Note:
        Python's str.title() has a known limitation with apostrophes:
        "don't" becomes "Don'T" instead of "Don't".

    Args:
        text: Input string to convert.

    Returns:
        Title-cased string.

    Examples:
        >>> titlecase("hello world")
        'Hello World'
    """
    return text.title()


def titlecase_safe(text: str | None | float | bool) -> str:
    """Type-safe wrapper around titlecase() with None and type coercion handling.

    Args:
        text: String, None, or common types that can be coerced to string.
            - None returns empty string
            - Non-strings converted via str()

    Returns:
        Title-cased string. Empty string for None input.

    Examples:
        >>> titlecase_safe(None)
        ''
        >>> titlecase_safe(42)
        '42'
        >>> titlecase_safe("hello world")
        'Hello World'
    """
    if text is None:
        return ""
    return titlecase(str(text))


__all__ = ["slugify", "titlecase", "titlecase_safe"]
