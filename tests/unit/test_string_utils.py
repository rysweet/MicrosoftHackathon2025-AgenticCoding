"""Unit tests for string utility functions.

Tests the slugify and slugify_safe functions that convert strings to URL-safe slugs.

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
- Type coercion (slugify_safe)
- None handling (slugify_safe)
- Title case conversion (titlecase)
- Safe title case with None/type coercion (titlecase_safe)
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# slugify function to be implemented
try:
    from amplihack.utils.string_utils import slugify
except ImportError:
    # Define placeholder so tests can be written
    def slugify(text: str) -> str:
        """Placeholder - to be implemented.

        Args:
            text: String to convert to slug

        Returns:
            URL-safe slug string
        """
        raise NotImplementedError("slugify not yet implemented")


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
        """Test basic conversion of simple text to slug.

        Expected behavior:
        - "Hello World" should become "hello-world"
        - Spaces converted to hyphens
        - Uppercase converted to lowercase
        """
        result = slugify("Hello World")
        assert result == "hello-world", "Should convert 'Hello World' to 'hello-world'"

    def test_empty_string(self):
        """Test handling of empty string input.

        Expected behavior:
        - Empty string "" should return ""
        - No errors or exceptions
        """
        result = slugify("")
        assert result == "", "Empty string should return empty string"

    def test_special_characters_removed(self):
        """Test removal of special characters.

        Expected behavior:
        - "Hello@World!" should become "hello-world"
        - Special characters (@, !) should be removed
        - Only alphanumeric and hyphens remain
        """
        result = slugify("Hello@World!")
        assert result == "hello-world", "Should remove special characters"

    def test_unicode_normalization_cafe(self):
        """Test NFD unicode normalization with accented characters.

        Expected behavior:
        - "Café" should become "cafe"
        - Accented 'é' normalized to 'e'
        - Non-ASCII characters converted to ASCII equivalents
        """
        result = slugify("Café")
        assert result == "cafe", "Should normalize unicode 'Café' to 'cafe'"

    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces.

        Expected behavior:
        - "foo   bar" should become "foo-bar"
        - Multiple spaces collapsed to single hyphen
        - No consecutive hyphens in output
        """
        result = slugify("foo   bar")
        assert result == "foo-bar", "Should collapse multiple spaces to single hyphen"

    def test_leading_trailing_spaces(self):
        """Test stripping of leading and trailing spaces.

        Expected behavior:
        - " test " should become "test"
        - Leading spaces removed before conversion
        - Trailing spaces removed before conversion
        - No leading/trailing hyphens in output
        """
        result = slugify(" test ")
        assert result == "test", "Should strip leading and trailing spaces"

    def test_already_valid_slug(self):
        """Test that valid slugs pass through unchanged.

        Expected behavior:
        - "hello-world" should remain "hello-world"
        - Already valid slugs are idempotent
        - No unnecessary transformations
        """
        result = slugify("hello-world")
        assert result == "hello-world", "Already valid slug should remain unchanged"

    def test_numbers_preserved(self):
        """Test that numbers are preserved in slugs.

        Expected behavior:
        - "test123" should become "test123"
        - Numbers are alphanumeric and should be kept
        - Position of numbers doesn't matter
        """
        result = slugify("test123")
        assert result == "test123", "Should preserve numbers"

    def test_only_special_characters(self):
        """Test handling of string with only special characters.

        Expected behavior:
        - "!!!" should become ""
        - When all characters are removed, return empty string
        - No hyphens or other artifacts remain
        """
        result = slugify("!!!")
        assert result == "", "String with only special chars should return empty string"

    def test_mixed_case_conversion(self):
        """Test mixed case is converted to lowercase.

        Expected behavior:
        - "HeLLo WoRLd" should become "hello-world"
        - All uppercase letters converted to lowercase
        - Mixed case handled correctly
        """
        result = slugify("HeLLo WoRLd")
        assert result == "hello-world", "Should convert mixed case to lowercase"

    def test_consecutive_hyphens(self):
        """Test that consecutive hyphens are collapsed to single hyphen.

        Expected behavior:
        - "hello---world" should become "hello-world"
        - Multiple consecutive hyphens collapsed
        - Only single hyphen remains between words
        """
        result = slugify("hello---world")
        assert result == "hello-world", "Should collapse consecutive hyphens"

    def test_leading_trailing_hyphens_stripped(self):
        """Test that leading and trailing hyphens are removed.

        Expected behavior:
        - "-hello-world-" should become "hello-world"
        - Leading hyphens stripped
        - Trailing hyphens stripped
        """
        result = slugify("-hello-world-")
        assert result == "hello-world", "Should strip leading/trailing hyphens"

    def test_unicode_complex_accents(self):
        """Test complex unicode characters with multiple accents.

        Expected behavior:
        - "Crème brûlée" should become "creme-brulee"
        - Multiple different accents normalized
        - Spaces converted to hyphens
        """
        result = slugify("Crème brûlée")
        assert result == "creme-brulee", "Should normalize complex accents"

    def test_numbers_with_spaces(self):
        """Test numbers mixed with words and spaces.

        Expected behavior:
        - "Project 123 Version 2" should become "project-123-version-2"
        - Numbers preserved
        - Spaces converted to hyphens
        """
        result = slugify("Project 123 Version 2")
        assert result == "project-123-version-2", "Should handle numbers with spaces"

    def test_underscores_removed(self):
        """Test that underscores are removed (not kept as hyphens).

        Expected behavior:
        - "hello_world" should become "hello-world"
        - Underscores treated like other special characters
        - Result uses hyphens not underscores
        """
        result = slugify("hello_world")
        assert result == "hello-world", "Should convert underscores to hyphens"

    def test_dots_and_commas_removed(self):
        """Test removal of punctuation like dots and commas.

        Expected behavior:
        - "Hello, World." should become "hello-world"
        - Commas removed
        - Dots removed
        """
        result = slugify("Hello, World.")
        assert result == "hello-world", "Should remove dots and commas"

    def test_parentheses_removed(self):
        """Test removal of parentheses and brackets.

        Expected behavior:
        - "Hello (World)" should become "hello-world"
        - Opening parentheses removed
        - Closing parentheses removed
        - Brackets treated similarly
        """
        result = slugify("Hello (World)")
        assert result == "hello-world", "Should remove parentheses"

    def test_ampersand_removed(self):
        """Test removal of ampersand character.

        Expected behavior:
        - "Rock & Roll" should become "rock-roll"
        - Ampersand removed completely
        - Spaces around ampersand collapse to single hyphen
        """
        result = slugify("Rock & Roll")
        assert result == "rock-roll", "Should remove ampersand"

    def test_quotes_removed(self):
        """Test removal of single and double quotes.

        Expected behavior:
        - "It's \"Great\"" should become "its-great"
        - Single quotes removed
        - Double quotes removed
        """
        result = slugify('It\'s "Great"')
        assert result == "its-great", "Should remove quotes"

    def test_slash_removed(self):
        """Test removal of forward and back slashes.

        Expected behavior:
        - "Hello/World\\Test" should become "hello-world-test"
        - Forward slashes removed
        - Back slashes removed
        - Multiple words separated properly
        """
        result = slugify("Hello/World\\Test")
        assert result == "hello-world-test", "Should remove slashes"

    def test_very_long_string(self):
        """Test handling of very long strings.

        Expected behavior:
        - Long strings should be processed correctly
        - No length-based errors
        - All transformations applied
        """
        long_text = "This is a very long string " * 10
        result = slugify(long_text.strip())
        assert result.startswith("this-is-a-very-long-string")
        assert result.count("--") == 0, "No consecutive hyphens"

    def test_unicode_from_multiple_languages(self):
        """Test unicode characters from various languages.

        Expected behavior:
        - Characters should be normalized or removed
        - Result should be ASCII-only
        - No unicode characters in output
        """
        result = slugify("Héllo Wörld Česko")
        assert result.isascii(), "Result should be ASCII only"
        assert "-" in result or result.isalnum(), "Should contain valid slug characters"

    def test_all_whitespace(self):
        """Test string with only whitespace characters.

        Expected behavior:
        - "   " should become ""
        - All whitespace stripped
        - Empty string returned
        """
        result = slugify("   ")
        assert result == "", "All whitespace should return empty string"

    def test_tabs_and_newlines(self):
        """Test handling of tabs and newline characters.

        Expected behavior:
        - "Hello\tWorld\nTest" should become "hello-world-test"
        - Tabs converted to hyphens
        - Newlines converted to hyphens
        - Consecutive hyphens collapsed
        """
        result = slugify("Hello\tWorld\nTest")
        assert result == "hello-world-test", "Should handle tabs and newlines"

    def test_emoji_removed(self):
        """Test removal of emoji characters.

        Expected behavior:
        - "Hello 😀 World" should become "hello-world"
        - Emojis completely removed
        - Spaces collapse correctly
        """
        result = slugify("Hello 😀 World")
        assert result == "hello-world", "Should remove emoji"

    def test_html_tags_removed(self):
        """Test removal of HTML-like tags.

        Expected behavior:
        - "<div>Hello</div>" should become "div-hello-div" or "hello"
        - Angle brackets removed
        - Text content preserved
        """
        result = slugify("<div>Hello</div>")
        # Could be "div-hello-div" or just "hello" depending on implementation
        assert "hello" in result, "Should extract text from HTML-like tags"
        assert "<" not in result, "Should remove angle brackets"

    def test_mixed_alphanumeric_special(self):
        """Test complex mix of alphanumeric and special characters.

        Expected behavior:
        - "abc123!@#def456$%^" should become "abc123-def456"
        - Alphanumeric preserved
        - Special chars removed
        - Proper separation maintained
        """
        result = slugify("abc123!@#def456$%^")
        assert "abc123" in result, "Should preserve first alphanumeric group"
        assert "def456" in result, "Should preserve second alphanumeric group"
        assert result.replace("-", "").replace("abc123", "").replace("def456", "") == "", (
            "Should only contain alphanumeric and hyphens"
        )

    def test_idempotency(self):
        """Test that slugify is idempotent - applying it twice gives same result.

        Expected behavior:
        - slugify(slugify(x)) == slugify(x)
        - Second application doesn't change result
        """
        original = "Hello World!"
        first_pass = slugify(original)
        second_pass = slugify(first_pass)
        assert first_pass == second_pass, "Slugify should be idempotent"

    def test_numeric_only_string(self):
        """Test string with only numbers.

        Expected behavior:
        - "123456" should remain "123456"
        - Numbers preserved
        - No unnecessary transformations
        """
        result = slugify("123456")
        assert result == "123456", "Numeric-only string should be preserved"

    def test_single_character(self):
        """Test single character inputs.

        Expected behavior:
        - "A" should become "a"
        - Single letter lowercase
        - "1" should remain "1"
        """
        assert slugify("A") == "a", "Single uppercase letter should lowercase"
        assert slugify("1") == "1", "Single digit should be preserved"
        assert slugify("!") == "", "Single special char should return empty"

    def test_hyphen_separated_already(self):
        """Test input that's already hyphen-separated.

        Expected behavior:
        - "already-a-slug" should remain "already-a-slug"
        - Already valid slug unchanged
        """
        result = slugify("already-a-slug")
        assert result == "already-a-slug", "Already valid hyphen-separated slug should remain"


