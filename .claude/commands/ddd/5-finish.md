---
description: DDD Phase 5 - Cleanup and finalize (project:ddd)
argument-hint: [optional instructions]
allowed-tools: TodoWrite, Read, Write, Bash(git:*), Bash(pre-commit:*), Bash(pytest:*), Bash(rm:*), Glob, Task
---

# DDD Phase 5: Wrap-Up & Cleanup

Ahoy! Time to clean up the ship and push to harbor, matey! 🏴‍☠️

Loading context:

@ai_working/ddd/

Instructions: $ARGUMENTS

---

## Yer Task: Clean Up & Finalize

**Goal**: Remove temporary files, verify clean state, push/PR with explicit authorization

**Every git operation requires EXPLICIT user authorization, arr!**

---

## Phase 5 Steps

### Step 1: Cleanup Temporary Files

Remove all DDD workin' artifacts:

```bash
# Show what will be deleted
ls -la ai_working/ddd/

# Ask user: "Delete DDD workin' files?"
# If yes:
rm -rf ai_working/ddd/
```

Remove any test artifacts:

```bash
# Common locations
rm -rf .pytest_cache/
rm -rf __pycache__/
rm -f .coverage
rm -rf htmlcov/
rm -rf .ruff_cache/
```

Remove debug code:

```bash
# Search fer common debug patterns
grep -r "console.log" src/
grep -r "print(" src/  # except legitimate loggin'
grep -r "debugger" src/
grep -r "TODO.*debug" src/

# If found, ask user: "Remove debug code?"
# Show locations, get confirmation, then remove
```

### Step 2: Final Verification

Run complete quality check:

```bash
pre-commit run --all-files
```

**Status**: ✅ All passin' / ❌ Issues found

If issues found:
- List all issues clearly
- Ask user: "Fix these before finishin'?"
- If yes, fix and re-run
- If no, note in summary

Check git status:

```bash
git status
```

**Questions to answer**:
- Are there uncommitted changes? (Should there be?)
- Are there untracked files? (Should they be added/ignored?)
- Is workin' tree clean? (Or remainin' work?)

List all commits from this DDD session:

```bash
# Assumin' session started after last push
git log --oneline origin/$(git branch --show-current)..HEAD
```

**Show user**:
- Number of commits
- Summary of each commit
- Overall changes (insertions/deletions)

### Step 3: Commit Any Remaining Changes

Check fer uncommitted changes:

```bash
git status --short
```

If changes exist:

**Ask user**: "There be uncommitted changes. Commit them?"

If YES:
- Show the diff
- Ask fer commit message or suggest one
- Request explicit authorization
- Commit with provided/suggested message

If NO:
- Leave changes uncommitted
- Note in final summary

### Step 4: Push to Remote

**Ask user**: "Push to remote?"

Show context:

```bash
# Current branch
git branch --show-current

# Commits to push
git log --oneline origin/$(git branch --show-current)..HEAD
```

If YES:
- Confirm which remote and branch
- Push with: `git push -u origin [branch]`
- Show result

If NO:
- Leave local only
- Note in final summary

### Step 5: Create Pull Request (If Appropriate)

**Determine if PR be appropriate**:
- Are we on a feature branch? (not main/master)
- Has branch been pushed?
- Does user want a PR?

If appropriate, **ask user**: "Create pull request?"

If YES:

**Generate PR description** from DDD artifacts:

```markdown
## Summary

[From plan.md: Problem statement and solution]

## Changes

### Documentation

[List docs changed]

### Code

[List code changed]

### Tests

[List tests added]

## Testing

[From test_report.md: Key test scenarios]

## Verification Steps

[From test_report.md: Recommended smoke tests]

## Related

[Link to any related issues/discussions]
```

