# Feature Development Session Template

## Session Efficiency Target: 5-8 exchanges

This template optimizes feature development sessions by front-loading all requirement gathering and planning to minimize back-and-forth clarification.

## Pre-Session Checklist

Before starting implementation:

- [ ] Complete feature requirements gathered
- [ ] All constraints and dependencies identified
- [ ] Technical approach decided
- [ ] Success criteria clearly defined
- [ ] Testing strategy planned

## Exchange Flow Template

### Exchange 1: Comprehensive Requirement Gathering

**Goal**: Capture 90% of all necessary information in single exchange

```
I need to understand the complete context to plan this feature efficiently. Please provide:

**Feature Requirements:**
1. What specific functionality is needed? (detailed use cases)
2. What are the exact input/output requirements?
3. What edge cases should be handled?
4. Are there any specific UI/UX requirements?
5. What's explicitly out of scope for this feature?

**Technical Context:**
6. Which files/modules will likely be affected?
7. Are there existing patterns in the codebase to follow?
8. What external systems need integration?
9. Are there performance requirements?
10. What security considerations apply?

**Constraints & Preferences:**
11. Any specific technology choices required?
12. Timeline or deadline constraints?
13. Testing requirements or preferences?
14. Code style or architectural preferences?

**Acceptance Criteria:**
15. How will we know this feature is complete and successful?
16. Who needs to review or approve this?
17. What would constitute failure or need for rollback?
```

### Exchange 2: Implementation Plan Confirmation

**Goal**: Present complete implementation roadmap and get final approval

```
Based on your requirements, here's the complete implementation plan:

## Feature: [Name]

### Architecture Overview
- [High-level technical approach]
- [Key components and their interactions]
- [Integration points with existing system]

### Implementation Phases

**Phase 1: Foundation (Parallel)**
- Task A: [Details and deliverables]
- Task B: [Details and deliverables]
- Expected completion: [timeframe]

**Phase 2: Core Implementation (Sequential)**
- Task A: [Details and deliverables]
- Task B: [Details and deliverables]
- Expected completion: [timeframe]

**Phase 3: Integration & Testing (Parallel)**
- Task A: [Details and deliverables]
- Task B: [Details and deliverables]
- Expected completion: [timeframe]

### Success Validation
- [Testing approach]
- [Review checkpoints]
- [Acceptance criteria verification]

**Confirm**: Does this plan address all your requirements? Any adjustments needed?
```

### Exchange 3-5: Implementation Phases

**Goal**: Execute planned phases without backtracking or clarification

```
## Phase [N] Implementation

**Context Package** (no re-explanation needed):
- Requirements: [reference to Exchange 1]
- Constraints: [key limitations]
- Decisions made: [architectural choices and reasoning]

**Current Phase Work**:
[Execute planned work with clear deliverables]

**Progress Marker**: Phase [N] complete when [specific criteria met]
```

### Exchange 6: Testing and Validation

**Goal**: Comprehensive testing without requirement clarification

```
## Feature Testing & Validation

**Testing Against Requirements** (from Exchange 1):
- [Requirement 1]: [Test results]
- [Requirement 2]: [Test results]
- [Edge Case 1]: [Test results]

**Integration Testing**:
- [System integration verification]
- [Performance validation]
- [Security verification]

**Success Criteria Validation**:
- [Criterion 1]: ✓ Met / ⚠ Needs attention
- [Criterion 2]: ✓ Met / ⚠ Needs attention

**Ready for Review**: [Summary of deliverables]
```

### Exchange 7: Review and Finalization

**Goal**: Final review and any necessary adjustments

```
## Feature Review & Finalization

**Implementation Summary**:
- [What was built]
- [How it meets requirements]
- [Key technical decisions made]

**Review Findings**:
- [Any issues identified]
- [Recommended improvements]
- [Future considerations]

**Final Adjustments** (if needed):
[Minimal changes based on review]
```

### Exchange 8: Documentation and Cleanup

**Goal**: Complete session with full documentation

```
## Feature Documentation & Session Closure

**Feature Documentation**:
- [Usage guide]
- [Technical documentation]
- [Integration notes]

**Session Summary**:
- Original requirements: [reference]
- Final deliverables: [list]
- Decisions made: [key choices]
- Exchange count: [actual vs target]

**Session Complete**: Feature ready for production use
```

## Efficiency Optimization Techniques

### Information Capture Strategy

- **Batch Questions**: Ask all clarifying questions in Exchange 1
- **Context Packaging**: Structure information to prevent re-explanation
- **Decision Pre-Loading**: Make architectural decisions upfront
- **Scope Locking**: Fix requirements after Exchange 2

### Parallel Execution Opportunities

- Database schema + API design (Phase 1)
- Frontend + Backend implementation (Phase 2)
- Unit testing + Integration testing (Phase 3)
- Documentation + Code review (Final phase)

### Common Pitfalls to Avoid

- Starting implementation before complete requirements
- Asking follow-up questions that should have been covered in Exchange 1
- Changing scope or requirements mid-session
- Re-explaining context that should be referenced
- Sequential work that could be parallel

## Success Metrics

- **Exchange Count**: Target 5-8, Maximum 10
- **Requirement Changes**: Maximum 1 minor change after Exchange 2
- **Context Re-explanation**: 0 instances
- **Backtracking**: Maximum 1 instance for critical issues
- **Parallel Work**: Minimum 2 opportunities identified and utilized

## Session Adaptation

If session exceeds target exchanges:

### After Exchange 8 (Still Working)

- **Analyze**: What information was missing upfront?
- **Adapt**: Modify question set for future sessions
- **Continue**: Use structured approach to minimize additional exchanges

### Mid-Session Scope Change

- **Pause**: Document current progress
- **Re-plan**: Apply planning template to new requirements
- **Resume**: With updated context package

### Complexity Underestimation

- **Acknowledge**: Original estimate was insufficient
- **Restructure**: Break into additional phases
- **Communicate**: Updated timeline and approach

Remember: The goal is efficient completion, not rigid adherence to exchange count. Use this template as a guide while adapting to actual complexity and needs.
