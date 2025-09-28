# Session Efficiency Templates

This directory contains optimized session templates designed to reduce conversation length from an average of 35.5 exchanges to <15 exchanges through aggressive upfront planning.

## Templates Available

### 1. Feature Development Template (`feature-development-template.md`)

**Target**: 5-8 exchanges
**Use for**: New feature implementation, significant functionality additions
**Strategy**: Architecture-first planning with comprehensive upfront requirements

### 2. Bug Fix Template (`bug-fix-template.md`)

**Target**: 4-6 exchanges
**Use for**: Issue resolution, debugging, problem diagnosis
**Strategy**: Diagnostic-first approach with complete context gathering

### 3. Quick Clarification Template (`quick-clarification-template.md`)

**Target**: 2-3 exchanges
**Use for**: Simple questions, minor changes, documentation updates
**Strategy**: Scope control with focused boundaries

## Usage

These templates are automatically applied when using the `/plan` command:

```bash
# Automatically selects appropriate template
/plan "Add authentication system" --type=feature
/plan "Fix login timeout issue" --type=bug_fix
/plan "Explain JWT token handling" --type=clarification
```

## Template Structure

Each template follows the same efficiency optimization principles:

1. **Exchange 1**: Comprehensive information gathering (90% of context)
2. **Exchange 2**: Implementation plan confirmation and final clarifications
3. **Exchanges 3-N**: Structured execution without backtracking
4. **Final Exchange**: Documentation and clean closure

## Success Metrics

Templates are optimized for:

- **Conversation Length**: Target reductions of 60% from baseline
- **Context Capture**: 90% of necessary information in first exchange
- **Backtracking Prevention**: <1 instance of requirement re-clarification
- **Parallel Execution**: Multiple opportunities identified per session

## Integration

Templates integrate with:

- **Planning Agent**: Automatically selects and applies appropriate template
- **Workflow System**: Works with existing DEFAULT_WORKFLOW.md processes
- **Agent Delegation**: Coordinates with specialized agents for parallel execution

## Customization

To create organization-specific templates:

1. Copy existing template as starting point
2. Modify question sets for domain-specific needs
3. Adjust exchange targets based on complexity patterns
4. Update planning agent to recognize new template triggers

Templates are designed to be living documents that improve based on actual usage patterns and feedback.
