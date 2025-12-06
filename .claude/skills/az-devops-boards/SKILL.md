---
name: az-devops-boards
description: Azure DevOps Boards work item management using CLI tools with HTML formatting and parent linking support
version: 1.0.0
type: skill
auto_activate_keywords:
  - azure devops
  - work item
  - boards
  - wiql
  - ado
  - ado boards
  - devops work item
tools_required:
  - .claude/scenarios/az-devops-tools/auth_check.py
  - .claude/scenarios/az-devops-tools/create_work_item.py
  - .claude/scenarios/az-devops-tools/link_parent.py
  - .claude/scenarios/az-devops-tools/query_wiql.py
  - .claude/scenarios/az-devops-tools/format_html.py
  - .claude/scenarios/az-devops-tools/list_types.py
references:
  - name: "Azure DevOps CLI Documentation"
    url: "https://learn.microsoft.com/en-us/cli/azure/devops"
  - name: "az boards work-item Commands"
    url: "https://learn.microsoft.com/en-us/cli/azure/boards/work-item"
  - name: "Work Items REST API"
    url: "https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items"
  - name: "WIQL Syntax Reference"
    url: "https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax"
  - name: "Work Item Fields"
    url: "https://learn.microsoft.com/en-us/azure/devops/boards/work-items/work-item-fields"
  - name: "Link Types Reference"
    url: "https://learn.microsoft.com/en-us/azure/devops/boards/queries/link-type-reference"
---

# Azure DevOps Boards Skill

Manage Azure DevOps work items using reusable Python CLI tools.

## Purpose

This skill provides guidance for Azure DevOps work item management through a suite of purpose-built Python tools that handle:

- Work item creation with HTML-formatted descriptions
- Parent-child relationship linking
- WIQL query execution
- Authentication verification and auto-fixing
- Work item type and field discovery

## Authentication First

**ALWAYS start by checking authentication:**

```bash
python .claude/scenarios/az-devops-tools/auth_check.py --auto-fix
```

This verifies Azure CLI is installed, you're logged in, org/project are configured, and you have access.

See: [@docs/azure-devops/authentication.md](../../docs/azure-devops/authentication.md)

## Available Tools

| Tool                  | Purpose               | When to Use                               |
| --------------------- | --------------------- | ----------------------------------------- |
| `auth_check.py`       | Verify authentication | Before any operations                     |
| `create_work_item.py` | Create work items     | Add User Stories, Tasks, Bugs, etc.       |
| `link_parent.py`      | Link parent-child     | Create Epic → Feature → Story hierarchies |
| `query_wiql.py`       | Execute WIQL queries  | Find, filter, and list work items         |
| `format_html.py`      | Convert to HTML       | Format rich descriptions                  |
| `list_types.py`       | Discover types/fields | Explore available options                 |

## Common Patterns

### Pattern 1: Create Work Item with Parent

```bash
# Create parent work item
python .claude/scenarios/az-devops-tools/create_work_item.py \
  --type "Epic" \
  --title "Q1 Planning Initiative" \
  --description @epic_desc.md

# Output: Created work item #12345

# Create child and link to parent
python .claude/scenarios/az-devops-tools/create_work_item.py \
  --type "Feature" \
  --title "Authentication System" \
  --description @feature_desc.md \
  --parent-id 12345

# Output: Created work item #12346 and linked to parent #12345
```

### Pattern 2: Query Your Work Items

```bash
# Query with predefined query
python .claude/scenarios/az-devops-tools/query_wiql.py --query my-items

# Custom WIQL query
python .claude/scenarios/az-devops-tools/query_wiql.py \
  --query "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] = 'Active'"

# Get just IDs for scripting
python .claude/scenarios/az-devops-tools/query_wiql.py \
  --query my-items \
  --format ids
```

### Pattern 3: Discover Available Types

```bash
# List all work item types in your project
python .claude/scenarios/az-devops-tools/list_types.py

# Show fields for specific type
python .claude/scenarios/az-devops-tools/list_types.py \
  --type "User Story" \
  --fields
```

## Critical Learnings

### HTML Formatting Required

Azure DevOps work item descriptions use HTML, not Markdown or plain text.

**The tools handle this automatically:**

- `create_work_item.py` converts markdown to HTML by default
- Use `--no-html` to disable conversion
- Or use `format_html.py` directly for custom formatting

See: [@docs/azure-devops/html-formatting.md](../../docs/azure-devops/html-formatting.md)

### Two-Step Parent Linking

You cannot specify a parent during work item creation via CLI (Azure limitation).

**The tools provide two approaches:**

**Option A:** Use `--parent-id` flag (recommended):

```bash
python .claude/scenarios/az-devops-tools/create_work_item.py \
  --type "Task" \
  --title "My Task" \
  --parent-id 12345
```

**Option B:** Link separately:

```bash
# Step 1: Create
TASK_ID=$(python .claude/scenarios/az-devops-tools/create_work_item.py \
  --type "Task" \
  --title "My Task" \
  --json | jq -r '.id')

# Step 2: Link
python .claude/scenarios/az-devops-tools/link_parent.py \
  --child $TASK_ID \
  --parent 12345
```

### Area Path and Work Item Types

- Area path format: `ProjectName\TeamName\SubArea`
- Work item types vary by project (standard + custom types)
- Use `list_types.py` to discover what's available in your project

## Error Recovery

| Error                  | Tool to Use                             | Example                       |
| ---------------------- | --------------------------------------- | ----------------------------- |
| Authentication failed  | `auth_check.py --auto-fix`              | Auto-login and configure      |
| Invalid work item type | `list_types.py`                         | See available types           |
| Field validation error | `list_types.py --type "Type" --fields`  | See valid fields              |
| Parent link failed     | Check IDs exist, verify hierarchy rules | Epic → Feature → Story → Task |

## Documentation

Comprehensive guides are in `docs/azure-devops/`:

- [Quick Start](../../docs/azure-devops/quick-start.md) - Get started in 5 minutes
- [Authentication](../../docs/azure-devops/authentication.md) - Setup and troubleshooting
- [Work Items](../../docs/azure-devops/work-items.md) - Creating and managing items
- [Queries](../../docs/azure-devops/queries.md) - WIQL query guide
- [HTML Formatting](../../docs/azure-devops/html-formatting.md) - Rich text formatting
- [Troubleshooting](../../docs/azure-devops/troubleshooting.md) - Common issues

## Tool Implementation

All tools are in `.claude/scenarios/az-devops-tools/`:

- Standalone Python programs (can run independently)
- Importable modules (can use in other scripts)
- Comprehensive error handling
- Tests in `tests/` directory

See: [Tool README](.claude/scenarios/az-devops-tools/README.md)

## Philosophy

These tools follow amplihack principles:

- **Ruthless Simplicity**: Each tool does one thing well
- **Zero-BS**: Every function works, no stubs or TODOs
- **Reusable**: Importable and composable
- **Fail-Fast**: Clear errors with actionable guidance

## Quick Reference

```bash
# Setup (first time)
python .claude/scenarios/az-devops-tools/auth_check.py --auto-fix

# Create work item
python .claude/scenarios/az-devops-tools/create_work_item.py \
  --type "User Story" \
  --title "Title" \
  --description @desc.md

# Query work items
python .claude/scenarios/az-devops-tools/query_wiql.py --query my-items

# Discover types
python .claude/scenarios/az-devops-tools/list_types.py
```
