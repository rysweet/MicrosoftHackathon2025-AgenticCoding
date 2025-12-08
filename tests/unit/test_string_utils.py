"""Unit tests for string utility functions - TDD approach.

Tests the slugify function that converts strings to URL-safe slugs.
Function to be implemented in amplihack/utils/string_utils.py

Following TDD approach - these tests should FAIL initially as slugify is not implemented.

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
    # Define placeholder so tests can be written (TDD approach)
    def titlecase(text: str | None) -> str:
        """Placeholder - to be implemented.

        Args:
            text: String to convert to title case

        Returns:
            Title case string with first char of each word capitalized
        """
        raise NotImplementedError("titlecase not yet implemented")


class TestTitlecase:
    """Test titlecase function for converting strings to Title Case.

    The titlecase function should:
    1. Capitalize the first character of each word
    2. Convert rest of each word to lowercase
    3. Treat whitespace and hyphens as word boundaries
    4. NOT treat apostrophes as word boundaries
    5. Preserve unicode characters
    6. Return empty string for None or empty input
    7. Preserve exact whitespace (multiple spaces, tabs, newlines)
    """

    def test_basic_hello_world(self):
        """Test basic conversion of simple text to title case.

        Expected behavior:
        - "hello world" should become "Hello World"
        - First char of each word capitalized
        - Rest of each word lowercase
        """
        result = titlecase("hello world")
        assert result == "Hello World", "Should convert 'hello world' to 'Hello World'"

    def test_none_input(self):
        """Test handling of None input.

        Expected behavior:
        - None should return ""
        - No errors or exceptions
        """
        result = titlecase(None)
        assert result == "", "None should return empty string"

    def test_empty_string(self):
        """Test handling of empty string input.

        Expected behavior:
        - Empty string "" should return ""
        - No errors or exceptions
        """
        result = titlecase("")
        assert result == "", "Empty string should return empty string"

    def test_single_word(self):
        """Test conversion of a single word.

        Expected behavior:
        - "hello" should become "Hello"
        - First letter capitalized
        - Rest lowercase
        """
        result = titlecase("hello")
        assert result == "Hello", "Should convert 'hello' to 'Hello'"

    def test_all_uppercase(self):
        """Test conversion of ALL CAPS text.

        Expected behavior:
        - "HELLO WORLD" should become "Hello World"
        - First char stays uppercase
        - Rest converted to lowercase
        """
        result = titlecase("HELLO WORLD")
        assert result == "Hello World", "Should convert 'HELLO WORLD' to 'Hello World'"

    def test_mixed_case(self):
        """Test conversion of mixed case text.

        Expected behavior:
        - "hElLo WoRlD" should become "Hello World"
        - Irregular casing normalized
        - First char uppercase, rest lowercase per word
        """
        result = titlecase("hElLo WoRlD")
        assert result == "Hello World", "Should convert 'hElLo WoRlD' to 'Hello World'"

    def test_multiple_spaces_preserved(self):
        """Test that multiple consecutive spaces are preserved exactly.

        Expected behavior:
        - "hello   world" should become "Hello   World"
        - Three spaces preserved between words
        - Each word still title-cased properly
        """
        result = titlecase("hello   world")
        assert result == "Hello   World", "Should preserve multiple spaces: 'Hello   World'"

    def test_leading_trailing_spaces_preserved(self):
        """Test that leading and trailing spaces are preserved.

        Expected behavior:
        - "  hello  " should become "  Hello  "
        - Leading spaces preserved
        - Trailing spaces preserved
        - Word still title-cased
        """
        result = titlecase("  hello  ")
        assert result == "  Hello  ", "Should preserve leading/trailing spaces: '  Hello  '"

    def test_tabs_and_newlines(self):
        """Test handling of tabs and newline characters as word boundaries.

        Expected behavior:
        - "hello\\tworld\\ntest" should become "Hello\\tWorld\\nTest"
        - Tab treated as word boundary
        - Newline treated as word boundary
        - Each word title-cased
        """
        result = titlecase("hello\tworld\ntest")
        assert result == "Hello\tWorld\nTest", "Should handle tabs and newlines as word boundaries"

    def test_hyphens_as_word_boundaries(self):
        """Test that hyphens act as word boundaries.

        Expected behavior:
        - "mother-in-law" should become "Mother-In-Law"
        - Each hyphen-separated segment treated as word
        - Hyphens preserved
        """
        result = titlecase("mother-in-law")
        assert result == "Mother-In-Law", "Should treat hyphens as word boundaries: 'Mother-In-Law'"

    def test_apostrophes_not_word_boundaries(self):
        """Test that apostrophes do NOT trigger new word capitalization.

        Expected behavior:
        - "it's a test" should become "It's A Test"
        - Apostrophe does not start a new word
        - 's' after apostrophe stays lowercase
        """
        result = titlecase("it's a test")
        assert result == "It's A Test", (
            "Apostrophes should not trigger capitalization: 'It's A Test'"
        )

    def test_unicode_accents_preserved(self):
        """Test that unicode/accented characters are preserved.

        Expected behavior:
        - "café" should become "Café"
        - Accent on e preserved
        - First letter capitalized
        """
        result = titlecase("café")
        assert result == "Café", "Should preserve unicode accents: 'Café'"

    def test_numbers_in_text(self):
        """Test handling of numbers mixed with text.

        Expected behavior:
        - "hello123 world" should become "Hello123 World"
        - Numbers preserved inline
        - Words still title-cased
        """
        result = titlecase("hello123 world")
        assert result == "Hello123 World", "Should preserve numbers: 'Hello123 World'"

    def test_idempotency(self):
        """Test that titlecase is idempotent - applying it twice gives same result.

        Expected behavior:
        - titlecase(titlecase(x)) == titlecase(x)
        - Already title-cased text unchanged
        - "Hello World" stays "Hello World"
        """
        original = "Hello World"
        result = titlecase(original)
        assert result == "Hello World", "Already title case should remain unchanged"

        # Double application
        double_result = titlecase(titlecase("hello world"))
        single_result = titlecase("hello world")
        assert double_result == single_result, "Titlecase should be idempotent"

    def test_single_character(self):
        """Test single character inputs.

        Expected behavior:
        - "a" should become "A"
        - Single lowercase letter capitalized
        """
        result = titlecase("a")
        assert result == "A", "Single character 'a' should become 'A'"

    def test_punctuation_preserved(self):
        """Test that punctuation is preserved in position.

        Expected behavior:
        - "hello, world!" should become "Hello, World!"
        - Comma preserved after Hello
        - Exclamation preserved after World
        - Words still title-cased
        """
        result = titlecase("hello, world!")
        assert result == "Hello, World!", "Should preserve punctuation: 'Hello, World!'"

    def test_complex_contraction(self):
        """Test complex contractions with apostrophes.

        Expected behavior:
        - "don't won't can't" should become "Don't Won't Can't"
        - Each contraction treated as single word
        - Apostrophe internal to word
        """
        result = titlecase("don't won't can't")
        assert result == "Don't Won't Can't", "Should handle contractions: 'Don't Won't Can't'"

    def test_possessive_apostrophe(self):
        """Test possessive apostrophes.

        Expected behavior:
        - "john's book" should become "John's Book"
        - Possessive 's stays lowercase
        """
        result = titlecase("john's book")
        assert result == "John's Book", "Should handle possessive: 'John's Book'"

    def test_hyphen_with_spaces(self):
        """Test hyphens combined with spaces.

        Expected behavior:
        - "well - known" should become "Well - Known"
        - Spaces around hyphen preserved
        - Words on both sides title-cased
        """
        result = titlecase("well - known")
        assert result == "Well - Known", "Should handle hyphen with spaces: 'Well - Known'"

    def test_only_whitespace(self):
        """Test string with only whitespace characters.

        Expected behavior:
        - "   " should return "   "
        - Whitespace preserved but no words to capitalize
        """
        result = titlecase("   ")
        assert result == "   ", "Whitespace-only string should preserve whitespace"

    def test_numeric_only_string(self):
        """Test string with only numbers.

        Expected behavior:
        - "123456" should remain "123456"
        - Numbers have no case to change
        """
        result = titlecase("123456")
        assert result == "123456", "Numeric-only string should be unchanged"

    def test_special_characters_start_of_word(self):
        """Test words starting with special characters.

        Expected behavior:
        - "$money talks" should become "$money Talks"
        - Special characters have no case, rest of word lowercase
        - Next word after space capitalizes normally
        - Follows ruthless simplicity: first char is $, not a letter
        """
        result = titlecase("$money talks")
        assert result == "$money Talks", "Special char prefix means rest of word is lowercase"

    def test_all_lowercase_already(self):
        """Test that lowercase input is properly title-cased.

        Expected behavior:
        - "the quick brown fox" should become "The Quick Brown Fox"
        """
        result = titlecase("the quick brown fox")
        assert result == "The Quick Brown Fox", "Should title-case: 'The Quick Brown Fox'"

    def test_mixed_separators(self):
        """Test mixing multiple separator types.

        Expected behavior:
        - "hello-world test" should become "Hello-World Test"
        - Both hyphen and space act as word boundaries
        """
        result = titlecase("hello-world test")
        assert result == "Hello-World Test", "Should handle mixed separators: 'Hello-World Test'"

    def test_consecutive_hyphens(self):
        """Test consecutive hyphens between words.

        Expected behavior:
        - "hello--world" should become "Hello--World"
        - Both hyphens preserved
        - Words on both sides title-cased
        """
        result = titlecase("hello--world")
        assert result == "Hello--World", "Should preserve consecutive hyphens: 'Hello--World'"

    def test_apostrophe_at_start(self):
        """Test word starting with apostrophe.

        Expected behavior:
        - "'twas the night" should become "'Twas The Night"
        - First alphabetic char after apostrophe capitalized
        """
        result = titlecase("'twas the night")
        assert result == "'Twas The Night", "Should handle leading apostrophe: ''Twas The Night'"

    def test_single_letter_words(self):
        """Test single letter words.

        Expected behavior:
        - "i am a hero" should become "I Am A Hero"
        - Each single letter word capitalized
        """
        result = titlecase("i am a hero")
        assert result == "I Am A Hero", "Should capitalize single letter words: 'I Am A Hero'"

    def test_newline_only(self):
        """Test string with only newline.

        Expected behavior:
        - "\\n" should return "\\n"
        - Newline preserved but no words to capitalize
        """
        result = titlecase("\n")
        assert result == "\n", "Newline-only string should preserve newline"

    def test_tab_only(self):
        """Test string with only tab.

        Expected behavior:
        - "\\t" should return "\\t"
        - Tab preserved but no words to capitalize
        """
        result = titlecase("\t")
        assert result == "\t", "Tab-only string should preserve tab"
