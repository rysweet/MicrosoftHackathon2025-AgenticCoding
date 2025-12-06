# Work Item Types Reference

Azure DevOps work item types an' their hierarchy rules.

## Standard Work Item Types

### Epic

**Purpose**: Large body of work that can be broken down into Features.

**Typical hierarchy**: Top-level planning item

**Common fields**:

- System.Title
- System.Description
- System.State (New, Active, Resolved, Closed)
- System.AreaPath
- System.IterationPath
- Microsoft.VSTS.Common.Priority (1-4, where 1 is highest)

**Children**: Features, User Stories (in some templates)

**Example usage**:

```bash
epic_id=$(create_work_item "$ORG" "$PROJECT" "Epic" \
  "Platform Modernization" \
  "<p>Modernize core platform infrastructure</p>" \
  "MyProject\\Platform")
```

### Feature

**Purpose**: A service that fulfills stakeholder need. Can be broken down into User Stories.

**Typical hierarchy**: Child of Epic, parent of User Stories

**Common fields**:

- Same as Epic
- Microsoft.VSTS.Common.BusinessValue (numeric)
- Microsoft.VSTS.Common.Risk (1-High, 2-Medium, 3-Low)

**Children**: User Stories, Tasks (in some templates)

**Parent**: Epic

**Example usage**:

```bash
feature_id=$(create_work_item "$ORG" "$PROJECT" "Feature" \
  "API Gateway" \
  "<p>Implement API gateway for service mesh</p>" \
  "MyProject\\Platform")
link_parent "$ORG" "$feature_id" "$epic_id"
```

### User Story

**Purpose**: Describes functionality from user's perspective. Work that can be completed in a sprint.

**Typical hierarchy**: Child of Feature, parent of Tasks

**Common fields**:

- Same as Feature
- Microsoft.VSTS.Common.AcceptanceCriteria (HTML text)
- Microsoft.VSTS.Scheduling.StoryPoints (numeric, e.g., Fibonacci: 1,2,3,5,8,13)

**Children**: Tasks

**Parent**: Feature (or Epic in some templates)

**Special note**: Type name has space - requires quotes in CLI

**Example usage**:

```bash
story_id=$(create_work_item "$ORG" "$PROJECT" "User Story" \
  "User can log in with OAuth" \
  "<p>As a user, I want to log in using my Google account</p>" \
  "MyProject\\Platform")
link_parent "$ORG" "$story_id" "$feature_id"
```

### Task

**Purpose**: Smallest unit of work. Implementation detail.

**Typical hierarchy**: Child of User Story, Bug, or Feature

**Common fields**:

- Same as User Story
- Microsoft.VSTS.Scheduling.RemainingWork (hours)
- Microsoft.VSTS.Scheduling.OriginalEstimate (hours)
- Microsoft.VSTS.Scheduling.CompletedWork (hours)
- System.AssignedTo (specific developer)

**States**: To Do, In Progress, Done (varies by template)

**Parent**: User Story, Bug, or Feature

**Example usage**:

```bash
task_id=$(create_work_item "$ORG" "$PROJECT" "Task" \
  "Implement OAuth client" \
  "<p>Configure OAuth 2.0 client library</p>" \
  "MyProject\\Platform")
link_parent "$ORG" "$task_id" "$story_id"

# Set work estimates
update_work_item "$ORG" "$task_id" \
  "Microsoft.VSTS.Scheduling.OriginalEstimate=8" \
  "Microsoft.VSTS.Scheduling.RemainingWork=8"
```

### Bug

**Purpose**: Track defects and issues.

**Typical hierarchy**: Can be standalone or child of User Story/Feature

**Common fields**:

- Microsoft.VSTS.Common.Severity (1-Critical, 2-High, 3-Medium, 4-Low)
- Microsoft.VSTS.Common.Priority (1-4)
- Microsoft.VSTS.TCM.ReproSteps (HTML text)
- Microsoft.VSTS.TCM.SystemInfo (text)
- System.Reason (reason for current state)

**States**: New, Active, Resolved, Closed

**Children**: Tasks

**Example usage**:

```bash
bug_id=$(create_work_item "$ORG" "$PROJECT" "Bug" \
  "Login fails with special characters in password" \
  "<p><strong>Steps to reproduce:</strong></p><ol><li>Navigate to login page</li><li>Enter password with special chars</li><li>Click login</li></ol><p><strong>Expected:</strong> Login succeeds</p><p><strong>Actual:</strong> Error message displayed</p>" \
  "MyProject\\Platform")

update_work_item "$ORG" "$bug_id" \
  "Microsoft.VSTS.Common.Severity=2" \
  "Microsoft.VSTS.Common.Priority=1"
```

