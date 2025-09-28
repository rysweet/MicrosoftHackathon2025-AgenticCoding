---
name: /plan
description: Conversation efficiency optimization command for upfront planning and requirement gathering
version: 1.0
---

# Planning Command (/plan)

## Purpose

The `/plan` command activates conversation efficiency optimization by engaging the planning agent to front-load requirement gathering and task decomposition, reducing session length by an average of 60%.

## Syntax

```
/plan <task_description> [options]
```

### Parameters

- `task_description` (required): Brief description of the task or question
- `--type` (optional): Session type [feature|bug_fix|analysis|optimization|clarification]
- `--urgency` (optional): Priority level [low|medium|high|critical]
- `--complexity` (optional): Expected complexity [simple|medium|complex]

### Examples

```bash
# Feature development
/plan "Add dark mode toggle to settings page" --type=feature

# Bug investigation
/plan "Users losing data during concurrent edits" --type=bug_fix --urgency=high

# Code analysis
/plan "Analyze authentication system for security issues" --type=analysis

# Quick clarification
/plan "Explain how JWT tokens are handled" --type=clarification

# Auto-detect type (most common)
/plan "Optimize database queries in user service"
```

## How It Works

### 1. Automatic Session Classification

The planning agent analyzes the task description and automatically:

- Identifies session type (feature, bug_fix, analysis, etc.)
- Selects appropriate efficiency template
- Estimates complexity and target exchange count
- Prepares comprehensive question sets

### 2. Template-Based Planning

Based on session type, applies optimized templates:

- **Feature Development**: 5-8 exchange target with comprehensive requirement gathering
- **Bug Fix**: 4-6 exchange target with diagnostic-first approach
- **Analysis**: 3-5 exchange target with scope-first boundaries
- **Clarification**: 2-3 exchange target with focus control

### 3. Efficiency Optimization

Automatically implements:

- Batch question strategies to minimize back-and-forth
- Context preservation frameworks to prevent re-explanation
- Parallel execution planning where possible
- Clear success criteria and completion markers

## Usage Patterns

### When to Use /plan

**Always use for:**

- Any non-trivial task (>30 minutes estimated work)
- Tasks requiring multiple steps or phases
- When requirements aren't completely clear
- Complex debugging or analysis work
- Feature development or significant changes

**Consider using for:**

- Questions that might expand into larger discussions
- Tasks where scope could be unclear
- When efficiency is particularly important

**Don't use for:**

- Extremely simple, single-step tasks
- Tasks with completely clear, unambiguous requirements
- Follow-up questions in existing well-structured sessions

### Integration with Workflow

The planning command integrates with the default workflow:

```
User request → /plan → Planning agent engagement → Template selection →
Comprehensive requirement gathering → Structured execution → Efficient completion
```

This replaces the typical:

```
User request → Clarification → More clarification → Implementation →
More questions → Fixes → Additional clarification → Completion
```

## Command Processing

### Step 1: Task Analysis

```yaml
Input: "/plan Add authentication system --type=feature"
Processing:
  - task: "Add authentication system"
  - type: "feature" (explicit)
  - urgency: "medium" (default)
  - complexity: "unknown" (default)
```

### Step 2: Planning Agent Engagement

```yaml
Agent_Call:
  agent: planning-agent
  context:
    task_description: "Add authentication system"
    session_type: "feature"
    urgency: "medium"
    complexity_hint: "unknown"
```

### Step 3: Template Selection and Execution

```yaml
Template: feature-development-template.md
Strategy: architecture-first-planning
Target_Exchanges: 5-8
Approach: comprehensive-upfront-gathering
```

## Output Format

The planning command produces:

### Initial Planning Response

```markdown
## Session Plan: [Task Title]

**Session Type**: [Detected/specified type]
**Efficiency Strategy**: [Template-based approach]
**Target Exchanges**: [Number based on complexity]
**Template Applied**: [Specific template used]

### Comprehensive Information Request

[Template-specific question set designed to capture 90% of
necessary information in single exchange]

### Execution Roadmap

**Phase 1**: [Steps and expected outcomes]
**Phase 2**: [Steps and expected outcomes]
**Phase 3**: [Steps and expected outcomes]
**Parallel Opportunities**: [Tasks that can run simultaneously]

### Success Metrics

- **Exchange Target**: [Number]
- **Completion Criteria**: [How to know we're done]
- **Quality Gates**: [Validation checkpoints]
```

## Advanced Features

### Complexity Detection

The planning agent automatically assesses complexity based on:

- Keywords in task description (authentication, optimization, migration, etc.)
- Number of implied components or systems
- Presence of integration requirements
- Security or performance implications

### Context Preservation

Creates structured context packages to prevent re-explanation:

- Decision records with reasoning
- Constraint documentation
- Progress markers and completion criteria
- Quick reference information

### Parallel Execution Planning

Identifies opportunities for parallel work:

- Independent components that can be developed simultaneously
- Testing that can run parallel to implementation
- Documentation that can be created alongside development

## Configuration Options

### Session Templates

Customize templates in `.claude/workflow/sessions/`:

- `feature-development-template.md`
- `bug-fix-template.md`
- `quick-clarification-template.md`
- Custom templates for organization-specific patterns

### Planning Agent Tuning

Modify `.claude/agents/amplihack/specialized/planning-agent.md`:

- Adjust question sets for your domain
- Customize complexity assessment criteria
- Modify efficiency targets
- Add organization-specific constraints

## Success Metrics and Monitoring

### Efficiency Tracking

The planning command tracks:

- Average session length before/after planning
- Requirement clarification cycles reduced
- Context re-explanation instances
- First-exchange information capture rate

### Quality Metrics

Monitors:

- Session completion without backtracking
- User satisfaction with planning thoroughness
- Accuracy of complexity assessments
- Template effectiveness by session type

## Integration Examples

### With UltraThink

```bash
# Use planning as part of comprehensive workflow
/plan "Implement user roles system" --type=feature
# Then continue with workflow execution using planned approach
```

### With Specialized Agents

```bash
# Planning identifies need for architect review
/plan "Redesign microservice communication" --type=refactoring
# Automatically engages architect agent based on complexity
```

### With CI/CD Workflow

```bash
# Planning includes testing and deployment considerations
/plan "Add new API endpoint with auth" --type=feature
# Includes pre-commit, CI, and deployment planning
```

## Troubleshooting

### Common Issues

**Session Still Too Long**

- Review question comprehensiveness in Exchange 1
- Check if scope creep occurred mid-session
- Validate template selection was appropriate
- Consider breaking complex tasks into multiple planned sessions

**Planning Overhead Too High**

- Use for appropriate complexity level tasks
- Ensure task description is specific enough
- Consider using quick-clarification template for simple tasks

**Template Doesn't Fit**

- Create custom template for repeated patterns
- Modify existing template parameters
- Provide more specific session type hints

## Best Practices

### For Maximum Efficiency

1. **Be Specific**: Provide clear task descriptions to enable better planning
2. **Trust the Process**: Follow the planned approach rather than ad-hoc changes
3. **Batch Information**: Provide all requested context in comprehensive responses
4. **Respect Boundaries**: Keep scope within planned limits

### For Quality Results

1. **Complete Planning**: Don't skip the comprehensive information gathering
2. **Context Preservation**: Reference established decisions rather than re-explaining
3. **Progress Markers**: Use defined completion criteria for each phase
4. **Quality Gates**: Validate success criteria before moving to next phase

Remember: The goal is to front-load all the thinking and planning to eliminate mid-session confusion and backtracking. Trust the process and provide comprehensive information upfront for maximum efficiency.