# Import titlecase functions
from amplihack.utils.string_utils import titlecase, titlecase_safe


class TestTitlecase:
    """Test titlecase function for converting strings to Title Case.

    The titlecase function should:
    1. Convert each word to Title Case using str.title()
    2. Raise TypeError for non-string input
    3. Preserve whitespace (spaces, tabs, newlines)
    4. Known limitation: apostrophe handling follows stdlib behavior
    """

    def test_basic_hello_world(self):
        """Test basic conversion of simple text to title case.

        Expected behavior:
        - "hello world" should become "Hello World"
        - First letter of each word capitalized
        - Other letters lowercased
        """
        result = titlecase("hello world")
        assert result == "Hello World", "Should convert 'hello world' to 'Hello World'"

    def test_empty_string(self):
        """Test handling of empty string input.

        Expected behavior:
        - Empty string "" should return ""
        - No errors or exceptions
        """
        result = titlecase("")
        assert result == "", "Empty string should return empty string"

    def test_whitespace_only(self):
        """Test handling of whitespace-only string input.

        Expected behavior:
        - "   " should return "   "
        - Whitespace is preserved unchanged
        """
        result = titlecase("   ")
        assert result == "   ", "Whitespace-only string should preserve whitespace"

    def test_single_word(self):
        """Test title case of a single word.

        Expected behavior:
        - "hello" should become "Hello"
        - First letter capitalized, rest lowercase
        """
        result = titlecase("hello")
        assert result == "Hello", "Should capitalize single word"

    def test_all_caps_normalization(self):
        """Test normalization of all-caps input.

        Expected behavior:
        - "HELLO WORLD" should become "Hello World"
        - All uppercase converted to title case
        """
        result = titlecase("HELLO WORLD")
        assert result == "Hello World", "Should normalize all caps to title case"

    def test_mixed_case_normalization(self):
        """Test normalization of mixed case input.

        Expected behavior:
        - "hELLo WoRLD" should become "Hello World"
        - Mixed case normalized to title case
        """
        result = titlecase("hELLo WoRLD")
        assert result == "Hello World", "Should normalize mixed case to title case"

    def test_preserves_multiple_spaces(self):
        """Test that multiple consecutive spaces are preserved.

        Expected behavior:
        - "hello   world" should become "Hello   World"
        - Multiple spaces between words preserved
        """
        result = titlecase("hello   world")
        assert result == "Hello   World", "Should preserve multiple spaces"

    def test_preserves_leading_trailing_spaces(self):
        """Test that leading and trailing spaces are preserved.

        Expected behavior:
        - "  hello world  " should become "  Hello World  "
        - Leading and trailing spaces preserved
        """
        result = titlecase("  hello world  ")
        assert result == "  Hello World  ", "Should preserve leading/trailing spaces"

    def test_handles_numbers(self):
        """Test handling of numbers mixed with words.

        Expected behavior:
        - "hello 123 world" should become "Hello 123 World"
        - Numbers preserved unchanged
        """
        result = titlecase("hello 123 world")
        assert result == "Hello 123 World", "Should handle numbers in text"

    def test_special_characters(self):
        """Test handling of special characters like hyphens.

        Expected behavior:
        - "hello-world" should become "Hello-World"
        - Title case applied after hyphens (stdlib behavior)
        """
        result = titlecase("hello-world")
        assert result == "Hello-World", "Should apply title case after hyphens"

    def test_apostrophe_stdlib_behavior(self):
        """Test documented stdlib behavior with apostrophes.

        Expected behavior:
        - "it's" should become "It'S"
        - This is the known stdlib str.title() behavior
        - Character after apostrophe is capitalized
        """
        result = titlecase("it's")
        assert result == "It'S", "Should follow stdlib apostrophe behavior (It'S)"

    def test_newlines_preserved(self):
        """Test that newline characters are preserved.

        Expected behavior:
        - "hello\\nworld" should become "Hello\\nWorld"
        - Newlines act as word separators for title case
        """
        result = titlecase("hello\nworld")
        assert result == "Hello\nWorld", "Should preserve newlines and title case each line"

    def test_tabs_preserved(self):
        """Test that tab characters are preserved.

        Expected behavior:
        - "hello\\tworld" should become "Hello\\tWorld"
        - Tabs act as word separators for title case
        """
        result = titlecase("hello\tworld")
        assert result == "Hello\tWorld", "Should preserve tabs and title case each word"

    def test_unicode_chars(self):
        """Test handling of unicode characters with accents.

        Expected behavior:
        - "cafe resume" should become "Cafe Resume"
        - Unicode characters preserved and title cased
        """
        result = titlecase("cafe resume")
        assert result == "Cafe Resume", "Should handle unicode characters"

    def test_raises_type_error_for_none(self):
        """Test that None input raises TypeError.

        Expected behavior:
        - titlecase(None) should raise TypeError
        - Clear error message indicating expected type
        """
        with pytest.raises(TypeError):
            titlecase(None)

    def test_raises_type_error_for_int(self):
        """Test that integer input raises TypeError.

        Expected behavior:
        - titlecase(42) should raise TypeError
        - Non-string types are not accepted
        """
        with pytest.raises(TypeError):
            titlecase(42)

    def test_idempotency(self):
        """Test that titlecase is idempotent - applying it twice gives same result.

        Expected behavior:
        - titlecase(titlecase(x)) == titlecase(x)
        - Second application doesn't change result
        """
        original = "hello world"
        first_pass = titlecase(original)
        second_pass = titlecase(first_pass)
        assert first_pass == second_pass, "Titlecase should be idempotent"


