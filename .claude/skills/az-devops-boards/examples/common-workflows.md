# Common Azure DevOps Workflows

Complete examples fer real-world Azure DevOps work item management scenarios.

## Prerequisites

Source the shell functions from the main skill file first:

```bash
# Set your organization and project
export ADO_ORG="https://dev.azure.com/MyOrg"
export ADO_PROJECT="MyProject"
export ADO_AREA="MyProject\\Platform"
```

## Workflow 1: Create Complete Epic Hierarchy

Create an Epic with Features, User Stories, and Tasks in a single workflow.

### Scenario

Building a new authentication system with:

- 1 Epic: Authentication System
- 2 Features: OAuth Integration, Session Management
- 4 User Stories: Google login, GitHub login, Session storage, Token refresh
- 8 Tasks: Implementation tasks for each story

### Implementation

```bash
#!/bin/bash
# create-auth-epic.sh

# Epic description with HTML formatting
epic_desc=$(cat <<'EOF'
<p>Complete user authentication system with modern security practices.</p>
<h3>Key Components</h3>
<ul>
<li><strong>OAuth 2.0 Integration</strong>: Support for Google and GitHub</li>
<li><strong>Session Management</strong>: Secure token storage and refresh</li>
<li><strong>Role-Based Access Control</strong>: Permission management</li>
</ul>
<h3>Success Criteria</h3>
<ol>
<li>Users can authenticate with OAuth providers</li>
<li>Sessions persist across browser restarts</li>
<li>Security audit passes all checks</li>
</ol>
EOF
)

# Create Epic
echo "Creating Epic..."
epic_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "Epic" \
  "Authentication System" "$epic_desc" "$ADO_AREA")
echo "Epic ID: $epic_id"

# Feature 1: OAuth Integration
feature1_desc="<p>Integrate OAuth 2.0 providers (Google, GitHub) for user authentication.</p>"
feature1_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "Feature" \
  "OAuth Integration" "$feature1_desc" "$ADO_AREA")
link_parent "$ADO_ORG" "$feature1_id" "$epic_id"
echo "Feature 1 ID: $feature1_id"

# User Stories for Feature 1
story1_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "User Story" \
  "Google OAuth Login" \
  "<p>As a user, I want to log in with my Google account.</p>" \
  "$ADO_AREA")
link_parent "$ADO_ORG" "$story1_id" "$feature1_id"

story2_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "User Story" \
  "GitHub OAuth Login" \
  "<p>As a user, I want to log in with my GitHub account.</p>" \
  "$ADO_AREA")
link_parent "$ADO_ORG" "$story2_id" "$feature1_id"

# Tasks for Story 1 (Google OAuth)
tasks1=("Configure Google OAuth client" "Implement OAuth callback handler" "Add Google login button to UI" "Write integration tests")
for task_title in "${tasks1[@]}"; do
  task_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "Task" \
    "$task_title" "<p>Implementation task</p>" "$ADO_AREA")
  link_parent "$ADO_ORG" "$task_id" "$story1_id"
  echo "  Task: $task_id - $task_title"
done

# Tasks for Story 2 (GitHub OAuth)
tasks2=("Configure GitHub OAuth client" "Implement OAuth callback handler" "Add GitHub login button to UI" "Write integration tests")
for task_title in "${tasks2[@]}"; do
  task_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "Task" \
    "$task_title" "<p>Implementation task</p>" "$ADO_AREA")
  link_parent "$ADO_ORG" "$task_id" "$story2_id"
  echo "  Task: $task_id - $task_title"
done

# Feature 2: Session Management
feature2_desc="<p>Implement secure session management with token refresh.</p>"
feature2_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "Feature" \
  "Session Management" "$feature2_desc" "$ADO_AREA")
link_parent "$ADO_ORG" "$feature2_id" "$epic_id"
echo "Feature 2 ID: $feature2_id"

# User Stories for Feature 2
story3_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "User Story" \
  "Session Storage" \
  "<p>As a user, I want my session to persist across browser restarts.</p>" \
  "$ADO_AREA")
link_parent "$ADO_ORG" "$story3_id" "$feature2_id"

story4_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "User Story" \
  "Token Refresh" \
  "<p>As a user, I want my session to automatically refresh before expiration.</p>" \
  "$ADO_AREA")
link_parent "$ADO_ORG" "$story4_id" "$feature2_id"

echo "Complete hierarchy created successfully!"
echo "Epic: $epic_id"
echo "  Feature: $feature1_id (OAuth Integration)"
echo "  Feature: $feature2_id (Session Management)"
```

## Workflow 2: Bulk Operations from CSV

