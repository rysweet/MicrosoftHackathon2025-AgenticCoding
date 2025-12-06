# Azure DevOps CLI Tools Documentation

Ahoy! Welcome to the Azure DevOps CLI tools documentation. This collection of Python tools helps ye manage Azure DevOps Boards efficiently through the command line.

## Table of Contents

- [Quick Start Guide](quick-start.md) - Get started in 5 minutes
- [Authentication](authentication.md) - Set up authentication and configuration
- [Work Items](work-items.md) - Create and manage work items
- [Queries](queries.md) - Query work items with WIQL
- [HTML Formatting](html-formatting.md) - Format descriptions and comments
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Overview

The az-devops-tools suite provides six specialized tools:

### 1. Authentication Check (`auth_check.py`)

Verify yer Azure DevOps setup be ready fer use.

- Checks az CLI installation
- Verifies login status
- Validates configuration
- Tests org/project access
- Auto-fix capability

### 2. HTML Formatter (`format_html.py`)

Convert markdown to Azure DevOps HTML format.

- Supports headings, lists, code blocks
- Inline formatting (bold, italic, code)
- CLI and importable functions
- Standard library only

### 3. Work Item Creator (`create_work_item.py`)

Create work items with auto-formatted descriptions.

- All work item types (Story, Bug, Task, Feature, Epic)
- Auto-converts markdown to HTML
- Optional parent linking
- Custom field support

### 4. Parent Linker (`link_parent.py`)

Link work items in parent-child relationships.

- Validates both items exist
- Checks type compatibility
- Clear error messages

### 5. WIQL Query Tool (`query_wiql.py`)

Query work items using WIQL.

- 5 predefined queries
- Custom WIQL support
- Multiple output formats (table, json, csv, ids-only)
- Result limiting

### 6. Type Lister (`list_types.py`)

Discover work item types and fields.

- List all types in project
- Show field schemas
- Required vs optional fields
- Custom type support

## Installation

These tools require:

- Python 3.8+
- Azure CLI with DevOps extension
- Azure DevOps authentication

See [Authentication](authentication.md) fer setup instructions.

## Quick Example

```bash
# Check authentication
python -m .claude.scenarios.az-devops-tools.auth_check

# Create a User Story
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type "User Story" \
  --title "Implement login" \
  --description "# Story\n\nAs a user, I want to log in..."

# Query yer work items
python -m .claude.scenarios.az-devops-tools.query_wiql --query my-items
```

## Philosophy

These tools follow amplihack principles:

- **Single responsibility** - Each tool does one thing well
- **Composable** - Tools can be combined
- **Clear errors** - Actionable error messages
- **No stubs** - All code works
- **Standard library** - Minimal dependencies

## Getting Help

- Read the [Quick Start Guide](quick-start.md)
- Check [Troubleshooting](troubleshooting.md)
- See tool help: `python -m .claude.scenarios.az-devops-tools.TOOL_NAME --help`
- Review [MS Learn Documentation](https://learn.microsoft.com/en-us/azure/devops/)

## Contributing

These tools be part of the amplihack framework. To create yer own tool:

1. See [HOW_TO_CREATE_YOUR_OWN.md](../../.claude/scenarios/az-devops-tools/HOW_TO_CREATE_YOUR_OWN.md)
2. Follow the template structure
3. Use common utilities from `common.py`
4. Add tests
5. Update documentation

Fair winds and following seas!