### Issue

**Purpose**: Track impediments, questions, or general items (varies by template).

**Typical hierarchy**: Usually standalone, but can have parent

**Common fields**:

- Same as Bug (severity, priority)
- Microsoft.VSTS.Common.Issue (text)

**States**: Active, Resolved, Closed

**Example usage**:

```bash
issue_id=$(create_work_item "$ORG" "$PROJECT" "Issue" \
  "Need access to production logs" \
  "<p>Development team needs read access to prod logs for debugging</p>" \
  "MyProject\\Platform")
```

## Custom Work Item Types

Projects can define custom types. Common custom types:

### Scenario

**Purpose**: High-level business scenario or use case (Microsoft OS project uses this)

**Typical hierarchy**: Similar to Epic, may be parent of Features

**Discovery**: Check project to see if available

### Requirement

**Purpose**: Formal requirement documentation (common in regulated industries)

**Typical hierarchy**: May be parent of User Stories or Features

### Test Case

**Purpose**: Formal test case definition

**Typical hierarchy**: Linked to User Stories or Features (not parent-child)

### Test Plan / Test Suite

**Purpose**: Organize test cases

**Typical hierarchy**: Test Plan > Test Suite > Test Cases

## Type Hierarchy Rules

### Scrum Template (Most Common)

```
Epic
└── Feature
    └── User Story
        └── Task

Bug (standalone or under Feature/Story)
```

### Agile Template

```
Epic
└── Feature
    └── User Story
        └── Task

Bug (standalone or under Feature/Story)
Issue (standalone)
```

### CMMI Template

```
Epic
└── Feature
    └── Requirement
        └── Task

Bug (standalone or under Requirement)
Issue (standalone)
Change Request (standalone)
Risk (standalone)
```

## Discovering Custom Types

### Method 1: Inspect Existing Work Item

```bash
az boards work-item show --id <any-id> --org $ORG --output json | jq '.fields."System.WorkItemType"'
```

### Method 2: List All Types in Project

Not directly available via CLI. Use Azure DevOps REST API:

```bash
curl -u :$AZURE_DEVOPS_PAT \
  "https://dev.azure.com/$ORG_NAME/$PROJECT/_apis/wit/workitemtypes?api-version=7.0" \
  | jq '.value[].name'
```

### Method 3: Check Project Settings

Navigate to Project Settings > Boards > Process in Azure DevOps UI to see all available types.

## Work Item Type Selection Guide

| Scenario                     | Type to Use | Notes                 |
| ---------------------------- | ----------- | --------------------- |
| Large initiative (6+ months) | Epic        | Break into Features   |
| Product feature              | Feature     | Break into Stories    |
| User-facing functionality    | User Story  | Deliverable in sprint |
| Implementation work          | Task        | Hours/days of work    |
| Defect/bug                   | Bug         | Use severity/priority |
| Blocker/question             | Issue       | Use for impediments   |
| Custom business concept      | Custom Type | Check if exists first |

## Common Mistakes

**Using wrong parent-child relationships**:

- ❌ Task → User Story (backwards)
- ✅ User Story → Task (correct)

**Type name typos**:

- ❌ `--type "UserStory"` (no space)
- ✅ `--type "User Story"` (with space)

**Assuming all projects have same types**:

- Different templates = different types
- Always discover types first

**Creating wrong type for need**:

- Don't create Epic for small task
- Don't create Task for feature-level work

## Related Commands

```bash
# Show work item with all fields
az boards work-item show --id <id> --org $ORG --output json

# Query by type
az boards query --org $ORG --project $PROJECT \
  --wiql "SELECT [System.Id] FROM workitems WHERE [System.WorkItemType] = 'Epic'"

# Create with multiple fields
az boards work-item create --org $ORG --project $PROJECT \
  --type "User Story" \
  --title "Title" \
  --description "Description" \
  --fields "System.Tags=tag1;tag2" "Microsoft.VSTS.Scheduling.StoryPoints=5"
```

## See Also

- [`field-reference.md`](field-reference.md) - Complete field reference
- [`../examples/common-workflows.md`](../examples/common-workflows.md) - Workflow examples
- [Azure DevOps Work Item Types](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/about-work-items)