Import work items from a CSV file (useful for migrating from other systems).

### CSV Format

```csv
Type,Title,Description,Parent,Area,Tags
Epic,Platform Modernization,Modernize core platform,,MyProject\Platform,modernization
Feature,API Gateway,Implement API gateway,1,MyProject\Platform,api;gateway
User Story,Rate Limiting,Add rate limiting to API,2,MyProject\Platform,api;security
Task,Implement token bucket algorithm,Code implementation,3,MyProject\Platform,implementation
Task,Add rate limit headers,Add HTTP headers,3,MyProject\Platform,implementation
```

### Implementation

```bash
#!/bin/bash
# import-from-csv.sh

csv_file="$1"
declare -A work_item_map  # Map CSV row numbers to work item IDs

# Read CSV and create work items
line_num=0
while IFS=',' read -r type title description parent area tags; do
  line_num=$((line_num + 1))

  # Skip header row
  [ $line_num -eq 1 ] && continue

  # Create work item
  desc="<p>${description}</p>"
  work_item_id=$(create_work_item "$ADO_ORG" "$ADO_PROJECT" "$type" "$title" "$desc" "$area")

  if [ $? -eq 0 ]; then
    echo "Created $type: $work_item_id - $title"
    work_item_map[$line_num]=$work_item_id

    # Link to parent if specified
    if [ -n "$parent" ] && [ "$parent" != "Parent" ]; then
      parent_id=${work_item_map[$parent]}
      if [ -n "$parent_id" ]; then
        link_parent "$ADO_ORG" "$work_item_id" "$parent_id"
      fi
    fi

    # Add tags if specified
    if [ -n "$tags" ] && [ "$tags" != "Tags" ]; then
      update_work_item "$ADO_ORG" "$work_item_id" "System.Tags=${tags}"
    fi
  fi
done < "$csv_file"

echo "Import complete!"
```

## Workflow 3: Query and Bulk Update

Find work items matching criteria and apply bulk updates.

### Scenario 1: Triage New Bugs

Find all new bugs and assign to triage team with priority.

```bash
#!/bin/bash
# triage-new-bugs.sh

# Query for new bugs
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'New' AND [System.CreatedDate] >= @Today - 7"

echo "Querying new bugs from last 7 days..."
bug_ids=$(az boards query \
  --org "$ADO_ORG" \
  --project "$ADO_PROJECT" \
  --wiql "$wiql" \
  --output tsv | tail -n +3 | awk '{print $1}')

# Assign to triage team
triage_team="triage-team@myorg.com"
count=0

for bug_id in $bug_ids; do
  echo "Processing bug: $bug_id"
  update_work_item "$ADO_ORG" "$bug_id" \
    "System.AssignedTo=$triage_team" \
    "System.Tags=needs-triage" \
    "Microsoft.VSTS.Common.Priority=2"
  count=$((count + 1))
done

echo "Triaged $count bugs"
```

### Scenario 2: Close Completed Stories

Find all User Stories in "Resolved" state for more than 30 days and close them.

```bash
#!/bin/bash
# close-old-resolved-stories.sh

# Query for old resolved stories
wiql="SELECT [System.Id], [System.Title], [System.ChangedDate] FROM workitems WHERE [System.WorkItemType] = 'User Story' AND [System.State] = 'Resolved' AND [System.ChangedDate] < @Today - 30"

echo "Finding stories resolved over 30 days ago..."
story_ids=$(az boards query \
  --org "$ADO_ORG" \
  --project "$ADO_PROJECT" \
  --wiql "$wiql" \
  --output tsv | tail -n +3 | awk '{print $1}')

count=0
for story_id in $story_ids; do
  echo "Closing story: $story_id"
  update_work_item "$ADO_ORG" "$story_id" \
    "System.State=Closed" \
    "System.Tags=auto-closed"
  count=$((count + 1))
done

echo "Closed $count stories"
```

## Workflow 4: Cross-Project Operations

Work with multiple projects in same organization.

### Copy Work Item Structure Across Projects

