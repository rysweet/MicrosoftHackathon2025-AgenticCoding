---
name: az-devops-boards
type: integration
category: devops
description: Azure DevOps work item management with shell helpers
version: 1.0.0
author: amplihack
tags: [azure-devops, work-items, project-management, wiql]
activation_keywords:
  - azure devops boards
  - create work item
  - ado work items
  - azure boards
  - wiql query
  - devops task
dependencies:
  external:
    - az-cli (Azure CLI with devops extension)
  configuration:
    - AZURE_DEVOPS_ORG: Azure DevOps organization URL
    - AZURE_DEVOPS_PROJECT: Default project name
prerequisites:
  - Azure CLI installed with devops extension
  - Authenticated to Azure DevOps (az login)
  - Access to target Azure DevOps organization
capabilities:
  - Create work items (Epic, Feature, User Story, Task, Bug, custom types)
  - Link parent-child relationships
  - Query work items with WIQL
  - Update work item fields
  - HTML formatting in descriptions
  - Bulk operations
related_skills:
  - project-management
  - git-workflow
priority: high
---

# Azure DevOps Boards Skill

Arrr! This skill be yer navigator fer Azure DevOps Boards, helpin' ye create work items, manage hierarchies, an' query yer project's treasure maps.

## Purpose

Provides shell helpers an' patterns fer efficient Azure DevOps work item management through the `az boards` CLI. Based on real-world learnings from complex work item creation an' bulk operations.

## Prerequisites

**Required:**

- Azure CLI installed: `brew install azure-cli` (macOS) or equivalent
- Azure DevOps extension: `az extension add --name azure-devops`
- Authentication: `az login` an' optionally `az devops configure --defaults organization=https://dev.azure.com/YourOrg project=YourProject`

**Verify setup:**

```bash
az boards work-item show --id 1 --org https://dev.azure.com/YourOrg --project YourProject
```

## Core Shell Functions

### HTML Formatting Helper

Azure DevOps work item descriptions support HTML. This helper formats content properly:

```bash
html_format() {
  local content="$1"
  echo "<p>${content}</p>"
}

html_list() {
  local items=("$@")
  echo "<ul>"
  for item in "${items[@]}"; do
    echo "<li>${item}</li>"
  done
  echo "</ul>"
}

html_code() {
  local code="$1"
  echo "<pre><code>${code}</code></pre>"
}

# Example usage
description=$(cat <<EOF
<p>This feature implements user authentication.</p>
<ul>
<li><strong>OAuth 2.0</strong> integration</li>
<li>Session management</li>
<li>Role-based access control</li>
</ul>
<p>See also: <code>auth-service</code> module</p>
EOF
)
```

### Create Work Item

```bash
create_work_item() {
  local org="$1"
  local project="$2"
  local type="$3"      # Epic, Feature, "User Story", Task, Bug, or custom type
  local title="$4"
  local description="$5"
  local area="${6:-$project}"  # Area path (required), defaults to project root

  # Create work item and capture ID from output
  local output=$(az boards work-item create \
    --org "$org" \
    --project "$project" \
    --type "$type" \
    --title "$title" \
    --description "$description" \
    --area "$area" \
    --output json 2>&1)

  if [ $? -eq 0 ]; then
    # Extract ID from JSON output
    local id=$(echo "$output" | grep -o '"id": [0-9]*' | head -1 | awk '{print $2}')
    echo "$id"
    return 0
  else
    echo "ERROR: Failed to create work item: $output" >&2
    return 1
  fi
}

# Example usage
epic_id=$(create_work_item \
  "https://dev.azure.com/MyOrg" \
  "MyProject" \
  "Epic" \
  "User Authentication System" \
  "<p>Implement complete authentication system with OAuth 2.0</p>" \
  "MyProject\\Platform\\Security")

if [ $? -eq 0 ]; then
  echo "Created Epic: $epic_id"
fi
```

### Link Parent-Child Relationship

**CRITICAL LEARNING:** Parent linking requires TWO steps - create item first, then link. Cannot be done in single command.

```bash
link_parent() {
  local org="$1"
  local child_id="$2"
  local parent_id="$3"

  az boards work-item relation add \
    --org "$org" \
    --id "$child_id" \
    --relation-type parent \
    --target-id "$parent_id" \
    --output none

  if [ $? -eq 0 ]; then
    echo "Linked work item $child_id to parent $parent_id"
    return 0
  else
    echo "ERROR: Failed to link $child_id to parent $parent_id" >&2
    return 1
  fi
}

# Example: Create Feature under Epic (two-step pattern)
feature_id=$(create_work_item \
  "https://dev.azure.com/MyOrg" \
  "MyProject" \
  "Feature" \
  "OAuth Integration" \
  "<p>Integrate OAuth 2.0 provider</p>" \
  "MyProject\\Platform\\Security")

if [ $? -eq 0 ]; then
  link_parent "https://dev.azure.com/MyOrg" "$feature_id" "$epic_id"
fi
```

### Query Work Items

```bash
query_work_items() {
  local org="$1"
  local project="$2"
  local wiql="$3"  # WIQL query string

  az boards query \
    --org "$org" \
    --project "$project" \
    --wiql "$wiql" \
    --output table
}

# Example: Find all active User Stories
query_work_items \
  "https://dev.azure.com/MyOrg" \
  "MyProject" \
  "SELECT [System.Id], [System.Title], [System.State] FROM workitems WHERE [System.WorkItemType] = 'User Story' AND [System.State] = 'Active'"
```

### Update Work Item

