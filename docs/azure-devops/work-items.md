# Work Item Management Guide

Complete guide to creating and managing work items with Azure DevOps CLI tools.

## Work Item Types

Standard types in most projects:

- **Epic** - Large body of work (months)
- **Feature** - Shippable functionality (weeks)
- **User Story** - User-facing feature (days)
- **Task** - Technical work (hours/days)
- **Bug** - Defect or issue

Check available types in yer project:

```bash
python -m .claude.scenarios.az-devops-tools.list_types
```

## Creating Work Items

### Basic Creation

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type "User Story" \
  --title "Implement user login"
```

### With Description (Markdown Auto-Converted)

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type "User Story" \
  --title "User authentication" \
  --description "# Story

As a user, I want to log in with my credentials.

## Acceptance Criteria
- User can enter email/password
- System validates credentials
- Invalid login shows error message"
```

### With All Options

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type Bug \
  --title "Login button not responding" \
  --description "Button click does nothing" \
  --assigned-to user@example.com \
  --area "MyProject\\Frontend" \
  --iteration "MyProject\\Sprint 1" \
  --tags "ui,critical,login" \
  --fields "Microsoft.VSTS.Common.Priority=1" \
  --fields "Microsoft.VSTS.Common.Severity=1-Critical"
```

### With Parent Link

```bash
# Creates Task and links to Story #1234
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type Task \
  --title "Write unit tests" \
  --parent 1234
```

## Linking Work Items

Create parent-child relationships:

```bash
# Link Task #5678 to Story #1234
python -m .claude.scenarios.az-devops-tools.link_parent \
  --child 5678 \
  --parent 1234
```

Valid relationships:

- Task → User Story, Bug, Feature, Epic
- Bug → Feature, Epic
- User Story → Feature, Epic
- Feature → Epic

## Common Workflows

### Create Epic with Features

```bash
# Create Epic
epic_output=$(python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type Epic \
  --title "Authentication System")
epic_id=$(echo "$epic_output" | grep "ID:" | awk '{print $2}')

# Create Features under Epic
for feature in "OAuth Integration" "Session Management" "RBAC"; do
  python -m .claude.scenarios.az-devops-tools.create_work_item \
    --type Feature \
    --title "$feature" \
    --parent "$epic_id"
done
```

### Create Story with Tasks

```bash
# Create Story
story_output=$(python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type "User Story" \
  --title "Implement login UI")
story_id=$(echo "$story_output" | grep "ID:" | awk '{print $2}')

# Create Tasks
for task in "Design mockup" "Implement form" "Add validation" "Write tests"; do
  python -m .claude.scenarios.az-devops-tools.create_work_item \
    --type Task \
    --title "$task" \
    --parent "$story_id"
done
```

### Bulk Import from CSV

```python
import csv
from .claude.scenarios.az_devops_tools.create_work_item import create_work_item

with open('stories.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        work_item = create_work_item(
            title=row['title'],
            work_item_type="User Story",
            org=org,
            project=project,
            description=row['description'],
            tags=row.get('tags', '').split(','),
        )
        print(f"Created: {work_item['id']}")
```

## Field Reference

### Common System Fields

- `System.Title` - Work item title (required)
- `System.Description` - HTML description
- `System.State` - Current state (New, Active, Closed, etc.)
- `System.AssignedTo` - Assigned user (email or display name)
- `System.AreaPath` - Area path (format: Project\\Team\\Area)
- `System.IterationPath` - Sprint/iteration
- `System.Tags` - Comma-separated tags

### Microsoft VSTS Fields

- `Microsoft.VSTS.Common.Priority` - 1 (highest) to 4 (lowest)
- `Microsoft.VSTS.Common.Severity` - 1-Critical, 2-High, 3-Medium, 4-Low
- `Microsoft.VSTS.Common.StackRank` - Backlog ordering

### Discover All Fields

```bash
# Show fields for specific type
python -m .claude.scenarios.az-devops-tools.list_types --type "User Story"

# Show all fields including system
python -m .claude.scenarios.az-devops-tools.list_types --type Bug --all-fields
```

## Tips and Best Practices

1. **Use markdown descriptions** - Auto-converted to HTML for better formatting
2. **Set area path** - Helps with team organization and queries
3. **Link work items early** - Easier to track relationships
4. **Use tags** - Improves searchability
5. **Validate types first** - Use list_types before creating

## Troubleshooting

### "Invalid work item type"

Check available types:

```bash
python -m .claude.scenarios.az-devops-tools.list_types
```

### "Work item type with spaces"

Use quotes:

```bash
--type "User Story"  # Correct
--type User Story    # Wrong
```

### "Parent link failed"

Verify both IDs exist and relationship be valid.

## See Also

- [WIQL Queries](queries.md) - Query work items
- [HTML Formatting](html-formatting.md) - Rich descriptions
- [MS Learn: Work Items](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/)
