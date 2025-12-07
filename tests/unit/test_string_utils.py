"""Unit tests for string utility functions.

Tests the slugify and titlecase functions for string transformations.
Functions implemented in amplihack/utils/string_utils.py

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
    # Define placeholder so tests can be written
    def titlecase(text: str) -> str:
        """Placeholder - to be implemented.

        Args:
            text: String to convert to title case

        Returns:
            Title cased string with preserved whitespace
        """
        raise NotImplementedError("titlecase not yet implemented")


class TestTitlecase:
    """Test titlecase function for converting strings to title case.

    The titlecase function should:
    1. Capitalize the first letter of each word
    2. Lowercase all other letters in each word
    3. Treat space, hyphen, underscore, tab, and newline as word boundaries
    4. NOT treat apostrophes as word boundaries (it's -> It's, not It'S)
    5. Preserve exact whitespace (multiple spaces, leading/trailing)
    6. Be a pure function with O(n) complexity using stdlib only
    """

    def test_empty_string(self):
        """Test handling of empty string input.

        Expected behavior:
        - Empty string "" should return ""
        - No errors or exceptions
        """
        result = titlecase("")
        assert result == "", "Empty string should return empty string"

    def test_single_word_lowercase(self):
        """Test single lowercase word conversion.

        Expected behavior:
        - "hello" should become "Hello"
        - First letter capitalized, rest lowercase
        """
        result = titlecase("hello")
        assert result == "Hello", "Single lowercase word should be capitalized"

    def test_basic_two_words(self):
        """Test basic two-word conversion with space separator.

        Expected behavior:
        - "hello world" should become "Hello World"
        - Each word's first letter capitalized
        - Space preserved as separator
        """
        result = titlecase("hello world")
        assert result == "Hello World", "Basic two words should be title cased"

    def test_all_uppercase_input(self):
        """Test conversion of all uppercase input.

        Expected behavior:
        - "HELLO WORLD" should become "Hello World"
        - All letters after first lowercased
        - First letter of each word capitalized
        """
        result = titlecase("HELLO WORLD")
        assert result == "Hello World", "All uppercase should convert to title case"

    def test_mixed_case_input(self):
        """Test conversion of mixed case input.

        Expected behavior:
        - "hELLo WoRLd" should become "Hello World"
        - Irregular casing normalized to title case
        """
        result = titlecase("hELLo WoRLd")
        assert result == "Hello World", "Mixed case should normalize to title case"

    def test_hyphen_word_boundary(self):
        """Test hyphen as word boundary.

        Expected behavior:
        - "hello-world" should become "Hello-World"
        - Hyphen acts as word separator
        - Hyphen preserved in output
        """
        result = titlecase("hello-world")
        assert result == "Hello-World", "Hyphen should act as word boundary"

    def test_underscore_word_boundary(self):
        """Test underscore as word boundary.

        Expected behavior:
        - "hello_world" should become "Hello_World"
        - Underscore acts as word separator
        - Underscore preserved in output
        """
        result = titlecase("hello_world")
        assert result == "Hello_World", "Underscore should act as word boundary"

    def test_apostrophe_not_boundary(self):
        """Test that apostrophe is NOT a word boundary.

        Expected behavior:
        - "it's" should become "It's"
        - Apostrophe is NOT a word separator
        - Letter after apostrophe stays lowercase
        """
        result = titlecase("it's")
        assert result == "It's", "Apostrophe should NOT act as word boundary"

    def test_multiple_spaces_preserved(self):
        """Test preservation of multiple consecutive spaces.

        Expected behavior:
        - "hello  world" should become "Hello  World"
        - Double space preserved exactly
        - Words still properly capitalized
        """
        result = titlecase("hello  world")
        assert result == "Hello  World", "Multiple spaces should be preserved exactly"

    def test_leading_trailing_spaces_preserved(self):
        """Test preservation of leading and trailing spaces.

        Expected behavior:
        - " hello " should become " Hello "
        - Leading space preserved
        - Trailing space preserved
        """
        result = titlecase(" hello ")
        assert result == " Hello ", "Leading and trailing spaces should be preserved"

    def test_newline_word_boundary(self):
        """Test newline as word boundary.

        Expected behavior:
        - "hello\\nworld" should become "Hello\\nWorld"
        - Newline acts as word separator
        - Newline preserved in output
        """
        result = titlecase("hello\nworld")
        assert result == "Hello\nWorld", "Newline should act as word boundary"

    def test_tab_word_boundary(self):
        """Test tab as word boundary.

        Expected behavior:
        - "hello\\tworld" should become "Hello\\tWorld"
        - Tab acts as word separator
        - Tab preserved in output
        """
        result = titlecase("hello\tworld")
        assert result == "Hello\tWorld", "Tab should act as word boundary"

    def test_numeric_only_string(self):
        """Test string with only numbers.

        Expected behavior:
        - "123" should remain "123"
        - Numbers have no case, pass through unchanged
        """
        result = titlecase("123")
        assert result == "123", "Numeric-only string should be unchanged"

    def test_word_starting_with_number(self):
        """Test word that starts with a number.

        Expected behavior:
        - "hello123" should become "Hello123"
        - First letter capitalized
        - Numbers preserved in position
        """
        result = titlecase("hello123")
        assert result == "Hello123", "Word with trailing numbers should title case"

    def test_all_whitespace(self):
        """Test string with only whitespace characters.

        Expected behavior:
        - "   " should remain "   "
        - Whitespace preserved exactly
        - No transformation needed
        """
        result = titlecase("   ")
        assert result == "   ", "All whitespace should be preserved unchanged"

    def test_single_character(self):
        """Test single character input.

        Expected behavior:
        - "a" should become "A"
        - Single letter capitalized
        """
        result = titlecase("a")
        assert result == "A", "Single character should be capitalized"

    def test_contractions_dont_capitalize_after_apostrophe(self):
        """Test that contractions handle apostrophes correctly.

        Expected behavior:
        - "don't" should become "Don't" (not "Don'T")
        - "i'm" should become "I'm" (not "I'M")
        - "won't" should become "Won't"
        """
        assert titlecase("don't") == "Don't", "Contraction 'don't' should handle apostrophe"
        assert titlecase("i'm") == "I'm", "Contraction 'i'm' should handle apostrophe"
        assert titlecase("won't") == "Won't", "Contraction 'won't' should handle apostrophe"

    def test_possessive_nouns(self):
        """Test possessive nouns with apostrophe.

        Expected behavior:
        - "john's" should become "John's"
        - Apostrophe not treated as boundary
        """
        result = titlecase("john's")
        assert result == "John's", "Possessive noun should handle apostrophe correctly"

    def test_multiple_boundary_types(self):
        """Test string with multiple types of boundaries.

        Expected behavior:
        - "hello world-test_foo" should become "Hello World-Test_Foo"
        - Space, hyphen, and underscore all act as boundaries
        """
        result = titlecase("hello world-test_foo")
        assert result == "Hello World-Test_Foo", "Multiple boundary types should all work"

    def test_consecutive_hyphens(self):
        """Test consecutive hyphens preserved.

        Expected behavior:
        - "hello--world" should become "Hello--World"
        - Both hyphens preserved
        - Word after hyphens capitalized
        """
        result = titlecase("hello--world")
        assert result == "Hello--World", "Consecutive hyphens should be preserved"

    def test_leading_hyphen(self):
        """Test leading hyphen preserved.

        Expected behavior:
        - "-hello" should become "-Hello"
        - Leading hyphen preserved
        - Word capitalized
        """
        result = titlecase("-hello")
        assert result == "-Hello", "Leading hyphen should be preserved"

    def test_trailing_hyphen(self):
        """Test trailing hyphen preserved.

        Expected behavior:
        - "hello-" should become "Hello-"
        - Trailing hyphen preserved
        """
        result = titlecase("hello-")
        assert result == "Hello-", "Trailing hyphen should be preserved"

    def test_number_followed_by_word(self):
        """Test number followed by word after boundary.

        Expected behavior:
        - "123 hello" should become "123 Hello"
        - Number unchanged
        - Word after space capitalized
        """
        result = titlecase("123 hello")
        assert result == "123 Hello", "Number followed by word should work"

    def test_mixed_whitespace_boundaries(self):
        """Test mixed whitespace characters.

        Expected behavior:
        - "hello\\t\\nworld" should become "Hello\\t\\nWorld"
        - Tab and newline both act as boundaries
        - Both preserved in output
        """
        result = titlecase("hello\t\nworld")
        assert result == "Hello\t\nWorld", "Mixed whitespace boundaries should work"

    def test_single_letter_words(self):
        """Test single letter words separated by spaces.

        Expected behavior:
        - "a b c" should become "A B C"
        - Each single letter capitalized
        """
        result = titlecase("a b c")
        assert result == "A B C", "Single letter words should each be capitalized"

    def test_long_sentence(self):
        """Test longer sentence with various boundaries.

        Expected behavior:
        - "the quick-brown_fox jumps" should become "The Quick-Brown_Fox Jumps"
        """
        result = titlecase("the quick-brown_fox jumps")
        assert result == "The Quick-Brown_Fox Jumps", "Longer sentence should title case correctly"

    def test_apostrophe_at_start(self):
        """Test apostrophe at start of word.

        Expected behavior:
        - "'twas" should become "'Twas"
        - Letter after apostrophe at start gets capitalized
        """
        result = titlecase("'twas")
        assert result == "'Twas", "Apostrophe at start should capitalize next letter"

    def test_apostrophe_at_end(self):
        """Test apostrophe at end of word.

        Expected behavior:
        - "dogs'" should become "Dogs'"
        - Trailing apostrophe preserved
        """
        result = titlecase("dogs'")
        assert result == "Dogs'", "Trailing apostrophe should be preserved"

    def test_pure_function_no_side_effects(self):
        """Test that titlecase is a pure function.

        Expected behavior:
        - Calling twice with same input gives same output
        - Original input not modified
        """
        original = "hello world"
        result1 = titlecase(original)
        result2 = titlecase(original)
        assert result1 == result2, "Same input should give same output"
        assert original == "hello world", "Original string should not be modified"

    def test_carriage_return_newline(self):
        """Test Windows-style line endings.

        Expected behavior:
        - "hello\\r\\nworld" should become "Hello\\r\\nWorld"
        - Carriage return and newline both as boundaries
        """
        result = titlecase("hello\r\nworld")
        assert result == "Hello\r\nWorld", "CRLF should act as word boundary"

    def test_only_boundaries(self):
        """Test string with only boundary characters.

        Expected behavior:
        - " -_\\t\\n" should remain " -_\\t\\n"
        - No letters to transform
        - Boundaries preserved exactly
        """
        result = titlecase(" -_\t\n")
        assert result == " -_\t\n", "Only boundaries should be preserved unchanged"

    def test_word_all_numbers_with_boundaries(self):
        """Test words that are all numbers between boundaries.

        Expected behavior:
        - "123-456_789" should remain "123-456_789"
        - Numbers unchanged
        - Boundaries preserved
        """
        result = titlecase("123-456_789")
        assert result == "123-456_789", "Numeric words with boundaries should be unchanged"
