# String Utilities Reference

Text processing utilities for URL-safe slugs and proper title casing.

**Module**: `amplihack.utils.string_utils`

## Quick Start

```python
from amplihack.utils.string_utils import slugify, titlecase

# Create URL-safe slugs
slug = slugify("Hello World!")
# Result: 'hello-world'

# Convert to proper title case
title = titlecase("the quick brown fox")
# Result: 'The Quick Brown Fox'
```

## Contents

- [slugify](#slugify)
- [titlecase](#titlecase)
- [SMALL_WORDS](#small_words)
- [Customization](#customization)

---

## slugify

Convert text to URL-safe slug format.

```python
def slugify(text: str) -> str
```

### Parameters

| Parameter | Type  | Description                                |
| --------- | ----- | ------------------------------------------ |
| `text`    | `str` | Input string with any characters or spaces |

### Returns

URL-safe slug with lowercase alphanumeric characters and hyphens.
Empty string if input contains no valid characters.

### Examples

```python
from amplihack.utils.string_utils import slugify

slugify("Hello World")
# Result: 'hello-world'

slugify("Cafe")
# Result: 'cafe'

slugify("Rock & Roll")
# Result: 'rock-roll'

slugify("  Multiple   Spaces  ")
# Result: 'multiple-spaces'

slugify("Special@#$Characters!")
# Result: 'special-characters'
```

### Behavior

1. Normalizes Unicode (NFD) and converts to ASCII
2. Converts to lowercase
3. Replaces whitespace and special chars with hyphens
4. Consolidates consecutive hyphens
5. Strips leading/trailing hyphens

---

## titlecase

Convert string to proper Title Case.

```python
def titlecase(s: str) -> str
```

### Parameters

| Parameter | Type  | Description             |
| --------- | ----- | ----------------------- |
| `s`       | `str` | Input string to convert |

### Returns

String converted to proper title case.
Empty string if input is empty.

### Examples

```python
from amplihack.utils.string_utils import titlecase

# Basic title casing
titlecase("the quick brown fox")
# Result: 'The Quick Brown Fox'

# Small words stay lowercase (except first/last)
titlecase("war and peace")
# Result: 'War and Peace'

titlecase("a tale of two cities")
# Result: 'A Tale of Two Cities'

# Acronyms preserved
titlecase("NASA launches new satellite")
# Result: 'NASA Launches New Satellite'

titlecase("the FBI and CIA report")
# Result: 'The FBI and CIA Report'

# Hyphenated words
titlecase("self-driving cars")
# Result: 'Self-Driving Cars'

titlecase("state-of-the-art technology")
# Result: 'State-Of-The-Art Technology'

# Colons: capitalize word after
titlecase("python: a beginner's guide")
# Result: "Python: A Beginner's Guide"

# All caps input normalized
titlecase("THE LORD OF THE RINGS")
# Result: 'The Lord of the Rings'
```

### Title Case Rules

1. **First/Last words**: Always capitalized
2. **Small words**: Kept lowercase unless first/last (see [SMALL_WORDS](#small_words))
3. **Acronyms**: Preserved (2+ consecutive uppercase letters)
4. **Hyphenated words**: Each part capitalized
5. **After colon**: Next word capitalized

---

## SMALL_WORDS

Set of words kept lowercase in titles (unless first or last word).

```python
SMALL_WORDS: set[str]
```

### Default Contents

```python
SMALL_WORDS = {
    # Articles
    "a", "an", "the",
    # Coordinating conjunctions
    "and", "but", "or", "nor", "for", "yet", "so",
    # Short prepositions
    "at", "by", "in", "of", "on", "to", "up", "as", "if",
    "en", "per", "via",
}
```

---

## Customization

### Adding Domain-Specific Small Words

For specialized domains, extend `SMALL_WORDS`:

```python
from amplihack.utils.string_utils import titlecase, SMALL_WORDS

# Add domain-specific words
SMALL_WORDS.add("vs")
SMALL_WORDS.add("v")

titlecase("cats vs dogs")
# Result: 'Cats vs Dogs'
```

### Removing Words

```python
from amplihack.utils.string_utils import titlecase, SMALL_WORDS

# Remove 'the' from small words
SMALL_WORDS.discard("the")

titlecase("the end of the world")
# Result: 'The End of The World'
```

### Creating Custom Small Word Sets

For complete control, replace the set:

```python
from amplihack.utils import string_utils

# Custom academic style
string_utils.SMALL_WORDS = {"a", "an", "the", "and", "or"}

titlecase("theory of everything")
# Result: 'Theory of Everything'
```

---

## Edge Cases

| Input           | Output          | Notes                   |
| --------------- | --------------- | ----------------------- |
| `""`            | `""`            | Empty string            |
| `"a"`           | `"A"`           | Single word capitalized |
| `"THE"`         | `"The"`         | All caps normalized     |
| `"NASA"`        | `"NASA"`        | Acronym preserved       |
| `"e-commerce"`  | `"E-Commerce"`  | Hyphen handling         |
| `"Q&A: basics"` | `"Q&A: Basics"` | After colon capitalized |

---

## See Also

- [Python `str.title()`](https://docs.python.org/3/library/stdtypes.html#str.title) - Built-in (does not handle small words)
- [Chicago Manual of Style](https://www.chicagomanualofstyle.org/) - Title case conventions
