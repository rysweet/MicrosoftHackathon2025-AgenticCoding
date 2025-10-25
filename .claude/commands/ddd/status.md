---
description: Show current DDD progress and next steps (project:ddd)
allowed-tools: Read, Bash(ls:*), Bash(cat:*), Bash(git status:*), Bash(git log:*)
---

# DDD Workflow Status

Ahoy! Checkin' yer current Document-Driven Development progress, matey... 🏴‍☠️

---

## DDD Working Directory

!`ls -la ai_working/ddd/ 2>/dev/null || echo "❌ No active DDD session (no ai_working/ddd/ directory)"`

---

## Phase Detection

Checkin' which artifacts exist to determine current phase:

**Phase 1 (Plan)**: !`test -f ai_working/ddd/plan.md && echo "✅ Plan created" || echo "❌ No plan yet"`

**Phase 2 (Docs)**: !`test -f ai_working/ddd/docs_status.md && echo "✅ Docs updated" || echo "❌ Docs not updated"`

**Phase 3 (Code Plan)**: !`test -f ai_working/ddd/code_plan.md && echo "✅ Code planned" || echo "❌ Code not planned"`

**Phase 4 (Code)**: !`test -f ai_working/ddd/impl_status.md && echo "✅ Code implemented" || echo "❌ Code not implemented"`

**Phase 5 (Finish)**: !`test -d ai_working/ddd/ && echo "⏳ Not finished yet" || echo "✅ Workflow complete (no artifacts remain)"`

---

## Git Status

Current workin' tree state:

!`git status --short || git status`

---

## Recent DDD-Related Commits

!`git log --oneline --all --grep="docs:\|feat:\|fix:" -10 2>/dev/null || git log --oneline -10`

---

## Current Branch

!`git branch --show-current`

---

## Unpushed Commits

!`git log --oneline origin/$(git branch --show-current)..HEAD 2>/dev/null || echo "No unpushed commits or remote branch doesn't exist"`

---

## Status Analysis

Based on the artifacts detected above, here be yer current status:

### Current Phase

**Determinin' phase...**

If `ai_working/ddd/` doesn't exist:
- **Status**: No active DDD session
- **Recommendation**: Start new feature with `/amplihack:ddd:1-plan [feature]`

If `plan.md` exists but not `docs_status.md`:
- **Status**: Phase 1 complete (Planning done)
- **Next**: Update documentation with `/amplihack:ddd:2-docs`

If `docs_status.md` exists but not `code_plan.md`:
- **Status**: Phase 2 in progress or awaitin' commit
- **Next**:
  - If docs not committed yet: Review and commit them
  - If docs committed: Plan code with `/amplihack:ddd:3-code-plan`

If `code_plan.md` exists but not `impl_status.md`:
- **Status**: Phase 3 complete (Code planned)
- **Next**: Implement code with `/amplihack:ddd:4-code`

If `impl_status.md` exists:
- **Status**: Phase 4 in progress (Implementation)
- **Next**: Continue `/amplihack:ddd:4-code` or finalize with `/amplihack:ddd:5-finish`

If no `ai_working/ddd/` but recent DDD commits:
- **Status**: DDD workflow previously completed
- **Next**: Start new feature with `/amplihack:ddd:1-plan [feature]`

---

## Artifact Details

### Quick Access to Current Artifacts

If artifacts exist, ye can read them:

**Plan** (Phase 1 output):
```bash
Read ai_working/ddd/plan.md
```

**Docs Status** (Phase 2 output):
```bash
Read ai_working/ddd/docs_status.md
```

**Code Plan** (Phase 3 output):
```bash
Read ai_working/ddd/code_plan.md
```

**Implementation Status** (Phase 4 tracking):
```bash
Read ai_working/ddd/impl_status.md
```

**Test Report** (Phase 4 output):
```bash
Read ai_working/ddd/test_report.md
```

---

## Recommended Next Command

Based on current phase:

**If no active session**:
```bash
/amplihack:ddd:1-plan [describe yer feature]
```

**If plan exists, docs not updated**:
```bash
/amplihack:ddd:2-docs
```

**If docs updated but not committed**:
```bash
# Review changes:
git diff

# When satisfied, commit:
git commit -m "docs: [yer description]"

# Then:
/amplihack:ddd:3-code-plan
```

**If docs committed, code not planned**:
```bash
/amplihack:ddd:3-code-plan
```

**If code planned but not implemented**:
```bash
/amplihack:ddd:4-code
```

**If code implemented but not finalized**:
```bash
/amplihack:ddd:5-finish
```

**If workflow complete**:
```bash
# Start next feature:
/amplihack:ddd:1-plan [next feature]
```

---

## Workflow Progress Summary

**Complete DDD Workflow**:

```
Phase 1: Planning ━━━━━━━━━┓
                         ↓
Phase 2: Docs ━━━━━━━━━━┫  ← Where are ye?
                         ↓
Phase 3: Code Plan ━━━━━┫
                         ↓
Phase 4: Code ━━━━━━━━━━┫
                         ↓
Phase 5: Finish ━━━━━━━━┛
```

**Yer Progress**: [Based on phase detection above]

---

## Git Summary

!`echo "Branch: $(git branch --show-current)"`
!`echo "Uncommitted changes: $(git status --short | wc -l) files"`
!`echo "Unpushed commits: $(git log --oneline origin/$(git branch --show-current)..HEAD 2>/dev/null | wc -l) commits"`

---

## Need Help?

**For complete DDD guide**:
```bash
/amplihack:ddd:0-help
```

**To load all DDD context**:
```bash
/amplihack:ddd:prime
```

**For phase-specific help**:
Run the command for that phase - each has detailed instructions, arr!

---

## Troubleshooting

**"I'm lost, not sure where I am"**
- Review the Phase Detection section above
- Check which artifacts exist
- Follow Recommended Next Command

**"I made a mistake in [phase]"**
- **Planning**: Edit `ai_working/ddd/plan.md` or re-run `/amplihack:ddd:1-plan`
- **Docs**: Re-run `/amplihack:ddd:2-docs` with feedback
- **Code Planning**: Edit `ai_working/ddd/code_plan.md` or re-run `/amplihack:ddd:3-code-plan`
- **Code**: Provide feedback to `/amplihack:ddd:4-code`

**"I want to start over"**
```bash
# Delete DDD artifacts
rm -rf ai_working/ddd/

# Start fresh
/amplihack:ddd:1-plan [feature]
```

**"I want to abandon this feature"**
```bash
# Delete DDD artifacts
rm -rf ai_working/ddd/

# Reset git changes (if needed)
git reset --hard HEAD
# or
git stash
```

---

**Status check complete, matey! Ready to continue? Run the recommended next command above, arr! 🏴‍☠️**
