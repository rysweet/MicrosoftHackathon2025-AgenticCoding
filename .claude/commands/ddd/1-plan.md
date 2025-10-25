---
description: DDD Phase 1 - Planning and design (project:ddd)
argument-hint: [feature description or leave empty to use existing plan]
allowed-tools: TodoWrite, Read, Grep, Glob, Task
---

# DDD Phase 1: Planning & Design

Ahoy matey! Time to chart the course before settin' sail! 🏴‍☠️

Loading context:

@docs/DDD_METHODOLOGY.md
@docs/DDD_CONTEXT_POISONING.md
@.claude/context/PHILOSOPHY.md

Feature: $ARGUMENTS

---

## Yer Task: Create Complete Implementation Plan

**Goal**: Design and plan the feature before touchin' ANY files, arr!

**Output**: `ai_working/ddd/plan.md` - Complete specification fer all subsequent phases

---

## Phase 1 Steps

### 1. Problem Framing

Answer these questions, matey:
- What are we buildin'?
- Why does it matter?
- What be the user value?
- What problem does this solve?

### 2. Reconnaissance

Explore the codebase:
- Use Glob to find relevant files
- Use Grep to search fer related code
- Understand current architecture
- Identify patterns to follow
- Find files that will be affected

**Document**: Current state, related code, architecture context

### 3. Design Proposals

Develop the approach:
- Propose initial design
- Consider alternatives (at least 2)
- Analyze trade-offs
- Check against philosophy:
  - Ruthless Simplicity? ✓
  - Modular Design? ✓
  - Clear interfaces? ✓
  - Zero-BS? ✓
- Iterate with user on decisions

**Get user feedback on design direction before proceedin'!**

### 4. Create Detailed Plan

Write `ai_working/ddd/plan.md` with this structure:

```markdown
# DDD Plan: [Feature Name]

## Problem Statement

[What we're solvin' and why - clear user value]

## Proposed Solution

[How we'll solve it - high level approach]

## Alternatives Considered

[Other approaches we evaluated and why we chose this one]

## Architecture & Design

### Key Interfaces

[Define the "studs" - how modules connect]

### Module Boundaries

[What goes where, clear separation of concerns]

### Data Models

[Key data structures, if applicable]

## Files to Change

### Non-Code Files (Phase 2)

- [ ] docs/file1.md - [what needs updatin']
- [ ] README.md - [what needs updatin']
      [... complete list of ALL non-code files]

### Code Files (Phase 4)

- [ ] src/module1.py - [what needs changin']
- [ ] src/module2.py - [what needs changin']
      [... complete list of ALL code files]

## Philosophy Alignment

### Ruthless Simplicity

- Start minimal: [how]
- Avoid future-proofin': [what we're NOT buildin']
- Clear over clever: [examples]

### Modular Design

- Bricks (modules): [list self-contained pieces]
- Studs (interfaces): [list connection points]
- Regeneratable: [could rebuild from this spec]

### Zero-BS Implementation

- No stubs or placeholders
- No TODOs in code
- No swallowed exceptions
- Complete features only

## Test Strategy

### Unit Tests

[What unit tests we'll need]

### Integration Tests

[What integration tests we'll need]

### User Testing

[How we'll actually test as a user]

## Implementation Approach

### Phase 2 (Docs)

[Specific docs to update, what to document]

### Phase 4 (Code)

[Chunks to implement, order matters if dependencies]

## Success Criteria

[How do we know it's done and workin'?]

## Next Steps

✅ Plan complete and approved
➡️ Ready fer `/amplihack:ddd:2-docs`
```

---

## Using TodoWrite

Track plannin' tasks:

```markdown
- [ ] Problem framin' complete
- [ ] Reconnaissance done
- [ ] Design proposals drafted
- [ ] User feedback incorporated
- [ ] Detailed plan written
- [ ] Philosophy alignment checked
- [ ] Plan reviewed with user
```

---

## Agent Suggestions

Consider spawnin' agents fer help:

**architect** - For complex architectural decisions
**reviewer** - To review the plan fer issues
**Explore agent** - For codebase reconnaissance

---

## Important Notes

**DO NOT write any files yet** - This phase be PLANNING ONLY!

**Iterate until solid**:
- Get user feedback on design direction
- Refine proposals based on feedback
- Clarify ambiguities
- Ensure shared understandin'

**Philosophy check**:
- Does this follow ruthless simplicity?
- Are module boundaries clear?
- Can we build in increments?
- Is this the simplest approach that works?

---

## When Planning is Approved

### Exit Message

```
✅ Phase 1 Complete: Planning Approved, Arr!

Plan written to: ai_working/ddd/plan.md

Next Phase: Update all non-code files (docs, configs, READMEs)

Run: /amplihack:ddd:2-docs

The plan will guide all subsequent phases, matey!
```

---

**Ready to set sail? Create that plan, arr! 🏴‍☠️**
