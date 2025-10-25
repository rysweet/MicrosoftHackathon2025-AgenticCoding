# Document-Driven Development (DDD) - Methodology Overview

**Arr! This be amplihack's systematic approach to buildin' complex features with AI assistance, matey!**

---

## What is Document-Driven Development?

Document-Driven Development (DDD) is a systematic approach where:

1. **Documentation comes first** - Ye design and document the system before writin' code
2. **Documentation BE the specification** - Code must match what docs describe exactly
3. **Approval gate** - Human reviews and approves design before implementation
4. **Implementation follows docs** - Code implements what documentation promises
5. **Testing verifies docs** - Tests ensure code matches documentation

**Core Principle**: "Documentation BE the specification. Code implements what documentation describes."

---

## Why This Works (Especially for AI)

### 1. Prevents Context Poisoning

**Context poisoning** = AI loads inconsistent information, makes wrong decisions

**How DDD prevents it**:
- Single source of truth for each concept
- No duplicate documentation
- No stale docs (updated before code)
- Clear, unambiguous specifications

### 2. Clear Contracts First

- Docs define interfaces before implementation
- Contracts clear before complexity added
- Easier to review design than code
- Cheaper to fix design than implementation

### 3. AI-Optimized

- Docs always current
- No conflicting information
- Clear specifications
- AI can't guess wrong (spec is clear)

### 4. No Drift

- Docs come first, so can't lag
- If code needs to differ, update docs first
- Always in sync by design
- Drift is impossible

---

## The Complete Workflow

```
Phase 1: Planning & Design
    ↓
    • Problem framing
    • Reconnaissance
    • Proposals and iteration
    • Shared understanding
    ↓
Phase 2: Documentation Retcon
    ↓
    • Update ALL docs to target state
    • Write as if already exists
    • Maximum DRY enforcement
    • Progressive organization
    ↓
Phase 3: Implementation Planning
    ↓
    • Code reconnaissance
    • Detailed plan
    • Right-sizing check
    ↓
Phase 4: Code Implementation
    ↓
    • Code matches docs exactly
    • Load full context
    • Commit incrementally
    ↓
Phase 5: Testing & Verification
    ↓
    • Test documented behaviors
    • Test as user would
    • AI is QA entity
    ↓
Phase 6: Cleanup & Push
    ↓
    • Remove temporary files
    • Final verification
    • Push to remote
```

---

## When to Use DDD

### ✅ Use DDD For

**Large changes**:
- New features requiring multiple files
- System redesigns or refactoring
- Any change touching 10+ files
- Cross-cutting concerns

**High-stakes work**:
- User-facing features
- Breaking changes
- Complex integrations
- Architecture decisions

### ❌ Don't Use DDD For

**Simple changes**:
- Typo fixes
- Single-file bug fixes
- Trivial updates

**Emergency situations**:
- Production hotfixes
- Critical security patches

**When uncertain**: Lean toward using DDD. Process prevents expensive mistakes.

---

## Key Benefits

- **Prevents Expensive Mistakes**: Catch design flaws before implementation
- **Eliminates Context Poisoning**: Single source of truth
- **Optimizes AI Collaboration**: Clear specifications
- **Maintains Quality**: Documentation always correct
- **Reduces Bugs**: Fewer misunderstandings

---

## Commands

- `/amplihack:ddd:0-help` - Complete guide
- `/amplihack:ddd:status` - Check progress
- `/amplihack:ddd:prime` - Load full context
- `/amplihack:ddd:1-plan` - Planning & Design
- `/amplihack:ddd:2-docs` - Update Documentation
- `/amplihack:ddd:3-code-plan` - Plan Code
- `/amplihack:ddd:4-code` - Implement & Test
- `/amplihack:ddd:5-finish` - Cleanup & Finalize

---

## Philosophy Alignment

DDD builds on amplihack's core principles:

**Ruthless Simplicity**:
- Start minimal, grow as needed
- Avoid future-proofing
- Clear over clever

**Modular Design**:
- Clear interfaces (studs)
- Self-contained modules (bricks)
- Regeneratable from specs

**Zero-BS Implementation**:
- No stubs or placeholders
- No TODOs in code
- Everything works or doesn't exist

---

## Quick Start

```bash
# Load context
/amplihack:ddd:prime

# Start planning
/amplihack:ddd:1-plan [describe yer feature]

# Follow the workflow
# Check status anytime: /amplihack:ddd:status
```

---

**Arr! May yer docs be true and yer code be simple!** 🏴‍☠️
