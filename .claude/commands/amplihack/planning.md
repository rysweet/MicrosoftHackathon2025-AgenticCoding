# Planning Command

## Usage
`/plan <task> [options]`

## Purpose
**Conversation efficiency optimization command** - Reduces session length by 60% through aggressive upfront planning and requirement gathering.

## How It Works

### Automatic Session Classification
The planning command automatically detects session type and complexity:

1. **Feature Development** (5-8 exchange target)
   - New functionality, system enhancements, feature additions
   - Applies comprehensive architecture-first planning

2. **Bug Fix** (4-6 exchange target)
   - Issue resolution, defect fixes, problem solving
   - Uses diagnostic-first approach with root cause analysis

3. **Analysis/Investigation** (3-5 exchange target)
   - Code review, performance analysis, research tasks
   - Structured investigation with clear deliverables

4. **Quick Clarification** (2-3 exchange target)
   - Questions, explanations, how-to guidance
   - Focused scope control with comprehensive responses

### Planning Process

1. **Session Type Detection**: Automatically classify based on task description
2. **Complexity Assessment**: Determine simple/medium/complex level
3. **Template Application**: Apply appropriate session efficiency template
4. **Requirement Gathering**: Front-load ALL clarification and planning
5. **Execution Structure**: Provide clear phases with completion markers

## Command Options

```bash
# Automatic detection (recommended)
/plan "Add authentication system"
/plan "Fix login bug causing timeouts"
/plan "Analyze performance bottlenecks"
/plan "Explain JWT token handling"

# Manual type specification
/plan "Add user dashboard" --type=feature
/plan "Database timeout errors" --type=bug_fix
/plan "Code architecture review" --type=analysis
/plan "How does caching work?" --type=clarification

# Complexity specification
/plan "Simple UI change" --complexity=simple
/plan "Multi-service integration" --complexity=complex

# Urgency specification
/plan "Production bug fix" --urgency=high
/plan "Feature enhancement" --urgency=normal
```

## Output Structure

Every planning session produces:

```
## Session Plan
**Type**: [Auto-detected or specified]
**Complexity**: [Simple/Medium/Complex]
**Target Exchanges**: [Specific number based on type]

## Complete Requirements
[All requirements gathered upfront - no gaps]

## Execution Plan
**Phase 1**: [Specific tasks with clear completion criteria]
**Phase 2**: [Next phase with dependencies identified]
**Phase 3**: [Final phase with success validation]
**Parallel Work**: [Tasks that can run simultaneously]

## Success Criteria
[Measurable completion markers]

## Context Preservation
[Information for future reference and handoff]
```

## Integration Points

### UltraThink Workflow
- Provides structured input for the 14-step workflow
- Pre-loads all requirement gathering and clarification
- Enables parallel agent execution planning

### TodoWrite Integration
- Automatically generates detailed todo lists from planning
- Creates clear task breakdown with completion criteria
- Enables progress tracking throughout execution

### Agent Orchestration
- Plans multi-agent coordination strategies
- Identifies parallel vs sequential agent usage
- Optimizes agent handoffs with context preservation

## Success Metrics

**Performance Targets**:
- **Session Length Reduction**: 35.5 exchanges → <15 exchanges (60% improvement)
- **First Exchange Information Capture**: >90% success rate
- **Context Re-explanation Incidents**: <10% of sessions
- **Requirement Clarification Cycles**: <2 per session

## When to Use

### Always Use For:
- **Non-trivial tasks** (estimated >30 minutes work)
- **Multi-step implementations** or investigations
- **Unclear or incomplete requirements**
- **Tasks involving multiple agents or systems**
- **When efficiency is particularly important**

### Automatic Triggers:
- Task mentions multiple components/systems
- Requirements contain ambiguous language
- Implementation involves multiple steps
- Cross-team or cross-system coordination needed

## Template Files

The planning command utilizes these session templates:

- `.claude/workflow/sessions/feature-development-template.md`
- `.claude/workflow/sessions/bug-fix-template.md`
- `.claude/workflow/sessions/quick-clarification-template.md`

## Philosophy Alignment

**Ruthless Simplicity**: Front-loads all complexity into planning phase
**Efficiency Focus**: Eliminates redundant clarification cycles
**Context Preservation**: Structured information transfer prevents re-explanation
**Parallel Optimization**: Identifies simultaneous work opportunities

Use `/plan` at the start of any non-trivial task to achieve maximum conversation efficiency.