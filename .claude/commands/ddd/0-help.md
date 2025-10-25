---
description: DDD workflow guide and help (project:ddd)
---

# Document-Driven Development (DDD) - Complete Guide

Ahoy matey! Ye be learnin' about Document-Driven Development - the systematic way to build features without gettin' lost at sea! 🏴‍☠️

Loading DDD context for comprehensive help...

@docs/DDD_METHODOLOGY.md
@docs/DDD_FILE_CRAWLING.md
@docs/DDD_CONTEXT_POISONING.md
@docs/DDD_RETCON_WRITING.md
@.claude/context/PHILOSOPHY.md

---

## What is Document-Driven Development?

**Core Principle**: Documentation BE the specification, arr! Code implements what documentation describes.

**Why it works**:
- Prevents context poisoning (no conflictin' docs, matey)
- Clear contracts before the complexity sets sail
- Reviewable design before expensive implementation
- AI-optimized workflow fer smooth sailin'
- Docs and code never drift apart like rival ships

**Philosophy Foundation**:
- Ruthless Simplicity (PHILOSOPHY.md)
- Modular Design / Bricks & Studs pattern
- Zero-BS implementation (no stubs, no TODOs!)

---

## Complete Workflow (5 Phases + Utilities)

### Main Workflow Commands (Run in Order, Arr!)

**1. `/amplihack:ddd:1-plan`** - Planning & Design

- Design feature before touchin' any files
- Create comprehensive plan
- Get shared understanding with yer crew
- **Output**: `ai_working/ddd/plan.md`

**2. `/amplihack:ddd:2-docs`** - Update All Non-Code Files

- Update docs, configs, READMEs
- Apply retcon writing (as if already exists, savvy?)
- Iterate until approved by the captain
- **Requires**: User must commit when satisfied

**3. `/amplihack:ddd:3-code-plan`** - Plan Code Changes

- Assess current code vs new docs
- Plan all implementation changes
- Break into manageable chunks
- **Requires**: User approval to proceed

**4. `/amplihack:ddd:4-code`** - Implement & Verify

- Write code matching docs exactly
- Test as a user would
- Iterate until workin' smooth
- **Requires**: User authorization for each commit

**5. `/amplihack:ddd:5-finish`** - Wrap-Up & Cleanup

- Clean temporary files
- Final verification
- Push/PR with explicit authorization
- **Requires**: User approval for all git operations

### Utility Commands

**`/amplihack:ddd:prime`** - Load all DDD context

- Loads complete methodology documentation
- Use at session start fer full context

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

**Each command reads previous artifacts**, so ye can run subsequent commands without arguments if ye want to continue from where ye left off, arr!

---

## Example Usage

### Starting a New Feature

```bash
# Load context (optional but recommended)
/amplihack:ddd:prime

# Phase 1: Plan the feature
/amplihack:ddd:1-plan Add JWT authentication for API

# Phase 2: Update all docs
/amplihack:ddd:2-docs

# Review the changes, iterate if needed
# When satisfied, commit the docs yourself

# Phase 3: Plan code implementation
/amplihack:ddd:3-code-plan

# Review the code plan, approve to continue

# Phase 4: Implement and test
/amplihack:ddd:4-code

# Test, provide feedback, iterate until working

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

**Every git operation requires explicit user authorization, matey**:

- You review changes before committin'
- You control commit messages
- You decide when to push
- You approve PR creation

### Iteration Support

**Phases 2 and 4 are designed fer back-and-forth**:

- Provide feedback at any time
- Commands stay active until yer satisfied
- Easy to iterate without restartin'

### Artifact-Driven

**Each phase creates artifacts fer next phase**:

- Can run without arguments (uses artifacts)
- Can override with arguments if needed
- State preserved across sessions

### Agent Orchestration

**Each phase suggests specialized agents**:

- architect fer design
- builder fer implementation
- reviewer fer code review
- tester fer testing
- cleanup fer final cleanup

---

## Authorization Checkpoints

### Phase 2 (Docs)

- ⚠️ **YOU must commit docs after review**
- Command stages changes but does NOT commit
- Review diff, iterate if needed, then commit when satisfied

### Phase 4 (Code)

- ⚠️ **Each code chunk requires explicit commit authorization**
- Command asks before each commit
- You control commit messages and timing

### Phase 5 (Finish)

- ⚠️ **Explicit authorization fer**: commit remaining, push, create PR
- Clear prompts at each decision point
- You control what happens to yer code

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

## Troubleshooting

### "I'm lost, where am I?"

```bash
/amplihack:ddd:status
```

### "I made a mistake in planning"

Edit `ai_working/ddd/plan.md` or re-run `/amplihack:ddd:1-plan` with corrections

### "Docs aren't right"

Stay in phase 2, provide feedback, command will iterate

### "Code isn't working"

Stay in phase 4, provide feedback, iterate until working

### "I want to start over"

```bash
rm -rf ai_working/ddd/
/amplihack:ddd:1-plan [your feature]
```

### "I need to understand a concept better"

Check the loaded documentation:
- @docs/DDD_METHODOLOGY.md
- @docs/DDD_FILE_CRAWLING.md
- @docs/DDD_CONTEXT_POISONING.md
- @docs/DDD_RETCON_WRITING.md

---

## Tips for Success

### For Humans

- Start with `/amplihack:ddd:prime` to load full context
- Use `/amplihack:ddd:status` frequently to stay oriented
- Trust the process - it prevents expensive mistakes
- Review thoroughly at approval gates
- Iterate as much as needed in phases 2 and 4

### For AI Assistants

- Follow the phase strictly
- Use TodoWrite in every phase
- Suggest appropriate agents
- Never commit without explicit authorization
- Iterate based on user feedback
- Exit phases only when user confirms ready

---

## Philosophy Alignment

Every phase checks against:

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
- Quality over speed

---

## Quick Reference Card

| Command                     | Purpose            | Output Artifact                | Next Step                                    |
| --------------------------- | ------------------ | ------------------------------ | -------------------------------------------- |
| `/amplihack:ddd:prime`      | Load context       | -                              | Start workflow                               |
| `/amplihack:ddd:status`     | Check progress     | -                              | Shows next command                           |
| `/amplihack:ddd:1-plan`     | Design feature     | plan.md                        | `/amplihack:ddd:2-docs`                      |
| `/amplihack:ddd:2-docs`     | Update non-code    | docs_status.md                 | User commits, then `/amplihack:ddd:3-code-plan` |
| `/amplihack:ddd:3-code-plan`| Plan code          | code_plan.md                   | User approves, then `/amplihack:ddd:4-code`  |
| `/amplihack:ddd:4-code`     | Implement & test   | impl_status.md, test_report.md | User confirms working, then `/amplihack:ddd:5-finish` |
| `/amplihack:ddd:5-finish`   | Cleanup & finalize | -                              | Done, arr!                                   |

---

## Need More Help?

**Loaded Documentation**:
- Methodology overview now in yer context
- Core concepts loaded
- Philosophy loaded

**Ask Specific Questions**:
- "How do I handle X?"
- "What if Y happens?"
- "Explain Z concept"

**Check Phase-Specific Help**:
Each command has detailed instructions for its phase.

---

**Ready to start? Run `/amplihack:ddd:1-plan [describe yer feature]`, arr! 🏴‍☠️**
