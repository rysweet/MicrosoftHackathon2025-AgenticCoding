# Document-Driven Development (DDD) Methodology

**Systematic approach to complex feature development that prevents context poisoning and enables efficient AI-driven implementation.**

---

## What is Document-Driven Development?

Document-Driven Development (DDD) is a systematic approach where:

1. **Documentation comes first** - Design and document the system before writing code
2. **Documentation IS the specification** - Code must match what docs describe exactly
3. **Approval gate** - Human reviews and approves design before implementation
4. **Implementation follows docs** - Code implements what documentation promises
5. **Testing verifies docs** - Tests ensure code matches documentation

**Core Principle**: "Documentation IS the specification. Code implements what documentation describes."

---

## The Problem: Context Poisoning

**Traditional approach**: Code → Docs (if at all)

What happens:
- Docs written after code or never updated
- Docs lag behind code changes
- Docs and code diverge over time
- AI tools load stale/conflicting docs
- Context poisoning leads to wrong implementations
- Bugs from misunderstanding requirements

**Result**: Documentation becomes untrustworthy. Developers stop reading docs. More bugs.

---

## The DDD Solution

**DDD approach**: Docs → Approval → Implementation

What happens:
- Design captured in docs first
- Human reviews and approves design
- **Only then** write code
- Code matches docs exactly
- Tests verify code matches docs
- Docs and code never diverge

**Result**: Documentation is always correct. Single source of truth. Fewer bugs.

---

## Why This Works (Especially for AI)

### 1. Prevents Context Poisoning
- Single source of truth for each concept
- No duplicate documentation
- No stale docs (updated before code)
- Clear, unambiguous specifications

### 2. Clear Contracts First
- Docs define interfaces before implementation
- Contracts clear before complexity added
- Easier to review design than code
- Cheaper to fix design than implementation

### 3. Reviewable Design
- Design reviewed at approval gate
- Catch flaws before coding
- Iterate on docs (cheap) not code (expensive)
- Human judgment applied early

### 4. AI-Optimized
- Docs always current
- No conflicting information
- Clear specifications
- AI can't guess wrong (spec is clear)

### 5. No Drift
- Docs come first, so can't lag
- If code needs to differ, update docs first
- Always in sync by design
- Drift is impossible

---

## Complete DDD Workflow

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
    ↓
Approval Gate ←─────────┐
    ↓                   │
    • Human reviews     │
    • Iterate until     │ (iterate if needed)
      right             │
    ↓                   │
    ├───────────────────┘
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
    • Test as user would
    • Commit incrementally
    ↓
Phase 5: Cleanup & Push
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
- API changes affecting documentation
- Any change touching 10+ files
- Cross-cutting concerns

**High-stakes work**:
- User-facing features
- Breaking changes
- Complex integrations
- Architecture decisions

**Collaborative work**:
- Multiple developers involved
- Need clear specification
- External review required

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

### Prevents Expensive Mistakes
- Catch design flaws before implementation
- Review is cheap, rework is expensive
- Philosophy compliance checked early
- Human judgment applied at right time

### Eliminates Context Poisoning
- Single source of truth
- No duplicate documentation
- No stale information
- Clear, unambiguous specs

### Optimizes AI Collaboration
- AI has clear specifications
- No guessing from unclear docs
- Can regenerate from spec
- Systematic file processing

### Maintains Quality
- Documentation always correct
- Code matches documentation
- Examples always work
- New developers understand from docs

### Reduces Bugs
- Fewer misunderstandings
- Clear requirements
- Tested against spec
- Integration verified

---

## Philosophy Integration

DDD builds on amplihack's core principles:

### Ruthless Simplicity
- Simple docs easier to maintain
- No speculative features in docs
- Each doc has one clear purpose
- Progressive organization

**Applied in DDD**:
- Start minimal, grow as needed
- Avoid future-proofing
- Question every abstraction
- Clear over clever

### Modular Design (Bricks & Studs)
- Self-contained modules
- Clear interfaces (studs)
- Regeneratable from spec
- Human architects, AI builds

