# Quick Start Guide

Get up and running with Azure DevOps CLI tools in 5 minutes.

## Prerequisites

1. **Python 3.8+**

   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Azure CLI**

   ```bash
   # macOS
   brew install azure-cli

   # Windows
   winget install Microsoft.AzureCLI

   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

3. **Azure DevOps Extension**
   ```bash
   az extension add --name azure-devops
   ```

## Step 1: Authentication

```bash
# Login to Azure
az login

# Configure default org and project (optional but recommended)
az devops configure --defaults \
  organization=https://dev.azure.com/YOUR_ORG \
  project=YOUR_PROJECT
```

## Step 2: Verify Setup

```bash
# Check authentication status
python -m .claude.scenarios.az-devops-tools.auth_check

# If issues, try auto-fix
python -m .claude.scenarios.az-devops-tools.auth_check --auto-fix
```

Expected output:

```
✓ Azure CLI installed
✓ Logged in
✓ DevOps extension installed
✓ Organization configured
✓ Project configured
✓ Organization accessible
✓ Project accessible

✓ Authentication is ready!
```

## Step 3: Your First Work Item

```bash
# Create a User Story
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type "User Story" \
  --title "My first story" \
  --description "# Description\n\nThis is my first work item!"
```

Output:

```
✓ Work item created successfully!
  ID: 1234
  URL: https://dev.azure.com/...
  Type: User Story
  Title: My first story
```

## Step 4: Query Work Items

```bash
# See your work items
python -m .claude.scenarios.az-devops-tools.query_wiql --query my-items
```

## Common Commands

### Check what work item types be available

```bash
python -m .claude.scenarios.az-devops-tools.list_types
```

### Create a Task linked to a Story

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --type Task \
  --title "Implement feature" \
  --parent 1234
```

### Convert markdown to HTML

```bash
echo "# Title\n\nParagraph" | \
  python -m .claude.scenarios.az-devops-tools.format_html
```

### Get unassigned work items

```bash
python -m .claude.scenarios.az-devops-tools.query_wiql --query unassigned
```

## Configuration Options

Set defaults to avoid repeating org/project:

**Option 1: az CLI configuration (recommended)**

```bash
az devops configure --defaults \
  organization=https://dev.azure.com/YOUR_ORG \
  project=YOUR_PROJECT
```

**Option 2: Environment variables**

```bash
export AZURE_DEVOPS_ORG_URL="https://dev.azure.com/YOUR_ORG"
export AZURE_DEVOPS_PROJECT="YOUR_PROJECT"
```

**Option 3: Command-line arguments**

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --org https://dev.azure.com/YOUR_ORG \
  --project YOUR_PROJECT \
  --type Task \
  --title "My task"
```

## Next Steps

- Read [Work Items Guide](work-items.md) fer detailed work item management
- Learn [WIQL Queries](queries.md) fer powerful searching
- See [HTML Formatting](html-formatting.md) fer rich descriptions
- Check [Troubleshooting](troubleshooting.md) if ye encounter issues

## Getting Help

Every tool has detailed help:

```bash
python -m .claude.scenarios.az-devops-tools.TOOL_NAME --help
```

Examples:

```bash
python -m .claude.scenarios.az-devops-tools.create_work_item --help
python -m .claude.scenarios.az-devops-tools.query_wiql --help
```

Arrr! Ye be ready to sail the Azure DevOps seas!
