# Troubleshooting Guide

Common issues and solutions fer Azure DevOps CLI tools.

## Authentication Issues

### "az: command not found"

**Problem**: Azure CLI not installed or not in PATH.

**Solution**:

```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify
az --version
```

### "ERROR: az devops: 'devops' is not in the 'az' command group"

**Problem**: Azure DevOps extension not installed.

**Solution**:

```bash
az extension add --name azure-devops
```

### "Please run 'az login' to setup account"

**Problem**: Not logged in to Azure.

**Solution**:

```bash
az login
```

### "Authentication failed"

**Problem**: Token expired or insufficient permissions.

**Solution**:

```bash
# Re-login
az logout
az login

# Verify permissions in Azure DevOps web portal
```

## Configuration Issues

### "Organization and project are required"

**Problem**: Missing org/project configuration.

**Solution**:

```bash
# Option 1: Set defaults
az devops configure --defaults \
  organization=https://dev.azure.com/YOUR_ORG \
  project=YOUR_PROJECT

# Option 2: Use command-line args
python -m .claude.scenarios.az-devops-tools.create_work_item \
  --org https://dev.azure.com/YOUR_ORG \
  --project YOUR_PROJECT \
  --type Task \
  --title "My task"

# Option 3: Environment variables
export AZURE_DEVOPS_ORG_URL="https://dev.azure.com/YOUR_ORG"
export AZURE_DEVOPS_PROJECT="YOUR_PROJECT"
```

### "TF401019: The Git repository with name or identifier does not exist"

**Problem**: Wrong organization or project name.

**Solution**:

- Verify org URL format: `https://dev.azure.com/ORG_NAME`
- Check project name (case-sensitive)
- Verify access in Azure DevOps web portal

## Work Item Issues

### "Invalid work item type: 'X'"

**Problem**: Work item type doesn't exist in project.

**Solution**:

```bash
# List available types
python -m .claude.scenarios.az-devops-tools.list_types

# Use exact type name (case-sensitive)
--type "User Story"  # Correct
--type user story    # Wrong
```

### "Work item X does not exist"

**Problem**: Referenced work item ID doesn't exist.

**Solution**:

- Verify work item ID
- Check project scope
- Query fer valid IDs:
  ```bash
  python -m .claude.scenarios.az-devops-tools.query_wiql --query recent
  ```

### "Failed to create link"

**Problem**: Parent link failed.

**Solution**:

- Verify both work items exist
- Check relationship be valid:
  - Task → Story, Bug, Feature, Epic
  - Story → Feature, Epic
  - Feature → Epic
- Use link_parent separately if needed:
  ```bash
  python -m .claude.scenarios.az-devops-tools.link_parent \
    --child CHILD_ID \
    --parent PARENT_ID
  ```

## Query Issues

### "Failed to execute query"

**Problem**: Invalid WIQL syntax.

**Solution**:

- Test query in Azure DevOps web UI first
- Check field names be correct: `[System.Title]`
- Verify operators: `=`, `<>`, `<`, `>`, etc.
- Check quotes: Use single quotes in WIQL strings

### "No work items found"

**Problem**: Query returned no results.

**Solution**:

- Verify query conditions
- Check work items exist in project
- Use broader query:
  ```bash
  python -m .claude.scenarios.az-devops-tools.query_wiql \
    --wiql "SELECT [System.Id] FROM workitems"
  ```

## Python Issues

### "ModuleNotFoundError: No module named 'claude'"

**Problem**: Wrong import path or module not found.

**Solution**:

```bash
# Run tools via -m flag from project root
python -m .claude.scenarios.az-devops-tools.TOOL_NAME

# Or import with correct path
from .claude.scenarios.az_devops_tools.TOOL_NAME import function
```

### "SyntaxError: invalid syntax"

**Problem**: Python version too old.

**Solution**:

```bash
# Check version (need 3.8+)
python --version

# Use correct Python
python3 -m .claude.scenarios.az-devops-tools.TOOL_NAME
```

## Network Issues

### "Timeout accessing organization"

**Problem**: Network connectivity or firewall.

**Solution**:

- Check internet connection
- Verify access to dev.azure.com
- Check corporate firewall/proxy
- Try with VPN if required

### "Connection refused"

**Problem**: Azure DevOps service down or network issue.

**Solution**:

- Check Azure DevOps status: https://status.dev.azure.com/
- Verify network connectivity
- Try again later

## Performance Issues

### "Command taking too long"

**Problem**: Large result sets or slow network.

**Solution**:

```bash
# Limit query results
python -m .claude.scenarios.az-devops-tools.query_wiql \
  --query my-items \
  --limit 10

# Increase timeout (if supported)
# Check tool documentation
```

## Getting More Help

### Enable Verbose Output

Most tools have `--help`:

```bash
python -m .claude.scenarios.az-devops-tools.TOOL_NAME --help
```

### Check Azure CLI Logs

```bash
# Azure CLI debug mode
az devops work-item show --id 1 --debug
```

### Verify Tool Installation

```bash
# Check auth status
python -m .claude.scenarios.az-devops-tools.auth_check

# Auto-fix common issues
python -m .claude.scenarios.az-devops-tools.auth_check --auto-fix
```

### Test with Azure CLI Directly

```bash
# Test basic connectivity
az boards work-item show \
  --id 1 \
  --org https://dev.azure.com/YOUR_ORG \
  --project YOUR_PROJECT
```

## Common Error Codes

- **Exit code 0**: Success
- **Exit code 1**: Authentication error
- **Exit code 2**: Configuration error
- **Exit code 3**: Command execution error
- **Exit code 4**: Validation error

## Still Having Issues?

1. Check [Authentication Guide](authentication.md)
2. Review [Work Items Guide](work-items.md)
3. Read [Quick Start](quick-start.md)
4. Check Azure DevOps status
5. Review Azure CLI documentation

## See Also

- [Authentication Setup](authentication.md)
- [Quick Start Guide](quick-start.md)
- [Azure DevOps CLI Docs](https://learn.microsoft.com/en-us/cli/azure/devops)
