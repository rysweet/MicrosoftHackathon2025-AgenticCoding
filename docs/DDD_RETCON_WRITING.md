# Retcon Writing

**Arr! Writing documentation as if the feature already exists, matey!**

---

## What is Retcon Writing?

**Retcon** (retroactive continuity) means writing documentation as if the new feature already exists and always worked this way. No historical references, no "will be implemented," just pure present-tense description of how it works.

**Purpose**: Eliminate ambiguity about what's current, what's planned, and what's historical.

---

## Why Retcon Writing Matters

### The Problem with Traditional Documentation

**Traditional approach**:
```markdown
## Provider Configuration (Updated 2025-01-15)

Previously, providers were configured using `amplihack setup`.
This approach has been deprecated as of version 2.0.

Now, use `amplihack init` instead.

In a future release, `setup` will be removed entirely.

For now, both work, but we recommend using `init`.
```

**What's wrong**:
- AI doesn't know which approach is current
- Mix of past, present, and future
- Unclear if `setup` still works
- Version numbers add confusion
- Multiple timelines create ambiguity

**Result**: AI might implement `setup`, or `init`, or both. Wrong decision made confidently.

### The Retcon Solution

**Retcon approach**:
```markdown
## Configuration

Configure amplihack using the init wizard:

```bash
amplihack init
```

The wizard guides ye through configuration.
```

**What's right**:
- Single timeline: NOW
- Clear current approach
- No version confusion
- No historical baggage
- Unambiguous for AI and humans

**Result**: AI knows exactly what to implement. Humans know exactly how to use it.

---

## Retcon Writing Rules

### DO:

✅ **Write in present tense** - "The system does X" not "will do X"

✅ **Write as if always existed** - Describe current reality only

✅ **Show actual commands** - Examples that work right now

✅ **Use canonical terminology** - No invented names

✅ **Document all complexity** - Be honest about what's required

✅ **Focus on now** - Not past, not future, just now

### DON'T:

❌ **"This will change to X"** - Write as if X is reality

❌ **"Coming soon" or "planned"** - Only document what you're implementing

❌ **Migration notes in main docs** - Belongs in CHANGELOG or git history

❌ **Historical references** - "Used to work this way"

❌ **Version numbers in docs** - Docs are always current

❌ **Future-proofing** - Document what exists, not what might

❌ **Transition language** - "Now use init instead of setup"

---

## Examples

### Example 1: Command Syntax

**BAD** (traditional):
```markdown
## Setup Command (Deprecated)

The `amplihack setup` command was used in v1.0 to configure providers.

As of v2.0, this is deprecated. Use `amplihack init` instead.

Example (old way - don't use):
amplihack setup

Example (new way - recommended):
amplihack init
```

**GOOD** (retcon):
```markdown
## Initial Configuration

Configure amplihack on first use:

```bash
amplihack init
```

The init wizard guides ye through configuration.
```

### Example 2: Configuration Files

**BAD** (traditional):
```markdown
## Settings Files

Previously, settings were stored in `~/.amplihack/config.json`.

In v2.0, we migrated to YAML format for better readability.

Old location (deprecated): `~/.amplihack/config.json`
New location: `~/.amplihack/settings.yaml`

If you're upgrading from v1.0, run `amplihack migrate` to convert your settings.
```

**GOOD** (retcon):
```markdown
## Settings Files

Amplihack stores settings in YAML format:

- `~/.amplihack/settings.yaml` - User-global settings
- `.amplihack/settings.yaml` - Project settings
- `.amplihack/settings.local.yaml` - Local overrides (gitignored)
```

---

## Where Historical Information Goes

**Retcon main docs**, but preserve history where appropriate:

### CHANGELOG.md

```markdown
# Changelog

## [2.0.0] - 2025-01-15

### Changed
- Configuration format: JSON → YAML
- Setup command: `amplihack setup` → `amplihack init`

### Migration
Run `amplihack migrate` to update v1.0 settings to v2.0 format.
```

### Git Commit Messages

```bash
git commit -m "refactor: Replace setup command with init

Replaces `amplihack setup` with `amplihack init`.

BREAKING CHANGE: `amplihack setup` has been removed.
Users should use `amplihack init` instead.

Migration: Manual update required for existing users."
```

**Key point**: Migration info goes in dedicated migration docs, CHANGELOG, and git history. NOT in main user-facing documentation.

---

## Benefits of Retcon Writing

### 1. Eliminates Ambiguity

**Single timeline**: Documentation describes ONE reality (current state)

**AI benefit**: No confusion about what to implement

**Human benefit**: No confusion about how to use it

### 2. Prevents Context Poisoning

**No mixed timelines**: Can't load "old approach" by mistake

**No version confusion**: Docs are always current

**Clear specification**: AI knows exactly what to build

### 3. Cleaner Documentation

**Shorter**: No historical baggage

**Focused**: Just how it works now

**Maintainable**: One timeline to maintain

### 4. Better User Experience

**Users don't care about history**: They want to know how it works now

**Clear examples**: Commands that actually work

**No confusion**: Single approach shown

---

## When NOT to Retcon

### Keep History When:

1. **CHANGELOG.md** - Explicitly about changes over time
2. **Migration guides** - Purpose is to document transition
3. **Git history** - Commit messages and history

### Retcon Everywhere Else:

- Main README
- User guides
- API documentation
- Architecture docs
- Examples and tutorials

---

## Quick Reference

### Retcon Writing Checklist

Before committing documentation:

- [ ] All present tense ("system does X")
- [ ] No "will" or "planned" language
- [ ] No historical references ("used to")
- [ ] No version numbers in main content
- [ ] No transition language ("now use X instead of Y")
- [ ] No backward compatibility notes in main docs
- [ ] Examples work with current code

### Quick Fixes

**Find non-retcon language**:
```bash
# Check for future tense
grep -rn "will be\|coming soon\|planned" docs/

# Check for historical references
grep -rn "previously\|used to\|old way\|new way" docs/

# Check for version numbers
grep -rn "v[0-9]\|version [0-9]" docs/

# Check for transition language
grep -rn "instead of\|rather than\|no longer" docs/
```

**Fix systematically**:
- Remove identified issues
- Rewrite in present tense
- Describe only current state

---

**Arr! Write as if the future be now, and the past be forgotten!** 🏴‍☠️