**Applied in DDD**:
- Docs define interfaces (studs)
- Code implements modules (bricks)
- Can regenerate from docs
- Human reviews design, AI implements

### Zero-BS Implementation
- No stubs or placeholders
- No TODOs in code
- No swallowed exceptions
- Complete features only

**Applied in DDD**:
- Every phase enforces zero-BS
- Verification at each checkpoint
- Quality over speed

---

## Core Techniques

DDD uses three key techniques throughout:

### 1. File Crawling
- Process many files systematically (99.5% token reduction)
- External checklist prevents AI forgetting files
- One file at a time for full context
- See: [DDD_FILE_CRAWLING.md](DDD_FILE_CRAWLING.md)

### 2. Context Poisoning Prevention
- Maximum DRY (each concept in ONE place)
- Eliminate duplicate documentation
- Consistent terminology everywhere
- See: [DDD_CONTEXT_POISONING.md](DDD_CONTEXT_POISONING.md)

### 3. Retcon Writing
- Write as if feature already exists (no "will be")
- Present tense only ("system does X")
- No historical references
- Single timeline: NOW
- See: [DDD_RETCON_WRITING.md](DDD_RETCON_WRITING.md)

---

## Getting Started

### Quick Start

```bash
# 1. Prime the context
/amplihack:ddd:prime

# 2. Start planning
/amplihack:ddd:1-plan [describe your feature]

# 3. Follow the workflow
# Check status anytime: /amplihack:ddd:status
```

### Commands Reference

| Command                      | Purpose                    |
| ---------------------------- | -------------------------- |
| `/amplihack:ddd:prime`       | Load complete DDD context  |
| `/amplihack:ddd:status`      | Check current progress     |
| `/amplihack:ddd:0-help`      | Complete guide and reference |
| `/amplihack:ddd:1-plan`      | Phase 1: Planning & Design |
| `/amplihack:ddd:2-docs`      | Phase 2: Documentation     |
| `/amplihack:ddd:3-code-plan` | Phase 3: Implementation Planning |
| `/amplihack:ddd:4-code`      | Phase 4: Code & Testing    |
| `/amplihack:ddd:5-finish`    | Phase 5: Cleanup & Push    |

### Core Concepts

- **[File Crawling](DDD_FILE_CRAWLING.md)** - Process many files systematically
- **[Context Poisoning](DDD_CONTEXT_POISONING.md)** - Prevent inconsistent docs
- **[Retcon Writing](DDD_RETCON_WRITING.md)** - Write as if already exists

---

## Success Criteria

You're doing DDD well when:

**Documentation Quality**:
- ✅ Docs and code never diverge
- ✅ Zero context poisoning incidents
- ✅ Examples all work when copy-pasted
- ✅ New developers understand from docs alone

**Process Quality**:
- ✅ Changes require minimal rework
- ✅ Design flaws caught at approval gate
- ✅ Philosophy principles naturally followed
- ✅ Git history is clean (no thrashing)

**AI Collaboration**:
- ✅ AI tools make correct decisions consistently
- ✅ No "wrong approach implemented confidently"
- ✅ Can regenerate modules from specs

**Team Impact**:
- ✅ Implementation time decreases (better specs)
- ✅ Bug rate decreases (fewer misunderstandings)
- ✅ Questions about features, not "which docs are right?"

---

## Common Questions

### "This is too much process"
**Reality**: Process prevents expensive rework. An hour in planning saves days of coding wrong thing.

### "We don't have time for this"
**Reality**: You don't have time NOT to do this. Rework from misunderstanding costs far more than upfront clarity.

### "Our docs are already good"
**Reality**: If docs and code can diverge, they will. DDD makes divergence impossible by design.

### "AI doesn't need perfect docs"
**Reality**: AI makes wrong decisions confidently when docs conflict. Context poisoning is real and expensive.

---

**Ready to start? Run `/amplihack:ddd:1-plan [describe your feature]`**
