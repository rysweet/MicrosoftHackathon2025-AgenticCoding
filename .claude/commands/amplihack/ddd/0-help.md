---
description: DDD workflow guide and help
---

# Document-Driven Development (DDD) - Complete Guide

Arr! Welcome to Document-Driven Development, matey! This be amplihack's systematic approach to buildin' complex features with AI assistance!

---

## What is Document-Driven Development?

**Core Principle**: Documentation BE the specification. Code implements what documentation describes.

**Why it works, ye scallywag**:
- Prevents context poisoning (inconsistent docs)
- Clear contracts before complexity
- Reviewable design before expensive implementation
- AI-optimized workflow
- Docs and code never drift

**Philosophy Foundation**:
- Ruthless Simplicity (from PHILOSOPHY.md)
- Modular Design / Bricks & Studs
- Zero-BS Implementation (no stubs, no placeholders)

---

## Complete Workflow (6 Phases)

### Main Workflow Commands (Run in Order, Arr!)

**1. `/amplihack:ddd:1-plan`** - Planning & Design
- Design feature before touchin' files
- Create comprehensive plan
- Get shared understanding
- **Output**: `ai_working/ddd/plan.md`

**2. `/amplihack:ddd:2-docs`** - Update All Non-Code Files
- Update docs, configs, READMEs
- Apply retcon writing (as if already exists)
- Iterate until approved
- **Requires**: User must commit when satisfied

**3. `/amplihack:ddd:3-code-plan`** - Plan Code Changes
- Assess current code vs new docs
- Plan all implementation changes
- Break into chunks
- **Requires**: User approval to proceed

**4. `/amplihack:ddd:4-code`** - Implement & Verify
- Write code matchin' docs exactly
- Test as user would
- Iterate until workin'
- **Requires**: User authorization for each commit

**5. `/amplihack:ddd:5-finish`** - Wrap-Up & Cleanup
- Clean temporary files
- Final verification
- Push/PR with explicit authorization
- **Requires**: User approval for all git operations

### Utility Commands

**`/amplihack:ddd:prime`** - Load all DDD context
- Loads complete methodology documentation
- Use at session start for full context

**`/amplihack:ddd:status`** - Check current progress
- Shows current phase
- Lists artifacts created
- Recommends next command

---

## State Management (Artifacts)

All phases use `ai_working/ddd/` directory:

```
ai_working/ddd/
├── plan.md              (Created by 1-plan, used by all)
├── docs_index.txt       (Working file for 2-docs)
├── docs_status.md       (Status from 2-docs)
├── code_plan.md         (Created by 3-code-plan)
├── impl_status.md       (Tracking for 4-code)
└── test_report.md       (Output from 4-code)
```

**Each command reads previous artifacts**, so ye can run subsequent commands without arguments to continue from where ye left off!

---

## Example Usage, Matey!

### Starting a New Feature

```bash
# Load context (optional but recommended)
/amplihack:ddd:prime

# Phase 1: Plan the feature
/amplihack:ddd:1-plan Add user authentication with JWT tokens

# Phase 2: Update all docs
/amplihack:ddd:2-docs

# Review the changes, iterate if needed
# When satisfied, commit the docs yerself

# Phase 3: Plan code implementation
/amplihack:ddd:3-code-plan

# Review the code plan, approve to continue

# Phase 4: Implement and test
/amplihack:ddd:4-code

# Test, provide feedback, iterate until workin'

# Phase 5: Finalize
/amplihack:ddd:5-finish

# Cleanup, push, PR (with yer explicit approval at each step)
```

### Checking Progress Mid-Stream

```bash
# See where ye are in the workflow
/amplihack:ddd:status

# It will tell ye:
# - Current phase
# - Artifacts created
# - Next recommended command
```

### Resuming After Break

```bash
# Check status
/amplihack:ddd:status

# Run next phase (artifacts are preserved)
/amplihack:ddd:3-code-plan
```

---

## Key Design Decisions

### No Auto-Commits

**Every git operation requires explicit user authorization**:
- Ye review changes before committin'
- Ye control commit messages
- Ye decide when to push
- Ye approve PR creation

### Iteration Support

