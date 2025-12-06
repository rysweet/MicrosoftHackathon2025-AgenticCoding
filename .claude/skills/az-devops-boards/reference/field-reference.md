# Work Item Field Reference

Complete reference fer Azure DevOps work item fields an' their usage patterns.

## Field Naming Conventions

Azure DevOps uses three field namespaces:

1. **System.\***: Core work item fields (title, state, area, etc.)
2. **Microsoft.VSTS.\***: Visual Studio Team Services fields (priority, severity, estimates, etc.)
3. **Custom.\***: Custom fields defined by your organization

## Core System Fields

### System.Id

**Type**: Integer (read-only)
**Description**: Unique work item identifier
**Usage**: Returned when creating work items, used for queries and updates

```bash
# Capture ID when creating
work_item_id=$(create_work_item ... | grep -o '[0-9]*')

# Use in queries
wiql="SELECT [System.Id] FROM workitems WHERE [System.Id] = 12345"
```

### System.Title

**Type**: String (255 chars max)
**Description**: Work item title/summary
**Required**: Yes
**Usage**: Main identifier in lists and queries

```bash
az boards work-item create ... --title "User can log in with OAuth"

# Query by title
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.Title] CONTAINS 'OAuth'"
```

### System.Description

**Type**: HTML text
**Description**: Detailed description of work item
**HTML Support**: Yes - use `<p>`, `<ul>`, `<li>`, `<strong>`, `<code>`, etc.

```bash
description="<p>Detailed description with <strong>bold</strong> text</p><ul><li>Item 1</li><li>Item 2</li></ul>"
az boards work-item create ... --description "$description"
```

### System.State

**Type**: String (from predefined list)
**Description**: Current workflow state
**Valid Values**: Varies by work item type and process template

Common states:

- **Epic/Feature/Story**: New, Active, Resolved, Closed
- **Task**: To Do, In Progress, Done
- **Bug**: New, Active, Resolved, Closed

```bash
# Update state
update_work_item "$ORG" "$id" "System.State=Active"

# Query by state
wiql="SELECT [System.Id] FROM workitems WHERE [System.State] = 'Active'"
```

### System.Reason

**Type**: String (read-only, auto-set)
**Description**: Reason for state transition
**Values**: Varies by state transition (e.g., "New", "Fixed", "Deferred")

### System.AssignedTo

**Type**: Identity (user reference)
**Description**: Person responsible for work item
**Format**: Email address or display name

```bash
# Assign to user
update_work_item "$ORG" "$id" "System.AssignedTo=user@myorg.com"

# Assign to me
update_work_item "$ORG" "$id" "System.AssignedTo=@Me"

# Unassign
update_work_item "$ORG" "$id" "System.AssignedTo="

# Query unassigned
wiql="SELECT [System.Id] FROM workitems WHERE [System.AssignedTo] = ''"
```

### System.CreatedBy

**Type**: Identity (read-only)
**Description**: Person who created work item

### System.CreatedDate

**Type**: DateTime (read-only)
**Description**: When work item was created

```bash
# Query recent items
wiql="SELECT [System.Id] FROM workitems WHERE [System.CreatedDate] >= @Today - 7"
```

### System.ChangedBy

**Type**: Identity (read-only)
**Description**: Person who last modified work item

### System.ChangedDate

**Type**: DateTime (read-only)
**Description**: When work item was last modified

```bash
# Query stale items
wiql="SELECT [System.Id] FROM workitems WHERE [System.ChangedDate] < @Today - 30"
```

### System.AreaPath

**Type**: String (tree path)
**Description**: Logical area for organizing work
**Format**: `ProjectName\TeamName\SubArea` (backslash-separated)
**Required**: Yes (defaults to project root)

```bash
# Set area when creating
create_work_item "$ORG" "$PROJECT" "Task" "Title" "Description" "MyProject\\Platform\\Security"

# Query by area (exact)
wiql="SELECT [System.Id] FROM workitems WHERE [System.AreaPath] = 'MyProject\\Platform'"

# Query by area (includes children)
wiql="SELECT [System.Id] FROM workitems WHERE [System.AreaPath] UNDER 'MyProject\\Platform'"

# List available areas
az boards area project list --org "$ORG" --project "$PROJECT"
```

### System.IterationPath

**Type**: String (tree path)
**Description**: Sprint or iteration for scheduling
**Format**: `ProjectName\SprintName` (backslash-separated)

```bash
# Set iteration
update_work_item "$ORG" "$id" "System.IterationPath=MyProject\\Sprint 23"

# Query current sprint work
wiql="SELECT [System.Id] FROM workitems WHERE [System.IterationPath] = @CurrentIteration"

# List available iterations
az boards iteration project list --org "$ORG" --project "$PROJECT"
```

### System.Tags

