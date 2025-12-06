# WIQL Query Guide

Work Item Query Language (WIQL) guide fer querying Azure DevOps work items.

## Predefined Queries

Five common queries be built-in:

### my-items

Yer assigned open work items:

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query my-items
```

### unassigned

Open work items with no assignee:

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query unassigned
```

### recent

Recently changed work items:

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query recent
```

### active-bugs

Open bugs by priority:

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query active-bugs
```

### active-stories

Open user stories:

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query active-stories
```

## Custom WIQL Queries

### Basic Syntax

```sql
SELECT [Field1], [Field2], [Field3]
FROM workitems
WHERE [Condition]
ORDER BY [Field] ASC/DESC
```

### Example: Active Tasks

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType] = 'Task' AND [System.State] = 'Active'"
```

### Example: High Priority Bugs

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title], [Microsoft.VSTS.Common.Priority] FROM workitems WHERE [System.WorkItemType] = 'Bug' AND [Microsoft.VSTS.Common.Priority] = 1"
```

### Example: Recently Created

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.CreatedDate] >= @Today - 7 ORDER BY [System.CreatedDate] DESC"
```

## Output Formats

### Table (Default)

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query my-items
```

Output:

```
ID    | Type        | State  | Title                | Assigned To
------+-------------+--------+---------------------+--------------
1234  | User Story  | Active | Implement login     | John Doe
5678  | Bug         | New    | Button not working  | John Doe
```

### JSON

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --query my-items \
  --format json
```

### CSV

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --query my-items \
  --format csv > my_items.csv
```

### IDs Only

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --query my-items \
  --format ids-only
```

Output:

```
1234
5678
9012
```

## Limit Results

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --query recent \
  --limit 10
```

## Common Fields

### System Fields

- `[System.Id]` - Work item ID
- `[System.Title]` - Title
- `[System.WorkItemType]` - Type (Bug, Task, Story, etc.)
- `[System.State]` - State (New, Active, Closed, etc.)
- `[System.AssignedTo]` - Assigned user
- `[System.CreatedDate]` - Creation date
- `[System.ChangedDate]` - Last modified date
- `[System.AreaPath]` - Area path
- `[System.IterationPath]` - Sprint/iteration
- `[System.Tags]` - Tags

### Microsoft VSTS Fields

- `[Microsoft.VSTS.Common.Priority]` - Priority (1-4)
- `[Microsoft.VSTS.Common.Severity]` - Severity (1-4)
- `[Microsoft.VSTS.Common.StackRank]` - Backlog rank

## Operators

### Comparison

- `=` - Equals
- `<>` - Not equals
- `<` - Less than
- `>` - Greater than
- `<=` - Less than or equal
- `>=` - Greater than or equal

### Logical

- `AND` - Both conditions true
- `OR` - Either condition true
- `NOT` - Negate condition

### String

- `CONTAINS` - Field contains value
- `LIKE` - Pattern matching

### Special

- `IN` - Value in list
- `UNDER` - Under area/iteration path
- `@Me` - Current user
- `@Today` - Current date
- `@Project` - Current project

## Example Queries

### Find Bugs Assigned to Me

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType] = 'Bug' AND [System.AssignedTo] = @Me"
```

### Find Stories in Sprint

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType] = 'User Story' AND [System.IterationPath] = 'MyProject\\Sprint 1'"
```

### Find Items with Tag

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.Tags] CONTAINS 'security'"
```

### Find Items in Area

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --wiql "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.AreaPath] UNDER 'MyProject\\Platform'"
```

## Programmatic Usage

```python
from .claude.scenarios.az_devops_tools.query_wiql import execute_wiql

wiql = """
    SELECT [System.Id], [System.Title], [System.State]
    FROM workitems
    WHERE [System.AssignedTo] = @Me
    AND [System.State] <> 'Closed'
"""

work_items = execute_wiql(
    wiql=wiql,
    org="https://dev.azure.com/myorg",
    project="MyProject",
    limit=100,
)

for item in work_items:
    print(f"{item['id']}: {item['fields']['System.Title']}")
```

## Tips

1. Test queries in Azure DevOps web UI first
2. Use `--limit` fer large result sets
3. Use `@Me`, `@Today`, `@Project` fer dynamic queries
4. Escape single quotes in strings with two single quotes
5. Field names be case-sensitive

## See Also

- [WIQL Syntax Reference](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
- [Work Items Guide](work-items.md)
