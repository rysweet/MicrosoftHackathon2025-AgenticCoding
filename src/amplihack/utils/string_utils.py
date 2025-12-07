"""String utility functions for text processing.

This module provides utilities for converting strings to URL-safe formats
and title case transformations.

Philosophy:
- Ruthless simplicity (stdlib only)
- Single responsibility per function
- Self-contained and regeneratable
- Zero-BS implementation (no stubs or placeholders)

Public API:
    slugify: Convert text to URL-safe slug format
    titlecase: Convert text to title case
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
    """Convert text to title case, capitalizing first letter of each word.

    Word boundaries are: space, hyphen, underscore, tab, newline, carriage return.
    Preserves whitespace positions and counts exactly.

    Args:
        text: Input string to convert.

    Returns:
        Title-cased string with first character of each word uppercased
        and remaining characters lowercased.

    Examples:
        >>> titlecase("hello world")
        'Hello World'
        >>> titlecase("hello-world")
        'Hello-World'
        >>> titlecase("it's a test")
        "It's A Test"
        >>> titlecase("  hello  ")
        '  Hello  '
    """
    if not text:
        return text

    word_boundaries = {" ", "-", "_", "\t", "\n", "\r"}
    result = []
    new_word = True

    for char in text:
        if char in word_boundaries:
            result.append(char)
            new_word = True
        elif new_word:
            result.append(char.upper())
            # Only end new_word state if character is alphabetic
            if char.isalpha():
                new_word = False
        else:
            result.append(char.lower())

    return "".join(result)


__all__ = ["slugify", "titlecase"]
