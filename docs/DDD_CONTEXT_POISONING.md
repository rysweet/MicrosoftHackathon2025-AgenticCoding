# Context Poisoning

**Arr! Understanding and preventing inconsistent information that misleads AI tools, matey!**

---

## What is Context Poisoning?

**Context poisoning** occurs when AI tools load inconsistent or conflicting information from the codebase, leading to wrong decisions and implementations.

**Metaphor**: Imagine a chef following multiple recipes for the same dish that contradict each other on ingredients and temperatures. The dish will fail. Same with code - AI following contradictory "recipes" (documentation) produces broken implementations.

---

## Why It's Critical

When AI tools load context for a task, they may:
- Load stale doc instead of current one
- Load conflicting docs and guess wrong
- Not know which source is authoritative
- Combine information incorrectly
- Make wrong decisions confidently

**Real-world impact**:
- Wasted hours implementing wrong design
- Bugs from mixing incompatible approaches
- Rework when conflicts discovered later
- User confusion when docs contradict
- Loss of trust in documentation

---

## Common Sources

### 1. Duplicate Documentation

Same concept described differently in multiple files

**Example**:
- `docs/USER_GUIDE.md`: "Workflows configure your environment"
- `docs/API.md`: "Profiles define capability sets"

**Impact**: AI doesn't know if "workflow" == "profile" or they're different

### 2. Stale Documentation

Docs don't match current code

**Example**:
- Docs: "Use `amplihack setup` to configure"
- Code: Only `amplihack init` works

**Impact**: AI generates code using removed command

### 3. Inconsistent Terminology

Multiple terms for same concept

**Example**:
- README: "workflow"
- USER_GUIDE: "profile"
- API: "capability set"

**Impact**: AI confused about canonical term

### 4. Historical References

Old approaches mentioned alongside new

**Example**:
```markdown
Previously, use `setup`. Now use `init`.
For now, both work.
```

**Impact**: AI implements BOTH, doesn't know which is current

---

## Prevention Strategies

### 1. Maximum DRY (Don't Repeat Yourself)

**Rule**: Each concept lives in exactly ONE place.

**Good organization**:
- ✅ Command syntax → `docs/USER_GUIDE.md#commands`
- ✅ Architecture → `docs/ARCHITECTURE.md`
- ✅ API reference → `docs/API.md`

**Cross-reference, don't duplicate**:
```markdown
For command syntax, see [USER_GUIDE.md#commands](...)

NOT: Duplicating all command syntax inline
```

### 2. Aggressive Deletion

When ye find duplication:
1. Identify which doc is canonical
2. **Delete** the duplicate entirely (don't update it)
3. Update cross-references to canonical source

**Why delete vs. update?**
- Prevents future divergence
- If it exists, it will drift
- Deletion is permanent elimination

### 3. Retcon, Don't Evolve

**BAD** (creates poison):
```markdown
Previously, use `amplihack setup`.
As of version 2.0, use `amplihack init`.
In future, `setup` will be removed.
For now, both work.
```

**GOOD** (clean retcon):
```markdown
## Configuration

Configure amplihack:
```bash
amplihack init
```

Historical info belongs in git history and CHANGELOG, not docs.

### 4. Systematic Global Updates

When terminology changes:
```bash
# 1. Global replace (first pass only)
find docs/ -name "*.md" -exec sed -i 's/\bworkflow\b/profile/g' {} +

# 2. STILL review each file individually
# Global replace is helper, not solution

# 3. Verify
grep -rn "\bworkflow\b" docs/  # Should be zero or intentional

# 4. Commit together
git commit -am "docs: Standardize terminology: workflow → profile"
```

---

## Detection and Resolution

### During Documentation Phase

**Watch for**:
- Conflicting definitions
- Duplicate content
- Inconsistent examples
- Historical baggage

**Action**: PAUSE, collect all instances, get human guidance

### Resolution Pattern

```markdown
# CONFLICT DETECTED - User guidance needed

## Issue
[Describe what conflicts]

## Instances
1. file1.md:42: says X
2. file2.md:15: says Y
3. file3.md:8: says Z

## Analysis
[What's most common, what matches code, etc.]

## Suggested Resolutions
Option A: [description]
Option B: [description]

## Recommendation
[AI's suggestion with reasoning]

Please advise which resolution to apply.
```

**Wait for human decision**, then apply systematically.

---

## Prevention Checklist

Before committing any documentation:

- [ ] No duplicate concepts across files
- [ ] Consistent terminology throughout
- [ ] No historical references (use retcon)
- [ ] All cross-references point to existing content
- [ ] Each doc has clear, non-overlapping scope
- [ ] Examples all work (test them)
- [ ] No "old way" and "new way" both shown
- [ ] Version numbers removed (docs always current)

---

## Quick Reference

### Detection

**Ask yerself**:
- Can same information be found in multiple places?
- Are there multiple terms for same concept?
- Do docs reference "old" vs "new" approaches?
- Do examples conflict with each other?

**If yes to any**: Context poisoning present

### Prevention

**Core rules**:
1. Each concept in ONE place only
2. Delete duplicates (don't update)
3. Use retcon (not evolution)
4. Consistent terminology everywhere
5. Test all examples work

### Resolution

**When detected**:
1. PAUSE all work
2. Collect all instances
3. Present to human with options
4. Wait for decision
5. Apply resolution systematically
6. Verify with grep

---

**Arr! Keep yer docs clean and yer context pure!** 🏴‍☠️
