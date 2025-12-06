# Azure DevOps Boards Skill

Ahoy! This Claude Code skill provides efficient Azure DevOps work item management through shell helpers an' proven patterns.

## What This Skill Provides

**Core Capabilities:**

- Create work items (Epic, Feature, User Story, Task, Bug, custom types)
- Link parent-child relationships (two-step pattern)
- Query work items with WIQL
- Update work item fields
- HTML formatting in descriptions
- Bulk operations

**Based on Real Experience:**

- HTML formatting patterns that work
- Two-step parent linking (the only way that works)
- Area path requirements an' conventions
- Cross-project operations
- Error handling an' validation

## Quick Start

**Prerequisites:**

```bash
# Install Azure CLI with devops extension
brew install azure-cli  # macOS
az extension add --name azure-devops

# Authenticate
az login
az devops configure --defaults organization=https://dev.azure.com/YourOrg project=YourProject
```

**Create Your First Work Item:**

```bash
# Source shell functions from skill.md

# Create an Epic
epic_id=$(create_work_item \
  "https://dev.azure.com/MyOrg" \
  "MyProject" \
  "Epic" \
  "New Feature Set" \
  "<p>Description with <strong>HTML</strong> formatting</p>" \
  "MyProject\\Team")

echo "Created Epic: $epic_id"

# Create Feature under Epic (two-step pattern)
feature_id=$(create_work_item \
  "https://dev.azure.com/MyOrg" \
  "MyProject" \
  "Feature" \
  "Specific Feature" \
  "<p>Feature description</p>" \
  "MyProject\\Team")

link_parent "https://dev.azure.com/MyOrg" "$feature_id" "$epic_id"
```

## Navigation

### Core Documentation

- **[skill.md](skill.md)** - Main skill file with shell functions, critical learnings, quick reference

### Examples

- **[examples/common-workflows.md](examples/common-workflows.md)** - Complete workflow examples
  - Create Epic with Features and Stories
  - Bulk create from CSV
  - Query and update patterns
  - Cross-project operations
  - WIQL query examples

### Reference

- **[reference/work-item-types.md](reference/work-item-types.md)** - Work item type details
  - Standard types (Epic, Feature, User Story, Task, Bug)
  - Custom type patterns
  - Type hierarchy rules
  - Selection guide

- **[reference/field-reference.md](reference/field-reference.md)** - Field reference
  - System fields (Title, State, AssignedTo, etc.)
  - Microsoft VSTS fields (Priority, StoryPoints, etc.)
  - Custom field patterns
  - HTML formatting rules

## Critical Learnings

**1. HTML Formatting**
Work item descriptions support HTML. Use `<p>`, `<ul><li>`, `<strong>`, `<code>` for professional-looking work items.

**2. Two-Step Parent Linking**
You CANNOT create a work item with parent in single command. Always:

1. Create child work item (capture ID)
2. Link to parent with `az boards work-item relation add`

**3. Area Path Required**
Always specify area path in format: `ProjectName\\TeamName\\SubArea`

**4. Work Item Types Vary**
Check your project's available types. Custom types like "Scenario" are common.

## Common Patterns

**Create hierarchy:**

```bash
epic → feature → story → task
```

**Query pattern:**

```bash
query_work_items "$ORG" "$PROJECT" \
  "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.State] = 'Active'"
```

**Update pattern:**

```bash
update_work_item "$ORG" "$work_item_id" \
  "System.State=Active" \
  "System.Tags=important;urgent"
```

## Philosophy

This skill follows ruthless simplicity:

- **Working shell functions** - no stubs, no TODOs
- **Real examples** - from actual usage patterns
- **Progressive disclosure** - core → examples → reference
- **Bricks & studs** - self-contained, reusable functions

## Token Budget

- **skill.md**: ~4,200 tokens (core functions, critical learnings)
- **common-workflows.md**: ~2,000 tokens (complete examples)
- **work-item-types.md**: ~1,000 tokens (type reference)
- **field-reference.md**: ~1,500 tokens (field details)

Total: ~8,700 tokens for comprehensive coverage

## See Also

- [Azure DevOps CLI Documentation](https://learn.microsoft.com/en-us/cli/azure/boards)
- [WIQL Query Language](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
- [Work Item Field Reference](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/work-item-field)
