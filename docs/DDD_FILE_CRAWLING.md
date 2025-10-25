# File Crawling Technique

**Arr! Systematic processing of many files without context overload, matey!**

---

## What is File Crawling?

File crawling be a technique for processing large numbers of files systematically using an external index and sequential processing. It solves the fundamental problem that AI cannot hold all files in context at once.

**Core pattern**: External checklist → Process one file → Mark complete → Repeat

---

## The Problem It Solves

### AI Limitations

AI assistants have critical limitations:
- **Limited context window** - Cannot hold 100+ files at once
- **Attention degradation** - Misses files in large lists
- **Memory limitations** - Forgets files between iterations
- **False confidence** - Thinks it remembers but doesn't

**Real example**: AI shown list of 100 files. AI processes first 20, then forgets about the rest. Returns saying "all done" but 80 files untouched.

---

## The Solution: External Index + Sequential Processing

### Core Pattern

```bash
# 1. Generate external checklist
find . -name "*.md" > /tmp/checklist.txt
sed -i 's/^/[ ] /' /tmp/checklist.txt

# 2. Process loop - AI reads only ONE line at a time
while [ $(grep -c "^\[ \]" /tmp/checklist.txt) -gt 0 ]; do
  # Get next uncompleted file (5-10 tokens)
  NEXT=$(grep -m1 "^\[ \]" /tmp/checklist.txt | sed 's/\[ \] //')

  # Process this ONE file completely
  # - AI reads full file
  # - AI makes all needed changes
  # - AI verifies changes

  # Mark complete (in-place edit)
  sed -i "s|\[ \] $NEXT|[x] $NEXT|" /tmp/checklist.txt
done

# 3. Cleanup
rm /tmp/checklist.txt
```

---

## Why It Works

### Token Efficiency

**Without file crawling**: 100 iterations × 2,000 tokens = 200,000 tokens wasted

**With file crawling**: 100 iterations × 10 tokens = 1,000 tokens

**Savings**: 199,000 tokens (99.5% reduction)

### Key Benefits

1. **No forgetting** - Files tracked externally, not in AI memory
2. **Clear progress** - Visual `[x]` marks show what's done
3. **Resumable** - Can stop and restart without losing place
4. **Systematic** - Guarantees every file processed exactly once
5. **Verifiable** - Human can check progress anytime

---

## When to Use File Crawling

### ✅ Use When:
- Processing 10+ files systematically
- Each file requires similar updates
- Need clear progress visibility
- Want resumability
- Working across multiple turns

### ✅ Common in DDD:
- **Phase 2**: Processing all documentation files
- **Phase 4**: Implementing changes across files
- **Phase 5**: Testing all documented examples

---

## Step-by-Step Guide

### Step 1: Generate File Index

```bash
# Find all files to process
find . -type f -name "*.md" ! -path "*/.git/*" > /tmp/files_to_process.txt

# Convert to checklist format
sed 's/^/[ ] /' /tmp/files_to_process.txt > /tmp/checklist.txt

# Show AI the checklist once
cat /tmp/checklist.txt
```

### Step 2: Sequential Processing

```bash
# AI executes this pattern
while [ $(grep -c "^\[ \]" /tmp/checklist.txt) -gt 0 ]; do
  # Get next (minimal tokens)
  NEXT=$(grep -m1 "^\[ \]" /tmp/checklist.txt | sed 's/\[ \] //')

  echo "Processing: $NEXT"

  # AI reads this ONE file COMPLETELY
  # AI makes ALL needed changes
  # AI verifies changes worked

  # Mark complete ONLY after full review
  sed -i "s|\[ \] $NEXT|[x] $NEXT|" /tmp/checklist.txt

  # Optional: Show progress every 10 files
  if [ $((counter % 10)) -eq 0 ]; then
    DONE=$(grep -c "^\[x\]" /tmp/checklist.txt)
    TOTAL=$(wc -l < /tmp/checklist.txt)
    echo "Progress: $DONE/$TOTAL files"
  fi
  counter=$((counter + 1))
done
```

### Step 3: Verify and Cleanup

```bash
# Verify all files processed
REMAINING=$(grep -c "^\[ \]" /tmp/checklist.txt)
if [ $REMAINING -gt 0 ]; then
  echo "WARNING: $REMAINING files not processed"
  grep "^\[ \]" /tmp/checklist.txt
else
  echo "✓ All files processed"
fi

# Cleanup
rm /tmp/checklist.txt /tmp/files_to_process.txt
```

---

## Common Mistakes to Avoid

### ❌ Loading Entire Checklist into Context

```bash
# BAD: All 100 files in context
for file in $(cat /tmp/checklist.txt); do
  # Won't work
done

# GOOD: Only next file
NEXT=$(grep -m1 "^\[ \]" /tmp/checklist.txt | sed 's/\[ \] //')
```

### ❌ Marking Complete Without Full Review

**Why this matters**: Global replacements miss files and context. Each file needs individual attention.

### ❌ Processing Multiple Files Per Iteration

Process one file at a time for best results.

---

## Quick Reference

```bash
# Standard Pattern

# 1. Generate index
find . -name "*.md" > /tmp/files.txt
sed 's/^/[ ] /' /tmp/files.txt > /tmp/checklist.txt

# 2. Process loop
while [ $(grep -c "^\[ \]" /tmp/checklist.txt) -gt 0 ]; do
  NEXT=$(grep -m1 "^\[ \]" /tmp/checklist.txt | sed 's/\[ \] //')
  # Process $NEXT completely
  sed -i "s|\[ \] $NEXT|[x] $NEXT|" /tmp/checklist.txt
done

# 3. Cleanup
rm /tmp/checklist.txt /tmp/files.txt
```

---

**Arr! File crawling be the secret to processin' many files efficiently!** 🏴‍☠️
