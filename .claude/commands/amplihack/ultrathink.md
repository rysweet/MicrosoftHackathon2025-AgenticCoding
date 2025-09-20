# Ultra-Think Command

## Input Validation

@.claude/context/AGENT_INPUT_VALIDATION.md

## Usage

`/ultrathink <TASK_DESCRIPTION>`

## Purpose

Deep analysis mode for complex tasks. Orchestrates multiple agents to break down, analyze, and solve challenging problems.

## Integration with Default Workflow

UltraThink integrates seamlessly with the 13-step workflow in `.claude/workflow/DEFAULT_WORKFLOW.md`:

- Can be invoked from workflow Step 1 for requirement analysis
- Can be invoked from workflow Step 4 for architecture design
- When implementing, follows the workflow steps automatically
- Provides deep analysis that feeds into workflow execution

## Process

For non-trivial code changes, UltraThink follows the workflow:

### Phase 1: Deep Analysis (Workflow Steps 1 & 4)

- Use prompt-writer to clarify requirements (Step 1)
- Use architect agent to decompose the problem
- Design solution architecture (Step 4)
- Create specifications
- Use tester agent for TDD test design (Step 4)

### Phase 2: Implementation (Workflow Steps 5-8)

- Create GitHub issue if needed (Step 2)
- Setup worktree and branch (Step 3)
- Use builder agent to implement (Step 5)
- Use cleanup agent for simplification (Step 6)
- Run tests and pre-commit hooks (Step 7)
- Commit and push changes (Step 8)

### Phase 3: Review & Finalization (Workflow Steps 9-13)

- Open pull request (Step 9)
- Use reviewer agent for code review (Step 10)
- Implement feedback with builder agent (Step 11)
- Philosophy compliance check (Step 12)
- Ensure PR is mergeable (Step 13)

## Agent Orchestration

### When to Use Sequential

- Architecture → Implementation → Review
- Each step depends on previous
- Building progressive context

### When to Use Parallel

- Multiple independent analyses
- Different perspectives needed
- Gathering diverse solutions

## When to Use UltraThink

### Use UltraThink When:

- Task complexity requires deep multi-agent analysis
- Architecture decisions need careful decomposition
- Requirements are vague and need exploration
- Multiple solution paths need evaluation
- Cross-cutting concerns need coordination

### Follow Workflow Directly When:

- Requirements are clear and straightforward
- Solution approach is well-defined
- Standard implementation patterns apply
- Single agent can handle the task

## Task Management

Always use TodoWrite to:

- Break down complex tasks
- Track progress
- Coordinate agents
- Document decisions
- Track workflow checklist completion

## Example Flow

```
1. Deep analysis with architect & tester (Workflow Steps 1 & 4)
2. Create issue and branch (Workflow Steps 2-3)
3. Build with builder agent (Workflow Step 5)
4. Simplify with cleanup agent (Workflow Step 6)
5. Test and commit (Workflow Steps 7-8)
6. PR and review cycle (Workflow Steps 9-13)
```

The workflow ensures consistent, high-quality implementation while UltraThink provides the deep analysis needed for complex tasks.

Remember: Ultra-thinking means thorough analysis before action.