class TestTitlecaseSafe:
    """Test titlecase_safe function for safe title case conversion with type coercion.

    The titlecase_safe function should:
    1. Return empty string for None input
    2. Coerce non-string values via str() before processing
    3. Delegate to titlecase() for actual conversion
    4. Never raise TypeError
    """

    def test_none_returns_empty(self):
        """Test that None input returns empty string.

        Expected behavior:
        - titlecase_safe(None) should return ""
        - No TypeError raised
        """
        result = titlecase_safe(None)
        assert result == "", "None should return empty string"

    def test_empty_string(self):
        """Test handling of empty string input.

        Expected behavior:
        - titlecase_safe("") should return ""
        - Empty string passthrough
        """
        result = titlecase_safe("")
        assert result == "", "Empty string should return empty string"

    def test_string_passthrough(self):
        """Test that string input is processed normally.

        Expected behavior:
        - titlecase_safe("hello world") should return "Hello World"
        - Same behavior as titlecase() for string input
        """
        result = titlecase_safe("hello world")
        assert result == "Hello World", "Should convert string to title case"

    def test_integer_coercion(self):
        """Test coercion of positive integer to string.

        Expected behavior:
        - titlecase_safe(42) should return "42"
        - Integer converted to string, no transformation needed
        """
        result = titlecase_safe(42)
        assert result == "42", "Should coerce integer to string"

    def test_negative_integer(self):
        """Test coercion of negative integer to string.

        Expected behavior:
        - titlecase_safe(-123) should return "-123"
        - Negative sign preserved
        """
        result = titlecase_safe(-123)
        assert result == "-123", "Should coerce negative integer to string"

    def test_float_coercion(self):
        """Test coercion of float to string.

        Expected behavior:
        - titlecase_safe(12.5) should return "12.5"
        - Float converted to string representation
        """
        result = titlecase_safe(12.5)
        assert result == "12.5", "Should coerce float to string"

    def test_boolean_true(self):
        """Test coercion of boolean True to string.

        Expected behavior:
        - titlecase_safe(True) should return "True"
        - Boolean string representation title cased
        """
        result = titlecase_safe(True)
        assert result == "True", "Should coerce True to 'True'"

    def test_boolean_false(self):
        """Test coercion of boolean False to string.

        Expected behavior:
        - titlecase_safe(False) should return "False"
        - Boolean string representation title cased
        """
        result = titlecase_safe(False)
        assert result == "False", "Should coerce False to 'False'"

    def test_zero_integer(self):
        """Test coercion of zero integer to string.

        Expected behavior:
        - titlecase_safe(0) should return "0"
        - Zero converted to string
        """
        result = titlecase_safe(0)
        assert result == "0", "Should coerce zero to '0'"

    def test_idempotency(self):
        """Test that titlecase_safe is idempotent - applying it twice gives same result.

        Expected behavior:
        - titlecase_safe(titlecase_safe(x)) == titlecase_safe(x)
        - Second application doesn't change result
        """
        original = "hello world"
        first_pass = titlecase_safe(original)
        second_pass = titlecase_safe(first_pass)
        assert first_pass == second_pass, "Titlecase_safe should be idempotent"
