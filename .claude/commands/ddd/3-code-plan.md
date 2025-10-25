---
description: DDD Phase 3 - Plan code implementation (project:ddd)
argument-hint: [optional override instructions]
allowed-tools: TodoWrite, Read, Grep, Glob, Task
---

# DDD Phase 3: Code Planning

Ahoy! Time to chart the implementation course, matey! 🏴‍☠️

Loading context:

@docs/DDD_METHODOLOGY.md
@.claude/context/PHILOSOPHY.md
@ai_working/ddd/plan.md

**CRITICAL**: Read ALL updated documentation - these be now the specifications!

Override instructions: $ARGUMENTS

---

## Yer Task: Plan Complete Code Implementation

**Goal**: Assess current code, plan all changes to match new documentation

**Output**: `ai_working/ddd/code_plan.md` - Detailed implementation specification

---

## Phase 3 Steps

### 1. Read Updated Documentation (The Specifications)

**The docs ye updated in Phase 2 be now the SPEC**:

Read ALL documentation that describes what the code should do:
- User-facing docs (how it works)
- API documentation (interfaces)
- Configuration docs (settings)
- Architecture docs (design)

This be what the code MUST implement, arr!

### 2. Code Reconnaissance

For each code file in the plan (Phase 1):

**Understand current state**:
- Read the existin' code
- Understand current architecture
- Identify current behavior
- Note existing tests

**Gap analysis**:
- What does code do now?
- What should code do (per docs)?
- What's missin'?
- What needs to change?
- What needs to be removed?

Use Grep and Glob to explore related code, matey!

### 3. Create Implementation Specification

Write `ai_working/ddd/code_plan.md`:

```markdown
# Code Implementation Plan

Generated: [timestamp]
Based on: Phase 1 plan + Phase 2 documentation

## Summary

[High-level description of what needs to be implemented]

## Files to Change

### File: src/module1.py

**Current State**:
[What the code does now]

**Required Changes**:
[What needs to change to match documentation]

**Specific Modifications**:
- Add function `do_something()` - [description]
- Modify function `existing_func()` - [changes needed]
- Remove deprecated code - [what to remove]

**Dependencies**:
[Other files this depends on, if any]

**Agent Suggestion**: builder

---

[... repeat fer EVERY code file]

## Implementation Chunks

Break implementation into logical, testable chunks:

### Chunk 1: Core Interfaces / Data Models

**Files**: [list]
**Description**: [what this chunk does]
**Why first**: [usually: other chunks depend on these]
**Test strategy**: [how to verify]
**Dependencies**: None
**Commit point**: After unit tests pass

[... continue until all changes covered]

## New Files to Create

[If any new files needed]

## Files to Delete

[If any files should be removed]

## Agent Orchestration Strategy

**Primary Agents**:
- builder - Fer module implementation
- tester - Fer test creation
- reviewer - Fer code review

### Sequential vs Parallel

Use sequential fer this project: [reason]

## Testing Strategy

### Unit Tests to Add

[List unit tests needed]

### Integration Tests to Add

[List integration tests needed]

### User Testing Plan

How will we actually test as a user?

**Commands to run**:
```bash
# Test basic functionality
command --flag value
```

**Expected behavior**:
[What user should see]

## Philosophy Compliance

### Ruthless Simplicity

- [How this implementation stays simple]
- [What we're NOT doin' (YAGNI)]
- [Where we're removin' complexity]

### Modular Design

- [Clear module boundaries]
- [Well-defined interfaces (studs)]
- [Self-contained components (bricks)]

### Zero-BS Implementation

- No stubs or placeholders
- No TODOs in code
- No swallowed exceptions
- Complete features only

## Commit Strategy

Detailed commit plan:

**Commit 1**: [Chunk 1] - [description]

[... continue fer all commits]

## Success Criteria

Code be ready when:

- [ ] All documented behavior implemented
- [ ] All tests passin'
- [ ] User testing works as documented
- [ ] No regressions in existing functionality
- [ ] Code follows philosophy principles
- [ ] Ready fer Phase 4 implementation

## Next Steps

✅ Code plan complete and detailed
➡️ Get user approval
➡️ When approved, run: `/amplihack:ddd:4-code`
```

### 4. Verify Completeness

**Checklist before presentin' to user**:

- [ ] Every code file from Phase 1 plan covered?
- [ ] Clear what changes fer each file?
- [ ] Implementation broken into chunks?
- [ ] Dependencies between chunks identified?
- [ ] Test strategy defined?
- [ ] Agent orchestration planned?
- [ ] Commit strategy clear?
- [ ] Philosophy alignment verified?

### 5. Present for Approval

Show user:
- The code plan document
- Summary of changes
- Implementation approach

**Get explicit approval before proceedin' to Phase 4, arr!**

---

## Using TodoWrite

Track code plannin' tasks:

```markdown
- [ ] Read all updated documentation
- [ ] Reconnaissance of file 1 of N
- [ ] Reconnaissance of file 2 of N
...
- [ ] Implementation spec written
- [ ] Chunks defined
- [ ] Test strategy defined
- [ ] User approval obtained
```

---

## Important Notes

**Documentation be the spec**:
- Code MUST match what docs describe
- If docs are ambiguous, ask user to clarify docs first
- If implementin' reveals docs need changes, update docs first

**Right-sizing chunks**:
- Each chunk should fit in context window
- Each chunk should be independently testable
- Each chunk should have clear commit point

**DO NOT write code yet**:
- This phase be PLANNING only
- All actual implementation happens in Phase 4
- Get user approval on plan before codin', arr!

---

## When Plan is Approved

### Exit Message

```
✅ Phase 3 Complete: Code Plan Approved, Arr!

Implementation plan written to: ai_working/ddd/code_plan.md

Summary:
- Files to change: [count]
- Implementation chunks: [count]
- New tests: [count]
- Estimated commits: [count]

⚠️ USER APPROVAL REQUIRED

Please review the code plan above.

When approved, proceed to implementation:

    /amplihack:ddd:4-code

Phase 4 will implement the plan incrementally, with yer
authorization required fer each commit, matey!
```

---

**Ready to plan that code? Chart the course, arr! 🏴‍☠️**
