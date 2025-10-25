---
description: DDD Phase 4 - Implement and verify code (project:ddd)
argument-hint: [optional feedback or instructions]
allowed-tools: TodoWrite, Read, Write, Edit, Grep, Glob, Task, Bash(*)
---

# DDD Phase 4: Implementation & Verification

Ahoy! Time to write the code and test it like a real user, arr! 🏴‍☠️

Loading context:

@docs/DDD_METHODOLOGY.md
@ai_working/ddd/code_plan.md

**CRITICAL**: Read ALL updated documentation - code must match exactly, matey!

User feedback/instructions: $ARGUMENTS

---

## Yer Task: Implement Code & Test as User

**Goal**: Write code matchin' docs exactly, test as real user would, iterate until workin'

**This phase stays active until user confirms "all workin'" - iterate as long as needed**

---

## Phase 4A: Implementation

### For Each Chunk in Code Plan

#### Step 1: Load Full Context

Before implementin' chunk:
- Read the code plan fer this chunk
- Read ALL relevant documentation (the specs)
- Read current code in affected files
- Understand dependencies

**Context be critical** - don't rush this step, arr!

#### Step 2: Implement Exactly as Documented

**Code MUST match documentation**:
- If docs say "function returns X", code returns X
- If docs show config format, code parses that format
- If docs describe behavior, code implements that behavior
- Examples in docs must actually work

**If conflict arises**:

```
STOP ✋

Don't guess or make assumptions, matey.

Ask user:
"Documentation says X, but implementin' Y seems better because Z.
Should I:
a) Update docs to match Y
b) Implement X as documented
c) Something else?"
```

#### Step 3: Verify Chunk Works

After implementin' chunk:
- Run relevant tests
- Check fer syntax errors
- Basic smoke test
- Ensure no regressions

#### Step 4: Show Changes & Get Commit Authorization

**IMPORTANT**: Each commit requires EXPLICIT user authorization, arr!

Show user:

```markdown
## Chunk [N] Complete: [Description]

### Files Changed

[list with brief description of changes]

### What This Does

[plain English explanation]

### Tests

[which tests pass]

### Diff Summary

git diff --stat

### Proposed Commit

feat: [Chunk description]

[Detailed commit message based on code plan]

⚠️ **Request explicit authorization**:
"Ready to commit? (yes/no/show me diff first)"

If yes: commit with message
If no: ask what needs changin'
If show diff: run `git diff` then ask again
```

#### Step 5: Move to Next Chunk

After successful commit, move to next chunk in plan.

Repeat Steps 1-4 fer all chunks, arr!

---

## Phase 4B: Testing as User Would

**After all implementation chunks complete**:

### Step 1: Actual User Testing

**Be the QA entity** - actually use the feature:

```bash
# Run the actual commands a user would run
amplihack run --with-new-feature

# Try the examples from documentation (they should work)
[copy exact examples from docs]

# Test error handlin'
[try invalid inputs]

# Test integration with existing features
[test it works with rest of system]
```

**Observe and record**:
- Actual output (what did ye see?)
- Actual behavior (what happened?)
- Logs generated (what was logged?)
- Error messages (clear and helpful?)
- Performance (reasonable speed?)

### Step 2: Create Test Report

Write `ai_working/ddd/test_report.md`:

```markdown
# User Testing Report

Feature: [name]
Tested by: AI (as QA entity)
Date: [timestamp]

## Test Scenarios

### Scenario 1: Basic Usage

**Tested**: [what ye tested]
**Command**: `[actual command run]`
**Expected** (per docs): [what docs say should happen]
**Observed**: [what actually happened]
**Status**: ✅ PASS / ❌ FAIL

[... continue fer all scenarios]

## Documentation Examples Verification

[Test ALL examples from docs]

## Integration Testing

[Test integration with other features]

## Issues Found

[List all issues with severity]

## Code-Based Test Verification

**Unit tests**:
```bash
pytest tests/
```

Status: ✅ All passin' / ❌ [N] failures

**Linting/Type checking**:
```bash
pre-commit run --all-files
```

Status: ✅ Clean / ❌ Issues found

## Summary

**Overall Status**: ✅ Ready / ⚠️ Issues to fix / ❌ Not workin'

**Code matches docs**: Yes/No
**Examples work**: Yes/No
**Tests pass**: Yes/No
**Ready fer user verification**: Yes/No

## Recommended Smoke Tests fer Human

User should verify:

1. **Basic functionality**:
   ```bash
   [command]
   # Should see: [expected output]
   ```

2. **Edge case**:
   ```bash
   [command]
   # Should see: [expected output]
   ```

3. **Integration**:
   ```bash
   [command]
   # Verify works with [existing feature]
   ```

## Next Steps

[Based on status, recommend next action]
```

### Step 3: Address Issues Found

If testin' revealed issues:
1. Note each issue clearly
2. Fix the code
3. Re-test
4. Update test report
5. Request commit authorization fer fixes

**Stay in this phase until all issues resolved, arr!**

---

## Iteration Loop

**This phase stays active until user says "all workin'"**:

User provides feedback:
- "Feature X doesn't work as expected"
- "Error message be confusin'"
- "Performance be slow"
- "Integration with Y be broken"

For each feedback:
1. Understand the issue
2. Fix the code
3. Re-test
4. Show changes
5. Request commit authorization
6. Repeat until user satisfied

---

## Using TodoWrite

Track implementation and testin' tasks:

```markdown
# Implementation
- [ ] Chunk 1 of N
- [ ] Chunk 2 of N
...
- [ ] All chunks implemented

# Testing
- [ ] User scenario 1 tested
- [ ] User scenario 2 tested
...
- [ ] Documentation examples verified
- [ ] Integration tests passin'
- [ ] Code tests passin'
- [ ] Test report written
- [ ] All issues resolved
- [ ] User confirms workin'
```

---

## Important Notes

**Code must match docs EXACTLY**:
- Docs are the contract
- If code needs to differ, update docs first
- Examples in docs MUST work when copy-pasted
- Error messages should match what docs describe

**Each commit needs authorization**:
- Never assume user wants to commit
- Show clear summary of changes
- Get explicit "yes" before committin'
- User can provide feedback instead

**Test as REAL user would**:
- Don't just run unit tests
- Actually use the CLI/feature
- Try the examples from docs
- See what real output looks like
- Experience what user will experience

**Stay in phase until workin'**:
- Don't rush to Phase 5
- Iterate as many times as needed
- Address all user feedback
- Only exit when user confirms "all workin'", arr!

---

## When All Working

### Exit Message

```
✅ Phase 4 Complete: Implementation & Testing, Arr!

All chunks implemented and committed.
All tests passin'.
User testin' complete.

Summary:
- Commits made: [count]
- Files changed: [count]
- Tests added: [count]
- Issues resolved: [count]

Test Report: ai_working/ddd/test_report.md

⚠️ USER CONFIRMATION

Is everything workin' as expected?

If YES, proceed to cleanup and finalization:

    /amplihack:ddd:5-finish

If NO, provide feedback and we'll continue iteratin' in Phase 4, matey!
```

---

**Ready to implement? Let's write some code, arr! 🏴‍☠️**
