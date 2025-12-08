"""String utility functions for text processing.

This module provides utilities for converting strings to URL-safe formats
and Title Case format.

Philosophy:
- Ruthless simplicity (stdlib only)
- Single responsibility per function
- Self-contained and regeneratable
- Zero-BS implementation (no stubs or placeholders)

Public API:
    slugify: Convert text to URL-safe slug format
    titlecase: Convert text to Title Case format
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
    """Convert text to Title Case format.

    Capitalizes the first character of each word while preserving:
    - Exact whitespace (spaces, tabs, newlines)
    - Hyphens as word boundaries
    - Apostrophes in contractions (doesn't capitalize after apostrophe)
    - Unicode characters (accented letters remain accented)

    Word boundaries are defined as: spaces, tabs, newlines, and hyphens.

    Args:
        text: Input string or None. If None, returns empty string.

    Returns:
        Title Case formatted string with exact whitespace preserved.
        Returns empty string if input is None or empty.

    Examples:
        >>> titlecase("hello world")
        'Hello World'
        >>> titlecase("it's a test")
        "It's A Test"
        >>> titlecase("mother-in-law")
        'Mother-In-Law'
        >>> titlecase("café")
        'Café'
        >>> titlecase("  hello  world  ")
        '  Hello  World  '
        >>> titlecase(None)
        ''
    """
    if text is None:
        return ""

    if not text:
        return text

    result = []
    capitalize_next = True

    for char in text:
        if char in (" ", "\t", "\n", "-"):
            # Whitespace and hyphens are word boundaries
            result.append(char)
            capitalize_next = True
        elif char == "'":
            # Apostrophes don't trigger capitalization
            result.append(char)
        else:
            # Regular character
            if capitalize_next:
                result.append(char.upper())
                capitalize_next = False
            else:
                result.append(char.lower())

    return "".join(result)


__all__ = ["slugify", "titlecase"]
