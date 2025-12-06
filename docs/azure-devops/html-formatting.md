# HTML Formatting Guide

Azure DevOps work items use HTML fer descriptions and comments. The format_html tool converts markdown to proper HTML.

## Why HTML?

Azure DevOps displays work item descriptions as HTML. Plain text looks unprofessional and lacks formatting.

## Auto-Formatting

The create_work_item tool automatically converts markdown to HTML:

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type "User Story" \
  --title "My Story" \
  --description "# Title

This is **bold** and this is *italic*.

- List item 1
- List item 2"
```

Disable with `--no-format`:

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type Task \
  --title "My Task" \
  --description "<p>Already HTML</p>" \
  --no-format
```

## Standalone Formatter

Convert markdown files to HTML:

```bash
# From file
python -m .claude.scenarios.az-devops-tools.format_html story.md

# From stdin
echo "# Title" | python -m .claude.scenarios.az-devops-tools.format_html

# Save to file
python -m .claude.scenarios.az-devops-tools.format_html story.md -o output.html
```

## Supported Markdown

### Headings

**Markdown:**

```markdown
# Heading 1

## Heading 2

### Heading 3
```

**HTML:**

```html
<h1>Heading 1</h1>
<h2>Heading 2</h2>
<h3>Heading 3</h3>
```

### Paragraphs

**Markdown:**

```markdown
This is a paragraph.

This is another paragraph.
```

**HTML:**

```html
<p>This is a paragraph.</p>
<p>This is another paragraph.</p>
```

### Bold and Italic

**Markdown:**

```markdown
**bold** or **bold**
_italic_ or _italic_
**_bold italic_**
```

**HTML:**

```html
<strong>bold</strong>
<em>italic</em>
<strong><em>bold italic</em></strong>
```

### Unordered Lists

**Markdown:**

```markdown
- Item 1
- Item 2
- Item 3
```

**HTML:**

```html
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
  <li>Item 3</li>
</ul>
```

### Ordered Lists

**Markdown:**

```markdown
1. First
2. Second
3. Third
```

**HTML:**

```html
<ol>
  <li>First</li>
  <li>Second</li>
  <li>Third</li>
</ol>
```

### Inline Code

**Markdown:**

```markdown
Use the `print()` function.
```

**HTML:**

```html
<p>Use the <code>print()</code> function.</p>
```

### Code Blocks

**Markdown:**

````markdown
```python
def hello():
    print("Hello!")
```
````

**HTML:**

```html
<pre><code class="language-python">def hello():
    print("Hello!")
</code></pre>
```

### Links

**Markdown:**

```markdown
[Link text](https://example.com)
```

**HTML:**

```html
<a href="https://example.com">Link text</a>
```

## Programmatic Usage

```python
from .claude.scenarios.az_devops_tools.format_html import markdown_to_html

markdown = """
# User Story

As a user, I want to **log in** so I can access my account.

## Acceptance Criteria

- User can enter credentials
- System validates login
- Error shown on failure
"""

html = markdown_to_html(markdown)
print(html)
```

## Utility Functions

Build HTML directly:

```python
from .claude.scenarios.az_devops_tools.format_html import (
    html_p,
    html_heading,
    html_list,
    html_code,
    html_link,
)

# Paragraph
p = html_p("This is a paragraph")

# Heading
h1 = html_heading("Title", level=1)

# List
items = ["Item 1", "Item 2", "Item 3"]
ul = html_list(items, ordered=False)
ol = html_list(items, ordered=True)

# Code
code = html_code("def hello(): pass", language="python")

# Link
link = html_link("Click here", "https://example.com")
```

## Best Practices

1. **Use markdown** - Easier to write and maintain
2. **Preview in Azure DevOps** - Check formatting after creation
3. **Keep it simple** - Avoid complex HTML
4. **Use code blocks** - For code snippets and logs
5. **Structure with headings** - Makes descriptions scannable

## Limitations

The formatter supports common markdown only:

- No tables
- No images
- No nested lists
- No HTML entities

Fer advanced formatting, use raw HTML with `--no-format`.

## See Also

- [Work Items Guide](work-items.md)
- [Markdown Guide](https://www.markdownguide.org/)
