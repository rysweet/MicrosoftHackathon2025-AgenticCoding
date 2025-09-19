# /workflow Command

Execute the default 13-step coding workflow for implementing features and fixes.

## Usage

```
/workflow start <task_description>
/workflow status
/workflow resume [workflow_id]
/workflow list
/workflow config [--edit]
```

## Commands

### /workflow start <task>

Start a new workflow with the given task description.

Options:

- `--auto`: Auto-proceed through all steps without confirmation
- `--skip-issue`: Skip GitHub issue creation
- `--skip-pr`: Skip pull request creation
- `--config <path>`: Use custom configuration file

Example:

```
/workflow start "Add user authentication to the API"
/workflow start "Fix bug in payment processing" --auto
```

### /workflow status

Show the status of the current active workflow.

Example:

```
/workflow status
```

Output:

```
Workflow: workflow_20240115_143022_abc123
Task: Add user authentication to the API
Status: IN_PROGRESS
Current Step: 5/13 - Simplify and Refactor
Completed: 4 steps
Time Elapsed: 5 minutes
```

### /workflow resume [workflow_id]

Resume a paused workflow. If no ID provided, resumes the most recent paused workflow.

Example:

```
/workflow resume
/workflow resume workflow_20240115_143022_abc123
```

### /workflow list

List all active and recently completed workflows.

Example:

```
/workflow list
```

### /workflow config [--edit]

Show or edit workflow configuration.

Options:

- `--edit`: Open configuration in editor
- `--reset`: Reset to default configuration
- `--validate`: Validate current configuration

Example:

```
/workflow config
/workflow config --edit
```

## Workflow Steps

The default workflow consists of 13 steps:

1. **Prompt Rewrite** - Clarify and structure requirements
2. **Create Issue** - Create GitHub issue for tracking
3. **Setup Worktree** - Create git worktree and branch
4. **Research & Plan** - Architecture and test planning
5. **Simplify & Refactor** - Apply ruthless simplicity
6. **Run Tests** - Execute tests and pre-commit hooks
7. **Commit & Push** - Create detailed commit and push
8. **Open PR** - Create pull request with issue link
9. **Review PR** - Automated code review
10. **Implement Feedback** - Address review comments
11. **Philosophy Check** - Ensure compliance with principles
12. **Ensure Mergeable** - Verify PR is ready to merge
13. **Notify Complete** - Send completion notification

## Configuration

The workflow is configured via YAML files:

### System Default

`.claude/workflow/config/default-workflow.yaml`

### User Customization

`~/.claude/workflow/custom.yaml`

### Project Override

`./.claude/workflow/project.yaml`

### Configuration Structure

```yaml
version: "1.0"
global_settings:
  auto_proceed: false
  error_handling: pause # pause | retry | fail
  philosophy_mode: strict # strict | relaxed

steps:
  - id: prompt_rewrite
    enabled: true
    config:
      agent: prompt-writer
      max_iterations: 2
```

## Pause and Resume

The workflow automatically saves state and can be paused/resumed:

- **Automatic Pause**: On errors when `error_handling: pause`
- **Manual Pause**: Press Ctrl+C during execution
- **Resume**: Use `/workflow resume` to continue

## Error Recovery

When a step fails:

1. **Pause Mode** (default): Workflow pauses, fix issue, then resume
2. **Retry Mode**: Automatically retry the failed step
3. **Fail Mode**: Stop workflow immediately

## Examples

### Basic Feature Implementation

```
/workflow start "Add pagination to the user list API endpoint"
```

This will:

1. Clarify requirements
2. Create GitHub issue
3. Setup worktree
4. Design and plan
5. Implement with TDD
6. Run tests
7. Create PR
8. Review and refine
9. Ensure mergeable

### Quick Bug Fix

```
/workflow start "Fix null pointer in checkout process" --auto --skip-issue
```

This will:

- Run automatically without prompts
- Skip issue creation
- Focus on fix and testing

### Custom Configuration

```
# First customize your workflow
/workflow config --edit

# Then run with custom settings
/workflow start "Implement new feature"
```

## Integration with Other Commands

The workflow integrates with other commands:

- `/analyze` - Can be run on workflow output
- `/improve` - Captures learnings from workflow
- `/ultrathink` - Can be used for complex workflow tasks

## Troubleshooting

### Workflow Stuck

```
/workflow status  # Check current state
/workflow resume  # Try to resume
```

### Reset Workflow

```
/workflow config --reset  # Reset configuration
/workflow list  # Find workflow ID
/workflow resume <id>  # Resume specific workflow
```

### View Logs

Workflow logs are stored in:
`.claude/runtime/workflow-state/active/<workflow_id>.json`

## Best Practices

1. **Clear Task Description**: Provide detailed requirements
2. **Review Configuration**: Customize for your project
3. **Monitor Progress**: Check status regularly
4. **Learn from Results**: Review completed workflows

## Philosophy Compliance

The workflow enforces:

- **Ruthless Simplicity**: Each step does one thing
- **Bricks & Studs**: Modular, composable steps
- **Zero-BS**: No placeholders, only working code
- **Regeneratable**: Can rebuild from specifications