**Type**: String (semicolon-separated)
**Description**: Free-form labels for categorization
**Format**: `tag1;tag2;tag3`

```bash
# Set tags
update_work_item "$ORG" "$id" "System.Tags=security;high-priority;auth"

# Add tags (append)
# Note: Must read current tags first, then append
current_tags=$(az boards work-item show --id "$id" --org "$ORG" --output json | jq -r '.fields."System.Tags" // ""')
new_tags="${current_tags};new-tag"
update_work_item "$ORG" "$id" "System.Tags=$new_tags"

# Query by tag
wiql="SELECT [System.Id] FROM workitems WHERE [System.Tags] CONTAINS 'security'"
```

### System.WorkItemType

**Type**: String (read-only)
**Description**: Type of work item (Epic, Feature, User Story, etc.)
**Set at creation**: Cannot be changed after creation

```bash
# Query by type
wiql="SELECT [System.Id] FROM workitems WHERE [System.WorkItemType] = 'User Story'"
```

### System.Parent

**Type**: Integer (work item ID reference)
**Description**: Parent work item in hierarchy
**Note**: Use `az boards work-item relation add` to set, not direct field update

```bash
# Link parent (correct way)
link_parent "$ORG" "$child_id" "$parent_id"

# Query children of parent
wiql="SELECT [System.Id] FROM workitems WHERE [System.Parent] = 12345"
```

## Microsoft VSTS Fields

### Microsoft.VSTS.Common.Priority

**Type**: Integer (1-4)
**Description**: Priority rating (1=highest, 4=lowest)
**Common Usage**: Bugs, User Stories

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Common.Priority=1"

# Query high priority
wiql="SELECT [System.Id] FROM workitems WHERE [Microsoft.VSTS.Common.Priority] = 1"
```

### Microsoft.VSTS.Common.Severity

**Type**: Integer (1-4)
**Description**: Severity rating for bugs (1=Critical, 4=Low)
**Common Usage**: Bugs

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Common.Severity=1"

# Query critical bugs
wiql="SELECT [System.Id] FROM workitems WHERE [System.WorkItemType] = 'Bug' AND [Microsoft.VSTS.Common.Severity] = 1"
```

### Microsoft.VSTS.Common.ValueArea

**Type**: String (Architectural, Business)
**Description**: Whether work is business-facing or architectural
**Common Usage**: Features, User Stories

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Common.ValueArea=Business"
```

### Microsoft.VSTS.Common.AcceptanceCriteria

**Type**: HTML text
**Description**: Criteria for accepting work as done
**Common Usage**: User Stories

```bash
acceptance="<p><strong>Acceptance Criteria:</strong></p><ul><li>User can log in</li><li>Session persists</li><li>Error handling works</li></ul>"
update_work_item "$ORG" "$id" "Microsoft.VSTS.Common.AcceptanceCriteria=$acceptance"
```

### Microsoft.VSTS.Common.BusinessValue

**Type**: Integer
**Description**: Numerical business value rating
**Common Usage**: Features, User Stories (for prioritization)

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Common.BusinessValue=100"
```

### Microsoft.VSTS.Common.Risk

**Type**: Integer (1-3)
**Description**: Risk level (1=High, 2=Medium, 3=Low)
**Common Usage**: Features, Epics

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Common.Risk=2"
```

### Microsoft.VSTS.Scheduling.StoryPoints

**Type**: Double
**Description**: Effort estimate in story points
**Common Usage**: User Stories (Scrum template)

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Scheduling.StoryPoints=5"

# Query by story points
wiql="SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.StoryPoints] FROM workitems WHERE [Microsoft.VSTS.Scheduling.StoryPoints] >= 8"
```

### Microsoft.VSTS.Scheduling.OriginalEstimate

**Type**: Double (hours)
**Description**: Original work estimate
**Common Usage**: Tasks

```bash
update_work_item "$ORG" "$id" \
  "Microsoft.VSTS.Scheduling.OriginalEstimate=8" \
  "Microsoft.VSTS.Scheduling.RemainingWork=8"
```

### Microsoft.VSTS.Scheduling.RemainingWork

**Type**: Double (hours)
**Description**: Remaining work estimate
**Common Usage**: Tasks

```bash
# Update as work progresses
update_work_item "$ORG" "$id" "Microsoft.VSTS.Scheduling.RemainingWork=4"

# Query tasks with remaining work
wiql="SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.RemainingWork] FROM workitems WHERE [System.WorkItemType] = 'Task' AND [Microsoft.VSTS.Scheduling.RemainingWork] > 0"
```

### Microsoft.VSTS.Scheduling.CompletedWork

