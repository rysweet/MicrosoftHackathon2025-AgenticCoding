"""Unit tests for string utility functions.

Tests the slugify, titlecase, and their _safe variants.

Test Coverage:
- Basic text to slug conversion
- Empty string handling
- Special character removal
- Unicode normalization (accents, diacritics)
- Multiple consecutive spaces
- Leading and trailing spaces
- Already valid slugs
- Numbers in strings
- Only special characters
- Mixed case conversion
- Consecutive hyphens
- Complex edge cases
- Type coercion (titlecase_safe)
- None handling (titlecase_safe)
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from amplihack.utils.string_utils import slugify, titlecase, titlecase_safe


class TestSlugify:
    """Test slugify function for converting strings to URL-safe slugs.

    The slugify function should:
    1. Apply NFD unicode normalization and convert to ASCII
    2. Convert to lowercase
    3. Remove special characters (keep alphanumeric + hyphens)
    4. Replace spaces with hyphens
    5. Replace consecutive hyphens with single hyphen
    6. Strip leading/trailing hyphens
    """

    def test_basic_hello_world(self):
        """Test basic conversion of simple text to slug."""
        result = slugify("Hello World")
        assert result == "hello-world"

    def test_empty_string(self):
        """Test handling of empty string input."""
        result = slugify("")
        assert result == ""

    def test_special_characters_removed(self):
        """Test removal of special characters."""
        result = slugify("Hello@World!")
        assert result == "hello-world"

    def test_unicode_normalization_cafe(self):
        """Test NFD unicode normalization with accented characters."""
        result = slugify("Café")
        assert result == "cafe"

    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces."""
        result = slugify("foo   bar")
        assert result == "foo-bar"

    def test_leading_trailing_spaces(self):
        """Test stripping of leading and trailing spaces."""
        result = slugify(" test ")
        assert result == "test"

    def test_already_valid_slug(self):
        """Test that valid slugs pass through unchanged."""
        result = slugify("hello-world")
        assert result == "hello-world"

    def test_numbers_preserved(self):
        """Test that numbers are preserved in slugs."""
        result = slugify("test123")
        assert result == "test123"

    def test_only_special_characters(self):
        """Test handling of string with only special characters."""
        result = slugify("!!!")
        assert result == ""

    def test_mixed_case_conversion(self):
        """Test mixed case is converted to lowercase."""
        result = slugify("HeLLo WoRLd")
        assert result == "hello-world"

    def test_consecutive_hyphens(self):
        """Test that consecutive hyphens are collapsed to single hyphen."""
        result = slugify("hello---world")
        assert result == "hello-world"

    def test_leading_trailing_hyphens_stripped(self):
        """Test that leading and trailing hyphens are removed."""
        result = slugify("-hello-world-")
        assert result == "hello-world"

    def test_unicode_complex_accents(self):
        """Test complex unicode characters with multiple accents."""
        result = slugify("Crème brûlée")
        assert result == "creme-brulee"

    def test_numbers_with_spaces(self):
        """Test numbers mixed with words and spaces."""
        result = slugify("Project 123 Version 2")
        assert result == "project-123-version-2"

    def test_underscores_removed(self):
        """Test that underscores are converted to hyphens."""
        result = slugify("hello_world")
        assert result == "hello-world"

    def test_dots_and_commas_removed(self):
        """Test removal of punctuation like dots and commas."""
        result = slugify("Hello, World.")
        assert result == "hello-world"

    def test_parentheses_removed(self):
        """Test removal of parentheses and brackets."""
        result = slugify("Hello (World)")
        assert result == "hello-world"

    def test_ampersand_removed(self):
        """Test removal of ampersand character."""
        result = slugify("Rock & Roll")
        assert result == "rock-roll"

    def test_quotes_removed(self):
        """Test removal of single and double quotes."""
        result = slugify('It\'s "Great"')
        assert result == "its-great"

    def test_slash_removed(self):
        """Test removal of forward and back slashes."""
        result = slugify("Hello/World\\Test")
        assert result == "hello-world-test"

    def test_very_long_string(self):
        """Test handling of very long strings."""
        long_text = "This is a very long string " * 10
        result = slugify(long_text.strip())
        assert result.startswith("this-is-a-very-long-string")
        assert result.count("--") == 0

    def test_unicode_from_multiple_languages(self):
        """Test unicode characters from various languages."""
        result = slugify("Héllo Wörld Česko")
        assert result.isascii()
        assert "-" in result or result.isalnum()

    def test_all_whitespace(self):
        """Test string with only whitespace characters."""
        result = slugify("   ")
        assert result == ""

    def test_tabs_and_newlines(self):
        """Test handling of tabs and newline characters."""
        result = slugify("Hello\tWorld\nTest")
        assert result == "hello-world-test"

    def test_emoji_removed(self):
        """Test removal of emoji characters."""
        result = slugify("Hello 😀 World")
        assert result == "hello-world"

    def test_html_tags_removed(self):
        """Test removal of HTML-like tags."""
        result = slugify("<div>Hello</div>")
        assert "hello" in result
        assert "<" not in result

    def test_mixed_alphanumeric_special(self):
        """Test complex mix of alphanumeric and special characters."""
        result = slugify("abc123!@#def456$%^")
        assert "abc123" in result
        assert "def456" in result

    def test_idempotency(self):
        """Test that slugify is idempotent."""
        original = "Hello World!"
        first_pass = slugify(original)
        second_pass = slugify(first_pass)
        assert first_pass == second_pass

    def test_numeric_only_string(self):
        """Test string with only numbers."""
        result = slugify("123456")
        assert result == "123456"

    def test_single_character(self):
        """Test single character inputs."""
        assert slugify("A") == "a"
        assert slugify("1") == "1"
        assert slugify("!") == ""

    def test_hyphen_separated_already(self):
        """Test input that's already hyphen-separated."""
        result = slugify("already-a-slug")
        assert result == "already-a-slug"