**Create PR** (usin' gh pr create):

```bash
gh pr create --title "[Feature name]" --body "[generated description]" 2>&1 | cat
```

Show PR URL to user.

If NO:
- Skip PR creation
- Note in final summary

### Step 6: Post-Cleanup Check

Consider spawnin' specialized cleanup agent:

```bash
Task cleanup: "Review workspace fer any remainin'
temporary files, test artifacts, or unnecessary complexity"
```

Final workspace verification:

```bash
# Workin' tree clean?
git status

# No untracked files that shouldn't be there?
git ls-files --others --exclude-standard

# Quality checks pass?
pre-commit run --all-files
```

### Step 7: Generate Final Summary

Create comprehensive completion summary:

```markdown
# DDD Workflow Complete, Arr! 🎉

## Feature: [Name from plan.md]

**Problem Solved**: [from plan.md]
**Solution Implemented**: [from plan.md]

## Changes Made

### Documentation (Phase 2)

- Files updated: [count]
- Key docs: [list 3-5 most important]
- Commit: [hash and message]

### Code (Phase 4)

- Files changed: [count]
- Implementation chunks: [count]
- Commits: [list all commit hashes and messages]

### Tests

- Unit tests added: [count]
- Integration tests added: [count]
- All tests passin': ✅ / ❌

## Quality Metrics

- `pre-commit run --all-files`: ✅ Passin' / ❌ Issues
- Code matches documentation: ✅ Yes
- Examples work: ✅ Yes
- User testin': ✅ Complete

## Git Summary

- Total commits: [count]
- Branch: [name]
- Pushed to remote: Yes / No
- Pull request: [URL] / Not created

## Artifacts Cleaned

- DDD workin' files: ✅ Removed
- Temporary files: ✅ Removed
- Debug code: ✅ Removed
- Test artifacts: ✅ Removed

## Recommended Next Steps fer User

### Verification Steps

Please verify the followin':

1. **Basic functionality**:
   ```bash
   [command]
   # Expected: [output]
   ```

2. **Edge cases**:
   ```bash
   [command]
   # Expected: [output]
   ```

3. **Integration**:
   ```bash
   [command]
   # Verify works with [existing features]
   ```

[List 3-5 key smoke tests from test_report.md]

### If Issues Found

If ye find any issues:

1. Provide specific feedback
2. Re-run `/amplihack:ddd:4-code` with feedback
3. Iterate until resolved
4. Re-run `/amplihack:ddd:5-finish` when ready

## Workspace Status

- Workin' tree: Clean / [uncommitted changes]
- Branch: [name]
- Ready fer: Next feature

---

**DDD workflow complete. Ready fer next work, arr! 🏴‍☠️**
```

---

## Using TodoWrite

Track finalization tasks:

```markdown
- [ ] Temporary files cleaned
- [ ] Final verification passed
- [ ] Remainin' changes committed (if any)
- [ ] Pushed to remote (if authorized)
- [ ] PR created (if authorized)
- [ ] Post-cleanup check complete
- [ ] Final summary generated
```

---

## Authorization Checkpoints

### 1. Delete DDD Working Files

⚠️ **Ask**: "Delete ai_working/ddd/ directory?"
- Show what will be deleted
- Get explicit yes/no

### 2. Delete Temporary Files

⚠️ **Ask**: "Delete temporary/test artifacts?"
- Show what will be deleted
- Get explicit yes/no

### 3. Remove Debug Code

⚠️ **Ask**: "Remove debug code?"
- Show locations found
- Get explicit yes/no

### 4. Commit Remaining Changes

⚠️ **Ask**: "Commit these changes?"
- Show git diff
- Get explicit yes/no
- If yes, get/suggest commit message

### 5. Push to Remote

⚠️ **Ask**: "Push to remote?"
- Show branch and commit count
- Get explicit yes/no

### 6. Create PR

⚠️ **Ask**: "Create pull request?"
- Show PR description preview
- Get explicit yes/no
- If yes, create and show URL

---

## Important Notes

**Never assume**:
- Always ask before git operations
- Show what will happen
- Get explicit authorization
- Respect user's decisions

**Clean thoroughly**:
- DDD artifacts served their purpose
- Test artifacts aren't needed
- Debug code shouldn't ship
- Workin' tree should be clean

**Verify completely**:
- All tests passin'
- Quality checks clean
- No unintended changes
- Ready fer production

**Document everything**:
- Final summary should be comprehensive
- Include verification steps
- Note any follow-up items
- Preserve commit history

---

## Completion Message

```
✅ DDD Phase 5 Complete, Arr!

Feature: [name]
Status: Complete and verified

All temporary files cleaned.
Workspace ready fer next work.

Summary saved above.

---

Thank ye fer usin' Document-Driven Development, matey! 🚀

For yer next feature, start with:

    /amplihack:ddd:1-plan [feature description]

Or check current status anytime:

    /amplihack:ddd:status

Need help? Run: /amplihack:ddd:0-help
```

---

**Ready to finish up? Let's clean ship, arr! 🏴‍☠️**
