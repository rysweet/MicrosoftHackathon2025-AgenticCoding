"""Unit tests for string utility functions.

Tests the string_utils module including:
- slugify: Convert strings to URL-safe slugs
- titlecase: Convert strings to proper Title Case
- SMALL_WORDS: Constant for title case small words

Test Coverage (66 tests):
- slugify: 31 tests for slug conversion
- titlecase: 31 tests for title case conversion
- SMALL_WORDS: 4 tests for constant validation
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# Import string utility functions
from amplihack.utils.string_utils import SMALL_WORDS, slugify, titlecase


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


class TestTitlecase:
    """Test titlecase function for converting strings to proper Title Case.

    The titlecase function should:
    1. Capitalize first and last words always
    2. Capitalize words not in SMALL_WORDS
    3. Preserve acronyms (consecutive uppercase letters, 2+ chars)
    4. Handle hyphenated words (capitalize each part)
    5. Capitalize word after colon
    6. Handle all-caps input by converting to proper title case
    """

    # ==========================================================================
    # UNIT TESTS - Basic Functionality (60% of tests)
    # ==========================================================================

    def test_basic_hello_world(self):
        """Test basic conversion of simple text to title case."""
        result = titlecase("hello world")
        assert result == "Hello World", "Should convert 'hello world' to 'Hello World'"

    def test_empty_string(self):
        """Test handling of empty string input."""
        result = titlecase("")
        assert result == "", "Empty string should return empty string"

    def test_single_word(self):
        """Test single word input."""
        result = titlecase("hello")
        assert result == "Hello", "Should capitalize single word"

    def test_already_title_case(self):
        """Test string already in title case."""
        result = titlecase("Hello World")
        assert result == "Hello World", "Already title case should remain unchanged"

    # ==========================================================================
    # UNIT TESTS - Small Words Handling
    # ==========================================================================

    def test_small_words_lowercase_mid_title(self):
        """Test that small words stay lowercase in middle of title."""
        result = titlecase("the lord of the rings")
        assert result == "The Lord of the Rings", "Small words should stay lowercase mid-title"

    def test_first_word_always_capitalized(self):
        """Test that first word is always capitalized even if small word."""
        result = titlecase("a tale of two cities")
        assert result == "A Tale of Two Cities", "First word always capitalized"

    def test_last_word_always_capitalized(self):
        """Test that last word is always capitalized even if small word."""
        result = titlecase("turn it on")
        assert result == "Turn It On", "Last word always capitalized"

    def test_small_word_conjunction_and(self):
        """Test handling of conjunction 'and'."""
        result = titlecase("war and peace")
        assert result == "War and Peace", "Conjunction 'and' stays lowercase mid-title"

    def test_multiple_small_words(self):
        """Test multiple small words in sequence."""
        result = titlecase("the cat in the hat")
        assert result == "The Cat in the Hat", "Multiple small words handled correctly"

    # ==========================================================================
    # UNIT TESTS - Acronyms
    # ==========================================================================

    def test_acronym_preserved(self):
        """Test that acronyms are preserved."""
        result = titlecase("NASA launches new satellite")
        assert result == "NASA Launches New Satellite", "Acronym NASA should be preserved"

    def test_acronym_mid_sentence(self):
        """Test acronym in middle of sentence."""
        result = titlecase("the NASA program")
        assert result == "The NASA Program", "Acronym preserved mid-sentence"

    def test_multiple_acronyms(self):
        """Test multiple acronyms in same string."""
        result = titlecase("NASA and ESA collaboration")
        assert result == "NASA and ESA Collaboration", "Multiple acronyms preserved"

    def test_two_letter_acronym(self):
        """Test minimum acronym length (2 letters)."""
        result = titlecase("AI technology")
        assert result == "AI Technology", "Two-letter acronym preserved"

    # ==========================================================================
    # UNIT TESTS - Hyphenated Words
    # ==========================================================================

    def test_hyphenated_word(self):
        """Test basic hyphenated word handling."""
        result = titlecase("self-driving cars")
        assert result == "Self-Driving Cars", "Hyphenated words should capitalize each part"

    def test_hyphenated_word_multiple(self):
        """Test multiple hyphenated words."""
        result = titlecase("up-to-date information")
        assert result == "Up-To-Date Information", "Multiple hyphenated parts capitalized"

    def test_hyphenated_at_end(self):
        """Test hyphenated word at end of title."""
        result = titlecase("technology is cutting-edge")
        assert result == "Technology Is Cutting-Edge", "Hyphenated word at end handled"

    # ==========================================================================
    # UNIT TESTS - Colon Handling
    # ==========================================================================

    def test_colon_capitalizes_next_word(self):
        """Test that word after colon is capitalized."""
        result = titlecase("intro: a guide")
        assert result == "Intro: A Guide", "Word after colon should be capitalized"

    def test_colon_with_small_word(self):
        """Test colon followed by small word."""
        result = titlecase("python: the basics")
        assert result == "Python: The Basics", "Small word after colon capitalized"

    # ==========================================================================
    # UNIT TESTS - All Caps Input
    # ==========================================================================

    def test_all_caps_conversion(self):
        """Test that all caps input is converted to proper title case."""
        result = titlecase("THE LORD OF THE RINGS")
        assert result == "The Lord of the Rings", "All caps should convert to title case"

    def test_all_caps_simple(self):
        """Test all caps simple case."""
        result = titlecase("HELLO WORLD")
        assert result == "Hello World", "All caps simple case"

    # ==========================================================================
    # INTEGRATION TESTS - Combined Features (30% of tests)
    # ==========================================================================

    def test_complex_title_with_acronym_and_small_words(self):
        """Test complex title with acronyms and small words."""
        result = titlecase("the NASA guide to the moon")
        assert result == "The NASA Guide to the Moon", "Complex title with acronym and small words"

    def test_colon_and_hyphenated(self):
        """Test colon combined with hyphenated words."""
        result = titlecase("tech: self-driving cars")
        assert result == "Tech: Self-Driving Cars", "Colon and hyphenated combined"

    def test_subtitle_pattern(self):
        """Test common subtitle pattern."""
        result = titlecase("python: a beginner's guide")
        assert result == "Python: A Beginner's Guide", "Subtitle pattern handled"

    def test_book_title_complex(self):
        """Test realistic book title."""
        result = titlecase("the hitchhiker's guide to the galaxy")
        assert result == "The Hitchhiker's Guide to the Galaxy", "Complex book title"

    # ==========================================================================
    # EDGE CASE TESTS (10% of tests)
    # ==========================================================================

    def test_single_character(self):
        """Test single character input."""
        result = titlecase("a")
        assert result == "A", "Single character should be capitalized"

    def test_whitespace_only(self):
        """Test string with only whitespace."""
        result = titlecase("   ")
        assert result == "", "Whitespace only should return empty string"

    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces."""
        result = titlecase("hello   world")
        assert result == "Hello World", "Multiple spaces handled"

    def test_possessive_apostrophe(self):
        """Test words with possessive apostrophes."""
        result = titlecase("john's book")
        assert result == "John's Book", "Possessive apostrophe handled"

    def test_mixed_case_input(self):
        """Test mixed case input."""
        result = titlecase("hElLo WoRlD")
        assert result == "Hello World", "Mixed case normalized"

    def test_numbers_in_title(self):
        """Test numbers in title."""
        result = titlecase("the 7 habits of success")
        assert result == "The 7 Habits of Success", "Numbers in title handled"

    def test_idempotency(self):
        """Test that titlecase is idempotent."""
        original = "the lord of the rings"
        first_pass = titlecase(original)
        second_pass = titlecase(first_pass)
        assert first_pass == second_pass, "Titlecase should be idempotent"


class TestSmallWordsConstant:
    """Test the SMALL_WORDS constant."""

    def test_small_words_contains_articles(self):
        """Test SMALL_WORDS contains common articles."""
        assert "a" in SMALL_WORDS, "Should contain article 'a'"
        assert "an" in SMALL_WORDS, "Should contain article 'an'"
        assert "the" in SMALL_WORDS, "Should contain article 'the'"

    def test_small_words_contains_conjunctions(self):
        """Test SMALL_WORDS contains common conjunctions."""
        assert "and" in SMALL_WORDS, "Should contain conjunction 'and'"
        assert "but" in SMALL_WORDS, "Should contain conjunction 'but'"
        assert "or" in SMALL_WORDS, "Should contain conjunction 'or'"

    def test_small_words_contains_prepositions(self):
        """Test SMALL_WORDS contains common short prepositions."""
        prepositions = ["at", "by", "in", "of", "on", "to"]
        for prep in prepositions:
            assert prep in SMALL_WORDS, f"Should contain preposition '{prep}'"

    def test_small_words_is_set(self):
        """Test SMALL_WORDS is a set for O(1) lookup."""
        assert isinstance(SMALL_WORDS, set), "SMALL_WORDS should be a set"