```bash
update_work_item() {
  local org="$1"
  local id="$2"
  shift 2
  local fields=("$@")  # Field=Value pairs

  local field_args=()
  for field in "${fields[@]}"; do
    field_args+=(--fields "$field")
  done

  az boards work-item update \
    --org "$org" \
    --id "$id" \
    "${field_args[@]}" \
    --output none

  if [ $? -eq 0 ]; then
    echo "Updated work item $id"
    return 0
  else
    echo "ERROR: Failed to update work item $id" >&2
    return 1
  fi
}

# Example: Update state and add tags
update_work_item \
  "https://dev.azure.com/MyOrg" \
  "$feature_id" \
  "System.State=Active" \
  "System.Tags=authentication;security;oauth"
```

## Common Workflows

### 1. Create Epic with Features and Stories

```bash
# Set common variables
ORG="https://dev.azure.com/MyOrg"
PROJECT="MyProject"
AREA="MyProject\\Platform"

# Create Epic
epic_desc="<p>Complete user authentication system</p><ul><li>OAuth 2.0</li><li>Session management</li><li>RBAC</li></ul>"
epic_id=$(create_work_item "$ORG" "$PROJECT" "Epic" "Authentication System" "$epic_desc" "$AREA")

# Create Features
feature1_id=$(create_work_item "$ORG" "$PROJECT" "Feature" "OAuth Integration" "<p>Integrate OAuth provider</p>" "$AREA")
link_parent "$ORG" "$feature1_id" "$epic_id"

feature2_id=$(create_work_item "$ORG" "$PROJECT" "Feature" "Session Management" "<p>Implement session handling</p>" "$AREA")
link_parent "$ORG" "$feature2_id" "$epic_id"

# Create User Stories under Feature
story1_id=$(create_work_item "$ORG" "$PROJECT" "User Story" "Google OAuth Login" "<p>Allow users to log in with Google</p>" "$AREA")
link_parent "$ORG" "$story1_id" "$feature1_id"

story2_id=$(create_work_item "$ORG" "$PROJECT" "User Story" "GitHub OAuth Login" "<p>Allow users to log in with GitHub</p>" "$AREA")
link_parent "$ORG" "$story2_id" "$feature1_id"
```

### 2. Bulk Create Tasks from List

```bash
# Tasks for a User Story
STORY_ID=12345
TASKS=("Implement OAuth client" "Add login UI" "Write unit tests" "Update documentation")

for task_title in "${TASKS[@]}"; do
  task_id=$(create_work_item "$ORG" "$PROJECT" "Task" "$task_title" "<p>Task details</p>" "$AREA")
  if [ $? -eq 0 ]; then
    link_parent "$ORG" "$task_id" "$STORY_ID"
    echo "Created task: $task_id - $task_title"
  fi
done
```

### 3. Query and Update Work Items

```bash
# Find all Bugs in "New" state
bugs=$(az boards query \
  --org "$ORG" \
  --project "$PROJECT" \
  --wiql "SELECT [System.Id] FROM workitems WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'New'" \
  --output tsv | tail -n +3)  # Skip header rows

# Assign all to security team
for bug_id in $bugs; do
  update_work_item "$ORG" "$bug_id" "System.AssignedTo=security-team@myorg.com" "System.Tags=triage-needed"
done
```

## Critical Learnings

### 1. HTML Formatting in Descriptions

Work item descriptions support HTML tags. Common patterns:

- Paragraphs: `<p>text</p>`
- Lists: `<ul><li>item</li></ul>`
- Bold: `<strong>text</strong>`
- Code: `<code>inline</code>` or `<pre><code>block</code></pre>`
- Links: `<a href="url">text</a>`

**Anti-pattern:** Plain text without formatting looks unprofessional in Azure DevOps UI.

### 2. Two-Step Parent Linking

**YOU CANNOT** create a work item with parent in single command. Must use two steps:

1. Create child work item (get ID)
2. Add parent relationship with `az boards work-item relation add`

**Why:** Azure DevOps API requires work item to exist before establishing relationships.

### 3. Area Path Required

**ALWAYS** specify area path when creating work items. Format: `ProjectName\\TeamName\\SubArea`

**Default behavior:** If omitted, uses project root which may not match your team's conventions.

**Discovery:** Use `az boards area project list` to see valid area paths.

### 4. Work Item Types Vary by Project

**Standard types:** Epic, Feature, "User Story", Task, Bug, Issue

**Custom types:** Projects may define custom types like "Scenario", "Requirement", "Test Case", etc.

**Discovery:** Check project settings or use `az boards work-item show --id <any-id>` and inspect `fields."System.WorkItemType"`.

**IMPORTANT:** Type names with spaces require quotes: `--type "User Story"`

## Quick Reference

```bash
# Common field names
System.Title
System.Description
System.State
System.AssignedTo
System.AreaPath
System.IterationPath
System.Tags
System.Parent
Microsoft.VSTS.Common.Priority
Microsoft.VSTS.Common.Severity

# Common states (vary by type)
New, Active, Resolved, Closed
Proposed, In Progress, Completed

# Query operators
=, <>, <, >, <=, >=
IN, NOT IN
LIKE, NOT LIKE
UNDER (for area/iteration paths)
```

## See Also

- [`examples/common-workflows.md`](examples/common-workflows.md) - Complete workflow examples
- [`reference/work-item-types.md`](reference/work-item-types.md) - Work item type details
- [`reference/field-reference.md`](reference/field-reference.md) - Complete field reference
- [Azure DevOps CLI Documentation](https://learn.microsoft.com/en-us/cli/azure/boards)
- [WIQL Reference](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
