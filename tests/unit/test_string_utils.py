"""Unit tests for string utility functions - TDD approach.

Tests the string utility functions:
- slugify: converts strings to URL-safe slugs
- titlecase: converts strings to Title Case

Following TDD approach - write tests first, then implement.

Test Coverage (slugify):
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

Test Coverage (titlecase):
- Basic title case conversion
- Empty string and None handling
- Whitespace preservation
- Numbers and special characters
- Hyphenated words and apostrophes
- Edge cases and idempotency
"""

import sys
from pathlib import Path

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


# titlecase function to be implemented
try:
    from amplihack.utils.string_utils import titlecase
except ImportError:
    # Define placeholder so tests can be written - THIS SHOULD FAIL
    def titlecase(text: str | None) -> str:
        """Placeholder - to be implemented."""
        raise NotImplementedError("titlecase not yet implemented")


class TestTitlecaseBasicFunctionality:
    """Test basic titlecase functionality."""

    def test_basic_hello_world(self):
        """Test basic conversion of simple text to title case."""
        result = titlecase("hello world")
        assert result == "Hello World", "Should convert 'hello world' to 'Hello World'"

    def test_single_word(self):
        """Test conversion of single word."""
        result = titlecase("hello")
        assert result == "Hello", "Should capitalize single word 'hello' to 'Hello'"

    def test_already_uppercase_word(self):
        """Test conversion of already uppercase text."""
        result = titlecase("HELLO")
        assert result == "Hello", "Should convert 'HELLO' to 'Hello'"

    def test_mixed_case_text(self):
        """Test conversion of mixed case text."""
        result = titlecase("hElLo WoRlD")
        assert result == "Hello World", "Should normalize mixed case to 'Hello World'"

    def test_single_character(self):
        """Test conversion of single character."""
        result = titlecase("a")
        assert result == "A", "Should capitalize single char 'a' to 'A'"

    def test_single_uppercase_character(self):
        """Test single uppercase character remains uppercase."""
        result = titlecase("A")
        assert result == "A", "Single uppercase 'A' should remain 'A'"


class TestTitlecaseEmptyAndNullHandling:
    """Test titlecase handling of empty and null inputs."""

    def test_empty_string(self):
        """Test handling of empty string input."""
        result = titlecase("")
        assert result == "", "Empty string should return empty string"

    def test_none_input(self):
        """Test handling of None input."""
        result = titlecase(None)
        assert result == "", "None should return empty string"


class TestTitlecaseWhitespaceHandling:
    """Test titlecase handling of various whitespace scenarios."""

    def test_multiple_spaces_preserved(self):
        """Test that multiple consecutive spaces are preserved."""
        result = titlecase("hello  world")
        assert result == "Hello  World", "Should preserve multiple spaces"

    def test_whitespace_only_preserved(self):
        """Test that whitespace-only strings are preserved."""
        result = titlecase("   ")
        assert result == "   ", "Whitespace-only string should be preserved"

    def test_newline_handling(self):
        """Test handling of newline characters."""
        result = titlecase("hello\nworld")
        assert result == "Hello\nWorld", "Should handle newline as word separator"

    def test_tab_handling(self):
        """Test handling of tab characters."""
        result = titlecase("hello\tworld")
        assert result == "Hello\tWorld", "Should handle tab as word separator"

    def test_leading_trailing_spaces(self):
        """Test handling of leading and trailing spaces."""
        result = titlecase(" hello ")
        assert result == " Hello ", "Should preserve leading/trailing spaces"


class TestTitlecaseNumbersAndSpecialChars:
    """Test titlecase handling of numbers and special characters."""

    def test_numbers_in_word(self):
        """Test handling of numbers within words."""
        result = titlecase("hello2world")
        assert result == "Hello2World", "Should handle numbers"

    def test_punctuation_preserved(self):
        """Test that punctuation is preserved and affects title case."""
        result = titlecase("hello, world!")
        assert result == "Hello, World!", "Should preserve punctuation"

    def test_hyphenated_words(self):
        """Test handling of hyphenated words."""
        result = titlecase("hello-world")
        assert result == "Hello-World", "Should handle hyphen"

    def test_apostrophe_handling(self):
        """Test handling of apostrophes in words."""
        result = titlecase("o'brien")
        assert result == "O'Brien", "Should handle apostrophe"


class TestTitlecaseEdgeCases:
    """Test titlecase edge cases and boundary conditions."""

    def test_numbers_only(self):
        """Test string containing only numbers."""
        result = titlecase("123")
        assert result == "123", "Numbers-only string should remain unchanged"

    def test_punctuation_only(self):
        """Test string containing only punctuation."""
        result = titlecase("...")
        assert result == "...", "Punctuation-only string should remain unchanged"

    def test_mixed_numbers_and_words(self):
        """Test mixed numbers and words."""
        result = titlecase("test123 hello")
        assert result == "Test123 Hello", "Should handle mixed numbers and words"

    def test_underscore_in_text(self):
        """Test handling of underscores."""
        result = titlecase("hello_world")
        assert result == "Hello_World", "Should handle underscore as separator"

    def test_parentheses(self):
        """Test parentheses in text."""
        result = titlecase("hello (world)")
        assert result == "Hello (World)", "Should handle parentheses"


class TestTitlecaseIdempotency:
    """Test titlecase idempotency."""

    def test_idempotent_basic(self):
        """Test that titlecase is idempotent on basic input."""
        original = "hello world"
        first_pass = titlecase(original)
        second_pass = titlecase(first_pass)
        assert first_pass == second_pass, "Titlecase should be idempotent"

    def test_idempotent_with_punctuation(self):
        """Test idempotency with punctuation."""
        original = "hello, world!"
        first_pass = titlecase(original)
        second_pass = titlecase(first_pass)
        assert first_pass == second_pass, "Should be idempotent with punctuation"


class TestTitlecaseTypeHandling:
    """Test titlecase type handling and error cases."""

    def test_returns_string_type(self):
        """Test that titlecase always returns a string."""
        result = titlecase("hello")
        assert isinstance(result, str), "Should return string type"

    def test_none_returns_string(self):
        """Test that None input returns string (not None)."""
        result = titlecase(None)
        assert isinstance(result, str), "None input should return string type"
        assert result == "", "None should return empty string"


class TestTitlecaseKnownLimitations:
    """Test documented str.title() behavior quirks."""

    def test_apostrophe_quirk_documented(self):
        """Document that str.title() capitalizes after apostrophe.

        This is a known limitation of str.title() - it treats any
        non-letter character as a word boundary. For example:
        - "it's" becomes "It'S" (not "It's")
        - "o'brien" becomes "O'Brien" (expected)

        For AP-style title case, use a dedicated library.
        """
        result = titlecase("it's")
        assert result == "It'S", "Known behavior: str.title() capitalizes after apostrophe"
