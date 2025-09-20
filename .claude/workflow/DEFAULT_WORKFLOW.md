# Default Coding Workflow

This file defines the default workflow for all non-trivial code changes.
You can customize this workflow by editing this file.

## Integration with UltraThink

This workflow integrates with `/ultrathink` for deep analysis:

- Use `/ultrathink` at Step 1 for complex requirement analysis
- Use `/ultrathink` at Step 4 for complex architecture decisions
- UltraThink will follow these workflow steps when implementing solutions

## When This Workflow Applies

This workflow should be followed for:

- New features
- Bug fixes
- Refactoring
- Any non-trivial code changes

## The 13-Step Workflow

### Step 1: Rewrite and Clarify Requirements

- [ ] For complex tasks, use `/ultrathink` for deep analysis first
- [ ] Use the prompt-writer agent to clarify task requirements
- [ ] Remove ambiguity from the task description
- [ ] Define clear success criteria
- [ ] Document acceptance criteria

### Step 2: Create GitHub Issue

- [ ] Create issue using `gh issue create`
- [ ] Include clear problem description
- [ ] Define requirements and constraints
- [ ] Add success criteria
- [ ] Assign appropriate labels

### Step 3: Setup Worktree and Branch

- [ ] Create new git worktree for isolated development
- [ ] Create branch with format: `feat/issue-{number}-{brief-description}`
- [ ] Push branch to remote with tracking
- [ ] Switch to new worktree directory

### Step 4: Research and Design with TDD

- [ ] For complex architecture, use `/ultrathink` to orchestrate analysis
- [ ] Use architect agent to design solution architecture
- [ ] Document module specifications
- [ ] Use tester agent to write failing tests (TDD)
- [ ] Create detailed implementation plan
- [ ] Identify risks and dependencies

### Step 5: Implement the Solution

- [ ] Use builder agent to implement from specifications
- [ ] Follow the architecture design
- [ ] Make failing tests pass iteratively
- [ ] Ensure all requirements are met
- [ ] Add inline documentation

### Step 6: Refactor and Simplify

- [ ] Use cleanup agent for ruthless simplification
- [ ] Remove unnecessary abstractions
- [ ] Eliminate dead code
- [ ] Simplify complex logic
- [ ] Ensure single responsibility principle
- [ ] Verify no placeholders remain

### Step 7: Run Tests and Pre-commit Hooks

- [ ] Run all unit tests
- [ ] Execute `pre-commit run --all-files`
- [ ] Fix any linting issues
- [ ] Fix any formatting issues
- [ ] Resolve type checking errors
- [ ] Iterate until all checks pass

### Step 8: Commit and Push

- [ ] Stage all changes
- [ ] Write detailed commit message
- [ ] Reference issue number in commit
- [ ] Describe what changed and why
- [ ] Push to remote branch
- [ ] Verify push succeeded

### Step 9: Open Pull Request

- [ ] Create PR using `gh pr create`
- [ ] Link to the GitHub issue
- [ ] Write comprehensive description
- [ ] Include test plan
- [ ] Add screenshots if UI changes
- [ ] Request appropriate reviewers

### Step 10: Review the PR

- [ ] Use reviewer agent for code review
- [ ] Check code quality and standards
- [ ] Verify philosophy compliance
- [ ] Ensure adequate test coverage
- [ ] Post review comments on PR
- [ ] Identify potential improvements

### Step 11: Implement Review Feedback

- [ ] Review all feedback comments
- [ ] Use builder agent to implement changes
- [ ] Address each review comment
- [ ] Push updates to PR
- [ ] Respond to review comments
- [ ] Request re-review if needed

### Step 12: Philosophy Compliance Check

- [ ] Use reviewer agent for final check
- [ ] Verify ruthless simplicity achieved
- [ ] Confirm bricks & studs pattern followed
- [ ] Ensure zero-BS implementation (no stubs)
- [ ] Verify all tests passing
- [ ] Check documentation completeness

### Step 13: Ensure PR is Mergeable

- [ ] Check CI status (all checks passing)
- [ ] Use ci-diagnostic-workflow agent if CI fails
- [ ] Resolve any merge conflicts
- [ ] Verify all review comments addressed
- [ ] Confirm PR is approved
- [ ] Notify that PR is ready to merge

## Customization

To customize this workflow:

1. Edit this file to modify, add, or remove steps
2. Save your changes
3. The updated workflow will be used for future tasks

## Philosophy Notes

This workflow enforces our core principles:

- **Ruthless Simplicity**: Each step has one clear purpose
- **Test-Driven Development**: Write tests before implementation
- **Quality Gates**: Multiple review and validation steps
- **Documentation**: Clear commits and PR descriptions