**Type**: Double (hours)
**Description**: Completed work hours
**Common Usage**: Tasks

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.Scheduling.CompletedWork=4"
```

### Microsoft.VSTS.TCM.ReproSteps

**Type**: HTML text
**Description**: Steps to reproduce bug
**Common Usage**: Bugs

```bash
repro="<p><strong>Steps:</strong></p><ol><li>Open login page</li><li>Enter credentials</li><li>Click login</li></ol><p><strong>Expected:</strong> Success</p><p><strong>Actual:</strong> Error</p>"
update_work_item "$ORG" "$id" "Microsoft.VSTS.TCM.ReproSteps=$repro"
```

### Microsoft.VSTS.TCM.SystemInfo

**Type**: String
**Description**: System/environment information
**Common Usage**: Bugs

```bash
update_work_item "$ORG" "$id" "Microsoft.VSTS.TCM.SystemInfo=Windows 11, Chrome 120, .NET 8"
```

## Custom Fields

Custom fields follow the pattern `Custom.FieldName` or `OrganizationName.FieldName`.

### Discovering Custom Fields

```bash
# Show all fields for a work item
az boards work-item show --id "$id" --org "$ORG" --output json | jq '.fields | keys'

# Filter for custom fields
az boards work-item show --id "$id" --org "$ORG" --output json | jq '.fields | keys | .[] | select(startswith("Custom.") or (startswith("System.") | not) and (startswith("Microsoft.") | not))'
```

### Using Custom Fields

```bash
# Set custom field
update_work_item "$ORG" "$id" "Custom.ApprovalStatus=Approved"

# Query by custom field
wiql="SELECT [System.Id] FROM workitems WHERE [Custom.ApprovalStatus] = 'Approved'"
```

## Field Validation Rules

### HTML Fields

Fields supporting HTML:

- System.Description
- Microsoft.VSTS.Common.AcceptanceCriteria
- Microsoft.VSTS.TCM.ReproSteps

**Allowed tags**: `<p>`, `<br>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<code>`, `<pre>`, `<a>`, `<h1>`-`<h6>`, `<table>`, `<tr>`, `<td>`, `<th>`

**Sanitization**: Azure DevOps sanitizes HTML input, removing potentially dangerous tags like `<script>`, `<iframe>`, etc.

```bash
# Good HTML usage
description="<p>This is a paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul>"

# Avoid inline styles (may be stripped)
description="<p style='color: red'>Text</p>"  # Style may be removed
```

### Identity Fields

Fields accepting user identities:

- System.AssignedTo
- System.CreatedBy (read-only)
- System.ChangedBy (read-only)

**Valid formats**:

- Email: `user@myorg.com`
- Display name: `John Doe` (if unique)
- Special: `@Me` (current user)

```bash
# Email format (recommended)
update_work_item "$ORG" "$id" "System.AssignedTo=user@myorg.com"

# Display name (if unique in org)
update_work_item "$ORG" "$id" "System.AssignedTo=John Doe"

# Current user
update_work_item "$ORG" "$id" "System.AssignedTo=@Me"
```

### Date/Time Fields

**Format**: ISO 8601: `YYYY-MM-DDTHH:MM:SSZ`

**Special values in WIQL**:

- `@Today`: Current date
- `@Today - 7`: 7 days ago
- `@CurrentIteration`: Current sprint

```bash
# Query with date
wiql="SELECT [System.Id] FROM workitems WHERE [System.CreatedDate] >= '2024-01-01T00:00:00Z'"

# Query with special value
wiql="SELECT [System.Id] FROM workitems WHERE [System.CreatedDate] >= @Today - 7"
```

## Quick Reference Table

| Field                                   | Type     | Editable     | Common Usage         |
| --------------------------------------- | -------- | ------------ | -------------------- |
| System.Id                               | Integer  | No           | Unique identifier    |
| System.Title                            | String   | Yes          | Work item title      |
| System.Description                      | HTML     | Yes          | Detailed description |
| System.State                            | String   | Yes          | Workflow state       |
| System.AssignedTo                       | Identity | Yes          | Assignee             |
| System.AreaPath                         | TreePath | Yes          | Logical area         |
| System.IterationPath                    | TreePath | Yes          | Sprint/iteration     |
| System.Tags                             | String   | Yes          | Free-form tags       |
| System.Parent                           | Integer  | Via relation | Parent work item     |
| Microsoft.VSTS.Common.Priority          | Integer  | Yes          | Priority (1-4)       |
| Microsoft.VSTS.Common.Severity          | Integer  | Yes          | Bug severity         |
| Microsoft.VSTS.Scheduling.StoryPoints   | Double   | Yes          | Effort estimate      |
| Microsoft.VSTS.Scheduling.RemainingWork | Double   | Yes          | Remaining hours      |

## See Also

- [`work-item-types.md`](work-item-types.md) - Work item type reference
- [`../examples/common-workflows.md`](../examples/common-workflows.md) - Usage examples
- [Azure DevOps Field Reference](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/work-item-field)
- [WIQL Syntax Reference](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
