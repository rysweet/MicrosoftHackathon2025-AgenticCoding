# Diagnostic Workflow Migration Guide

## Overview

We've reorganized our diagnostic agents from technical capabilities to developer workflow stages that match how developers actually work.

## Migration Summary

### Old Structure (Technical Capabilities)

- `ci-diagnostics.md` - Environment comparison
- `silent-failure-detector.md` - Hidden failure detection
- `pattern-matcher.md` - Historical pattern matching

### New Structure (Developer Workflow)

#### Primary Workflow Agents

1. **`pre-commit-diagnostic.md`** - Stage 1: Fix locally before push
2. **`ci-diagnostic-workflow.md`** - Stage 2: Fix CI after push

#### Supporting Utility Agents (unchanged)

- `ci-diagnostics.md` - Still used for environment comparison
- `silent-failure-detector.md` - Still used for hidden failures
- `pattern-matcher.md` - Still used for pattern matching

## Key Changes

### 1. Workflow-Based Activation

**Before:** Choose agent based on technical problem

```
"CI is failing" → ci-diagnostics
"Hooks not working" → silent-failure-detector
"Seen this before?" → pattern-matcher
```

**After:** Choose agent based on development stage

```
"Can't commit" → pre-commit-diagnostic
"CI failing on PR" → ci-diagnostic-workflow
```

### 2. Orchestration Pattern

The new workflow agents orchestrate the existing utility agents:

```markdown
pre-commit-diagnostic
├── Handles all pre-commit issues
├── Calls silent-failure-detector if needed
└── Calls pattern-matcher for recurring issues

ci-diagnostic-workflow
├── Monitors CI with check_ci_status tool
├── Calls ci-diagnostics for environment issues
├── Calls pattern-matcher for known failures
└── Iterates until mergeable
```

### 3. Clear Progression

**Developer Workflow:**

1. Write code
2. Try to commit → If fails: `pre-commit-diagnostic`
3. Push to repository
4. CI runs → If fails: `ci-diagnostic-workflow`
5. PR becomes mergeable (but not auto-merged)
6. User reviews and merges

## Usage Examples

### Scenario 1: Pre-commit Failures

**Old Way:**

```python
# Manual diagnosis
bash("pre-commit run --all-files")
# Figure out which agent to use
Task("silent-failure-detector", "Check why hooks aren't working")
# Maybe also need
Task("pattern-matcher", "Find similar issues")
```

**New Way:**

```python
# Single workflow agent handles everything
Task("pre-commit-diagnostic", "Fix all pre-commit issues")
# It automatically orchestrates other agents as needed
```

### Scenario 2: CI Failures

**Old Way:**

```python
# Check CI manually
check_ci_status()
# Deploy multiple agents
Task("ci-diagnostics", "Compare environments")
Task("pattern-matcher", "Search for similar failures")
# Fix and push manually
# Check CI again manually
```

**New Way:**

```python
# Single workflow manages entire cycle
Task("ci-diagnostic-workflow", "Fix CI and iterate until mergeable")
# It handles the full loop: check → diagnose → fix → push → repeat
```

## Integration Points

### When to Use Each Agent

| Situation               | Use This Agent           | It Will                            |
| ----------------------- | ------------------------ | ---------------------------------- |
| Pre-commit hooks fail   | `pre-commit-diagnostic`  | Fix all issues before commit       |
| Can't commit code       | `pre-commit-diagnostic`  | Resolve blockers, make committable |
| CI failing after push   | `ci-diagnostic-workflow` | Iterate fixes until mergeable      |
| Need to check CI status | `ci-diagnostic-workflow` | Monitor and report status          |
| Want PR mergeable       | `ci-diagnostic-workflow` | Fix all CI issues (won't merge)    |

### Utility Agents (Still Available)

These are now primarily called BY the workflow agents, but can still be used directly for specific needs:

| Agent                     | Direct Use Case                     |
| ------------------------- | ----------------------------------- |
| `ci-diagnostics`          | Quick environment version check     |
| `silent-failure-detector` | Investigate specific silent failure |
| `pattern-matcher`         | Search for historical solutions     |

## Benefits of New Structure

1. **Matches Developer Mental Model**: Stages match actual workflow
2. **Clearer Delegation**: Know exactly which agent to use when
3. **Better Orchestration**: Workflow agents coordinate utilities
4. **Complete Automation**: Full fix cycles, not just diagnosis
5. **Prevents Premature Push**: Fix locally first philosophy

## Backward Compatibility

All existing utility agents still work independently if needed. The new workflow agents simply provide better orchestration on top.

## Quick Reference Card

```
BEFORE COMMIT/PUSH → pre-commit-diagnostic
AFTER PUSH, CI FAILING → ci-diagnostic-workflow

That's it! These two agents handle 95% of diagnostic needs.
```

## Migration Checklist

- [ ] Update any scripts using old delegation patterns
- [ ] Train on new workflow: local first, then CI
- [ ] Use workflow agents as primary entry points
- [ ] Let workflow agents orchestrate utilities
- [ ] Remember: Never auto-merge, stop at mergeable