```bash
#!/bin/bash
# copy-epic-structure.sh

source_project="SourceProject"
target_project="TargetProject"
source_epic_id="$1"

# Get source epic details
echo "Reading source epic $source_epic_id..."
source_epic=$(az boards work-item show \
  --org "$ADO_ORG" \
  --id "$source_epic_id" \
  --output json)

epic_title=$(echo "$source_epic" | jq -r '.fields."System.Title"')
epic_desc=$(echo "$source_epic" | jq -r '.fields."System.Description"')

# Create epic in target project
echo "Creating epic in target project..."
new_epic_id=$(create_work_item "$ADO_ORG" "$target_project" "Epic" \
  "$epic_title" "$epic_desc" "$target_project")

echo "Created new epic: $new_epic_id"

# Query child features in source project
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.Parent] = $source_epic_id AND [System.WorkItemType] = 'Feature'"

feature_ids=$(az boards query \
  --org "$ADO_ORG" \
  --project "$source_project" \
  --wiql "$wiql" \
  --output tsv | tail -n +3 | awk '{print $1}')

# Copy each feature
for feature_id in $feature_ids; do
  feature=$(az boards work-item show \
    --org "$ADO_ORG" \
    --id "$feature_id" \
    --output json)

  feature_title=$(echo "$feature" | jq -r '.fields."System.Title"')
  feature_desc=$(echo "$feature" | jq -r '.fields."System.Description"')

  echo "Copying feature: $feature_title"
  new_feature_id=$(create_work_item "$ADO_ORG" "$target_project" "Feature" \
    "$feature_title" "$feature_desc" "$target_project")

  link_parent "$ADO_ORG" "$new_feature_id" "$new_epic_id"
  echo "  Created feature: $new_feature_id"
done

echo "Cross-project copy complete!"
```

## Workflow 5: WIQL Query Patterns

Common WIQL query patterns fer findin' work items.

### Find Work Items by Tag

```bash
# Single tag
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.Tags] CONTAINS 'security'"

# Multiple tags (AND)
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.Tags] CONTAINS 'security' AND [System.Tags] CONTAINS 'high-priority'"

# Multiple tags (OR)
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.Tags] CONTAINS 'security' OR [System.Tags] CONTAINS 'compliance'"
```

### Find Work Items in Area Path

```bash
# Exact area
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.AreaPath] = 'MyProject\\Platform\\Security'"

# Under area (includes children)
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.AreaPath] UNDER 'MyProject\\Platform'"
```

### Find Work Items by Date

```bash
# Created in last 7 days
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.CreatedDate] >= @Today - 7"

# Changed today
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.ChangedDate] >= @Today"

# Not changed in 30 days
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.ChangedDate] < @Today - 30"
```

### Find Work Items by Assignment

```bash
# Assigned to specific user
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.AssignedTo] = 'user@myorg.com'"

# Unassigned
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.AssignedTo] = ''"

# Assigned to me
wiql="SELECT [System.Id], [System.Title] FROM workitems WHERE [System.AssignedTo] = @Me"
```

### Complex Queries

```bash
# Active User Stories with high priority in specific area
wiql="SELECT [System.Id], [System.Title], [Microsoft.VSTS.Common.Priority] FROM workitems WHERE [System.WorkItemType] = 'User Story' AND [System.State] = 'Active' AND [Microsoft.VSTS.Common.Priority] = 1 AND [System.AreaPath] UNDER 'MyProject\\Platform' ORDER BY [Microsoft.VSTS.Common.Priority] ASC"

# Bugs not resolved in 30 days
wiql="SELECT [System.Id], [System.Title], [System.CreatedDate] FROM workitems WHERE [System.WorkItemType] = 'Bug' AND [System.State] <> 'Resolved' AND [System.State] <> 'Closed' AND [System.CreatedDate] < @Today - 30 ORDER BY [System.CreatedDate] ASC"
```

## Best Practices

1. **Always capture work item IDs**: Store in variables or files for later reference
2. **Use HTML formatting**: Makes descriptions readable in Azure DevOps UI
3. **Set area paths consistently**: Use team conventions
4. **Add tags early**: Easier to query later
5. **Link relationships promptly**: Two-step pattern (create then link)
6. **Query before bulk updates**: Preview results with `--output table` first
7. **Handle errors**: Check return codes and provide fallback logic
8. **Use environment variables**: Avoid hardcoding org/project URLs

## Troubleshooting

**Error: "TF401232: Work item type does not exist"**

- Check available types with `az boards work-item show --id <any-id>` and inspect type field
- Remember quotes for types with spaces: `--type "User Story"`

**Error: "TF401243: Area path does not exist"**

- List valid areas: `az boards area project list --org $ADO_ORG --project $ADO_PROJECT`
- Use correct format: `ProjectName\\TeamName\\SubArea` (double backslash in shell)

**Parent linking fails silently**

- Verify both work items exist
- Check if relationship already exists
- Ensure using correct relation type: `--relation-type parent`

**WIQL query returns no results**

- Test query in Azure DevOps UI query editor first
- Check field names (case-sensitive): use `System.Title` not `system.title`
- Verify work item type names match exactly