class TestTitlecase:
    """Test titlecase function for converting strings to Title Case."""

    def test_basic_hello_world(self):
        """Test basic conversion of simple text."""
        result = titlecase("hello world")
        assert result == "Hello World"

    def test_empty_string(self):
        """Test handling of empty string input."""
        result = titlecase("")
        assert result == ""

    def test_single_word(self):
        """Test single word conversion."""
        result = titlecase("hello")
        assert result == "Hello"

    def test_already_titlecase(self):
        """Test that already title-cased text passes through."""
        result = titlecase("Hello World")
        assert result == "Hello World"

    def test_all_uppercase(self):
        """Test all uppercase input."""
        result = titlecase("HELLO WORLD")
        assert result == "Hello World"

    def test_all_lowercase(self):
        """Test all lowercase input."""
        result = titlecase("hello world")
        assert result == "Hello World"

    def test_mixed_case(self):
        """Test mixed case input."""
        result = titlecase("hElLo WoRlD")
        assert result == "Hello World"

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        result = titlecase("version 2.0")
        assert result == "Version 2.0"

    def test_special_characters_preserved(self):
        """Test that special characters are preserved."""
        result = titlecase("hello, world!")
        assert result == "Hello, World!"

    def test_hyphenated_words(self):
        """Test hyphenated words (each part capitalized by str.title())."""
        result = titlecase("well-known fact")
        assert result == "Well-Known Fact"

    def test_whitespace_preserved(self):
        """Test that whitespace is preserved."""
        result = titlecase("hello   world")
        assert result == "Hello   World"

    def test_unicode_characters(self):
        """Test unicode characters."""
        result = titlecase("café résumé")
        assert result == "Café Résumé"

    def test_apostrophe_limitation(self):
        """Test known apostrophe limitation (documented behavior)."""
        # Python's str.title() capitalizes after apostrophes
        result = titlecase("don't stop")
        assert result == "Don'T Stop"  # Known limitation


class TestTitlecaseSafe:
    """Test titlecase_safe wrapper for type-safe title case conversion."""

    def test_none_returns_empty_string(self):
        """Test that None input returns empty string."""
        result = titlecase_safe(None)
        assert result == ""

    def test_integer_coercion(self):
        """Test that integer input is coerced to string."""
        result = titlecase_safe(42)
        assert result == "42"

    def test_negative_integer(self):
        """Test negative integer handling."""
        result = titlecase_safe(-123)
        assert result == "-123"

    def test_float_coercion(self):
        """Test that float input is coerced to string."""
        result = titlecase_safe(12.5)
        assert result == "12.5"

    def test_boolean_true(self):
        """Test boolean True handling."""
        result = titlecase_safe(True)
        assert result == "True"

    def test_boolean_false(self):
        """Test boolean False handling."""
        result = titlecase_safe(False)
        assert result == "False"

    def test_string_passthrough(self):
        """Test that string input behaves same as titlecase()."""
        result = titlecase_safe("hello world")
        assert result == "Hello World"

    def test_empty_string(self):
        """Test empty string input."""
        result = titlecase_safe("")
        assert result == ""

    def test_idempotency(self):
        """Test that titlecase_safe is idempotent."""
        original = "test value"
        first_pass = titlecase_safe(original)
        second_pass = titlecase_safe(first_pass)
        assert first_pass == second_pass

    def test_zero_integer(self):
        """Test zero integer."""
        result = titlecase_safe(0)
        assert result == "0"

    def test_large_integer(self):
        """Test large integer handling."""
        result = titlecase_safe(123456789)
        assert result == "123456789"

    def test_unicode_string_via_safe(self):
        """Test unicode string through safe wrapper."""
        result = titlecase_safe("café")
        assert result == "Café"