**Phases 2 and 4 be designed for back-and-forth**:
- Provide feedback at any time
- Commands stay active until ye be satisfied
- Easy to iterate without restartin'

### Artifact-Driven

**Each phase creates artifacts for next phase**:
- Can run without arguments (uses artifacts)
- Can override with arguments if needed
- State preserved across sessions

### Agent Orchestration

**Each phase leverages amplihack's specialized agents**:
- architect for design
- builder for implementation
- reviewer for code review
- tester for testing
- cleanup for final cleanup

---

## Authorization Checkpoints

### Phase 2 (Docs)
- ⚠️ **YOU must commit docs after review**
- Command stages changes but does NOT commit
- Review diff, iterate if needed, then commit when satisfied

### Phase 4 (Code)
- ⚠️ **Each code chunk requires explicit commit authorization**
- Command asks before each commit
- Ye control commit messages and timing

### Phase 5 (Finish)
- ⚠️ **Explicit authorization for**: commit remaining, push, create PR
- Clear prompts at each decision point
- Ye control what happens to yer code

---

## Common Workflows

### Feature Development
1-plan → 2-docs → 3-code-plan → 4-code → 5-finish

### Bug Fix with Docs
1-plan → 2-docs → 3-code-plan → 4-code → 5-finish

### Documentation-Only Change
1-plan → 2-docs → 5-finish (skip code phases)

### Refactoring
1-plan → 2-docs → 3-code-plan → 4-code → 5-finish

---

## Troubleshooting, Arr!

### "I'm lost, where am I?"
```bash
/amplihack:ddd:status
```

### "I made a mistake in planning"
Edit `ai_working/ddd/plan.md` or re-run `/amplihack:ddd:1-plan` with corrections

### "Docs aren't right"
Stay in phase 2, provide feedback, command will iterate

### "Code isn't working"
Stay in phase 4, provide feedback, iterate until workin'

### "I want to start over"
```bash
rm -rf ai_working/ddd/
/amplihack:ddd:1-plan [your feature]
```

---

## Philosophy Alignment

Every phase checks against amplihack's philosophy:

**Ruthless Simplicity**:
- Start minimal, grow as needed
- Avoid future-proofing
- Question every abstraction
- Clear over clever

**Modular Design**:
- Clear interfaces (studs)
- Self-contained modules (bricks)
- Regeneratable from specs
- Human architects, AI builds

**Zero-BS Implementation**:
- No stubs or placeholders
- No TODOs in code
- No swallowed exceptions
- Everything works or doesn't exist

---

## Quick Reference Card

| Command                         | Purpose            | Output Artifact                | Next Step                                   |
| ------------------------------- | ------------------ | ------------------------------ | ------------------------------------------- |
| `/amplihack:ddd:prime`          | Load context       | -                              | Start workflow                              |
| `/amplihack:ddd:status`         | Check progress     | -                              | Shows next command                          |
| `/amplihack:ddd:1-plan`         | Design feature     | plan.md                        | `/amplihack:ddd:2-docs`                     |
| `/amplihack:ddd:2-docs`         | Update non-code    | docs_status.md                 | User commits, then `/amplihack:ddd:3-code-plan` |
| `/amplihack:ddd:3-code-plan`    | Plan code          | code_plan.md                   | User approves, then `/amplihack:ddd:4-code` |
| `/amplihack:ddd:4-code`         | Implement & test   | impl_status.md, test_report.md | User confirms working, then `/amplihack:ddd:5-finish` |
| `/amplihack:ddd:5-finish`       | Cleanup & finalize | -                              | Done, matey!                                |

---

## Core Concepts

For deeper understanding, see the DDD documentation:
- **File Crawling**: Systematic processing of many files (99.5% token reduction)
- **Context Poisoning**: Prevention of inconsistent documentation
- **Retcon Writing**: Write as if feature already exists (no "will be")

---

## Need More Help?

**Specific Questions**:
- "How do I handle X?"
- "What if Y happens?"
- "Explain Z concept"

**Check Phase-Specific Help**:
Each command has detailed instructions for its phase.

---

**Arr! Ready to build with Document-Driven Development?**

Run `/amplihack:ddd:1-plan [describe yer feature]` to set sail!

🏴‍☠️ **May ye code be simple and yer docs be true!** 🏴‍☠️
