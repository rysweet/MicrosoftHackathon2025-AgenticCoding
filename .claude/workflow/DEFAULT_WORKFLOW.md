# Default Coding Workflow

This file defines the default workflow for all non-trivial code changes.
You can customize this workflow by editing this file.

## When This Workflow Applies

This workflow should be followed for:

- New features
- Bug fixes
- Refactoring
- Any non-trivial code changes

## The 13-Step Workflow

### Step 1: Rewrite and Clarify Requirements

Use the prompt-writer agent to clarify the task requirements, remove ambiguity, and define clear success criteria.

### Step 2: Create GitHub Issue

Create a GitHub issue using `gh issue create` with a clear description, requirements, and success criteria.

### Step 3: Setup Worktree and Branch

Create a new git worktree and branch for the issue:

- Branch name format: `feat/issue-{number}-{brief-description}`
- Use worktrees to keep work isolated

### Step 4: Research and Design with TDD

1. Use the architect agent to design the solution architecture
2. Use the tester agent to write failing tests first (TDD approach)
3. Create an implementation plan

### Step 5: Implement the Solution

Use the builder agent to implement based on:

- The architecture design
- The failing tests
- The clarified requirements
  Make tests pass iteratively.

### Step 6: Refactor and Simplify

Use the cleanup agent to apply ruthless simplicity:

- Remove unnecessary abstractions
- Eliminate dead code
- Simplify complex logic
- Ensure single responsibility

### Step 7: Run Tests and Pre-commit Hooks

Run all tests, linters, and pre-commit hooks:

- Execute `pre-commit run --all-files`
- Fix any issues found
- Iterate until all checks pass

### Step 8: Commit and Push

Create a detailed commit message:

- Reference the issue number
- Describe what changed and why
- Push to the remote branch

### Step 9: Open Pull Request

Create a PR using `gh pr create`:

- Link to the issue
- Include comprehensive description
- Provide test plan

### Step 10: Review the PR

Use the reviewer agent to:

- Check code quality
- Verify philosophy compliance
- Ensure adequate test coverage
- Post review comments

### Step 11: Implement Review Feedback

Use the builder agent to:

- Address all review comments
- Make necessary changes
- Push updates

### Step 12: Philosophy Compliance Check

Final check using the reviewer agent:

- Ruthless simplicity achieved?
- Bricks & studs pattern followed?
- Zero-BS implementation?
- All tests passing?

### Step 13: Ensure PR is Mergeable

Use the ci-diagnostic-workflow agent if needed to:

- Ensure CI is passing
- Resolve any merge conflicts
- Verify all review comments addressed
- Confirm PR is ready to merge

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
