---
description: DDD Phase 2 - Update all non-code files (project:ddd)
argument-hint: [optional override instructions]
allowed-tools: TodoWrite, Read, Write, Edit, Grep, Glob, Task, Bash(git diff:*), Bash(git status:*), Bash(git add:*)
---

# DDD Phase 2: Non-Code Changes

Ahoy! Time to update all the documentation, arr! 🏴‍☠️

Loading context:

@docs/DDD_METHODOLOGY.md
@docs/DDD_FILE_CRAWLING.md
@docs/DDD_RETCON_WRITING.md
@docs/DDD_CONTEXT_POISONING.md
@ai_working/ddd/plan.md

Override instructions: $ARGUMENTS

---

## Yer Task: Update All Non-Code Files

**Goal**: Update docs, configs, READMEs to reflect new feature AS IF IT ALREADY EXISTS, matey!

**This phase iterates until user approves - stay in this phase as long as needed**

---

## Phase 2 Steps

### 1. Generate File Index

Create `ai_working/ddd/docs_index.txt`:

```bash
# Read the plan to get list of non-code files
# Create checklist in format:
[ ] docs/file1.md
[ ] README.md
...
```

This index be yer workin' checklist - mark files complete as ye process them.

### 2. File Crawling - Process One File at a Time

**THIS BE CRITICAL FER SUCCESS, ARR!**

For each file in the index:

1. **Load full context**:
   - Read the file
   - Read relevant parts of plan
   - Load related docs if needed

2. **Update with retcon writing**:
   - Write as if feature ALREADY EXISTS
   - No "will be", "going to", "planned"
   - Present tense: "The system does X"
   - No historical references
   - No migration notes in docs

3. **Apply Maximum DRY**:
   - Each concept in ONE place only
   - No duplicate documentation
   - Use references/links instead of duplication
   - If found elsewhere, consolidate to best location

4. **Check fer context poisonin'**:
   - Conflicts with other docs?
   - Inconsistent terminology?
   - Contradictory statements?
   - If found: PAUSE, document conflicts, ask user

5. **Mark complete in index**:
   ```bash
   # Change [ ] to [x]
   [x] docs/file1.md
   ```

6. **Move to next file** - REPEAT until all files processed

**Why file crawlin'?**
- Token efficiency (99.5% reduction fer large batches)
- Prevents missin' files
- Clear progress trackin'
- Resumable if interrupted
- Avoids context overflow

### 3. Verification Pass

After all files updated:

1. **Read through all changed docs** (use file index)
2. **Check consistency**:
   - Terminology consistent?
   - Examples would work?
   - No contradictions?
3. **Verify DRY**:
   - Each concept in one place?
   - No duplicate explanations?
4. **Check philosophy alignment**:
   - Ruthless simplicity maintained?
   - Clear module boundaries?

### 4. Generate Review Materials

Create `ai_working/ddd/docs_status.md`:

```markdown
# Phase 2: Non-Code Changes Complete

## Summary

[High-level description of what was changed]

## Files Changed

[List from git status]

## Key Changes

### docs/file1.md
- [What changed and why]

[... for each file]

## Deviations from Plan

[Any changes from original plan and why]

## Approval Checklist

Please review the changes:

- [ ] All affected docs updated?
- [ ] Retcon writing applied (no "will be")?
- [ ] Maximum DRY enforced (no duplication)?
- [ ] Context poisoning eliminated?
- [ ] Philosophy principles followed?
- [ ] Examples work (could copy-paste and use)?

## Git Diff Summary

[Insert: git diff --stat]

## Next Steps After Commit

When ye've committed the docs, run: `/amplihack:ddd:3-code-plan`
```

### 5. Show Git Diff

Run these commands to show user the changes:

```bash
git add [changed files]
git status
git diff --cached --stat
git diff --cached
```

**IMPORTANT**: Stage the changes with `git add` but **DO NOT COMMIT**, arr!

---

## Iteration Loop

**This phase stays active until user approves**:

If user provides feedback:
1. Note the feedback
2. Make requested changes
3. Update docs_status.md
4. Show new diff
5. Repeat until user says "approved"

---

## Using TodoWrite

Track doc update tasks:

```markdown
- [ ] Generate file index
- [ ] Process file 1 of N
- [ ] Process file 2 of N
...
- [ ] Verification pass complete
- [ ] Review materials generated
- [ ] User review in progress
```

---

## Retcon Writing Examples

**❌ BAD (Traditional)**:

```markdown
## Authentication (Coming in v2.0)

We will add JWT authentication support. Users will be able to
authenticate with tokens. This feature is planned for next quarter.
```

**✅ GOOD (Retcon)**:

```markdown
## Authentication

The system uses JWT authentication. Users authenticate with tokens
that expire after 24 hours.

Configure authentication in yer config file:
```yaml
auth:
  type: jwt
  expiry: 24h
```

See [Authentication Guide](auth.md) fer details, arr!
```

---

## Context Poisoning Detection

**PAUSE if ye find**:
- Same concept explained differently in multiple places
- Contradictory statements about behavior
- Inconsistent terminology fer same thing
- Feature described differently in different docs

**Actions when found**:
1. Document the conflicts
2. Note which docs conflict
3. Ask user: "Which version be correct?"
4. After clarification, fix ALL instances

---

## When User Approves

### Exit Message

```
✅ Phase 2 Complete: Non-Code Changes Approved, Arr!

All documentation updated and staged.

⚠️ USER ACTION REQUIRED:
Review the changes above and commit when satisfied:

    git commit -m "docs: [yer description]"

After committin', proceed to code planning:

    /amplihack:ddd:3-code-plan

The updated docs are now the specification that code must match, matey!
```

---

**Ready to update those docs? Let's set sail, arr! 🏴‍☠️**
