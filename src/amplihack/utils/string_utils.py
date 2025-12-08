"""String utility functions for text processing.

This module provides utilities for converting strings to URL-safe formats.

Philosophy:
- Ruthless simplicity (stdlib only)
- Single responsibility per function
- Self-contained and regeneratable
- Zero-BS implementation (no stubs or placeholders)

Public API:
    slugify: Convert text to URL-safe slug format
    titlecase: Convert text to title case with graceful None handling
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


def titlecase(text: str | None) -> str:
    """Convert text to title case with graceful None handling.

    Transforms input text to title case (first letter of each word capitalized)
    using Python's built-in str.title() method. Handles None input gracefully
    by returning an empty string.

    Args:
        text: Input string to transform, or None.

    Returns:
        Title-cased string with first letter of each word capitalized.
        Empty string if input is None.

    Examples:
        >>> titlecase("hello world")
        'Hello World'
        >>> titlecase("the quick brown fox")
        'The Quick Brown Fox'
        >>> titlecase(None)
        ''
        >>> titlecase("")
        ''
        >>> titlecase("ALREADY UPPERCASE")
        'Already Uppercase'

    Note:
        Uses str.title() which capitalizes after any non-letter character.
        This means "it's" becomes "It'S". For more sophisticated title
        casing (e.g., AP style), consider a dedicated library.
    """
    if text is None:
        return ""
    return text.title()


__all__ = ["slugify", "titlecase"]
