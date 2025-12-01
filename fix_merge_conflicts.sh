#!/usr/bin/env bash
#
# Fix merge conflicts in stop.py across multiple branches
# Issue: #1778
#
# This script:
# 1. Fixes the conflict at line 231 (pragma comment)
# 2. Verifies Python syntax
# 3. Commits the fix
# 4. Reports results
#
# Usage:
#   ./fix_merge_conflicts.sh [--dry-run]

set -euo pipefail

# Configuration
FILE_PATH=".claude/tools/amplihack/hooks/stop.py"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

# Branches to fix
BRANCHES=(
    "chore/issue-1378-gitignore-settings"
    "chore/pre-commit-formatting-fixes"
    "feat/issue-1356-outside-in-testing-skill"
    "feat/issue-1359-serena-clean"
    "feat/issue-1359-serena-integration"
    "feat/issue-1359-serena-simple"
    "feat/issue-1360-design-patterns-skill"
    "feat/issue-1363-goal-seeking-agent-pattern-skill"
    "feat/issue-1363-goal-seeking-skill-only"
    "feat/issue-1369-priority-2-docs-clean"
    "feat/issue-1402-workflow-quick-win"
    "feat/issue-1403-workflow-comprehensive"
    "feat/issue-1404-workflow-maximum"
    "feat/issue-1420-tdd-prevention-suite"
)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0;m' # No Color

# Counters
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

# Log file
LOG_FILE=".claude/runtime/logs/merge-fix-$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$1" | tee -a "$LOG_FILE"
}

fix_branch() {
    local branch="$1"
    log "\n=== Processing: $branch ==="

    # Check out branch
    if ! git checkout "$branch" 2>&1 | tee -a "$LOG_FILE"; then
        log "${RED}✗ Failed to checkout branch${NC}"
        ((FAILED_COUNT++))
        return 1
    fi

    # Check if conflict exists
    if ! grep -q "<<<<<<< HEAD" "$FILE_PATH" 2>/dev/null; then
        log "${YELLOW}⊘ No conflict markers found - skipping${NC}"
        ((SKIPPED_COUNT++))
        return 0
    fi

    if $DRY_RUN; then
        log "${YELLOW}[DRY RUN] Would fix conflict in $branch${NC}"
        return 0
    fi

    # Fix the conflict using Python
    python3 << 'EOF'
import sys

# Read file
with open('.claude/tools/amplihack/hooks/stop.py', 'r') as f:
    content = f.read()

# Check for conflict
if '<<<<<<< HEAD' not in content:
    print("No conflict found")
    sys.exit(0)

# Fix conflict - keep the line with pragma comment
lines = content.splitlines(keepends=True)
result = []
i = 0

while i < len(lines):
    line = lines[i]

    # Found conflict start
    if line.strip().startswith("<<<<<<<"):
        # Save position
        conflict_start = i

        # Find the line between HEAD and =======
        i += 1
        head_line = lines[i]

        # Skip to =======
        while i < len(lines) and not lines[i].strip().startswith("======="):
            i += 1

        # Skip to >>>>>>> and grab their line
        i += 1
        their_line = lines[i]

        # Skip to end marker
        while i < len(lines) and not lines[i].strip().startswith(">>>>>>>"):
            i += 1

        # Choose the line WITH pragma comment (has more text)
        if len(head_line) > len(their_line):
            result.append(head_line)
        else:
            result.append(their_line)

        i += 1
    else:
        result.append(line)
        i += 1

# Write fixed content
with open('.claude/tools/amplihack/hooks/stop.py', 'w') as f:
    f.write(''.join(result))

print("Conflict resolved")
EOF

    # Verify no conflict markers remain
    if grep -q "<<<<<<< HEAD\|=======\|>>>>>>>" "$FILE_PATH"; then
        log "${RED}✗ Conflict markers still present after fix${NC}"
        ((FAILED_COUNT++))
        git checkout -- "$FILE_PATH"  # Revert changes
        return 1
    fi

    # Verify Python syntax
    if ! python3 -m py_compile "$FILE_PATH" 2>&1 | tee -a "$LOG_FILE"; then
        log "${RED}✗ Python syntax verification failed${NC}"
        ((FAILED_COUNT++))
        git checkout -- "$FILE_PATH"  # Revert changes
        return 1
    fi

    # Stage and commit
    git add "$FILE_PATH"
    if git commit -m "fix: Resolve merge conflict in stop.py (pragma comment)

Fixes #1778

The conflict was about adding a pragma comment to line 355:
- Kept: # pragma: allowlist secret
- This prevents security scanners from flagging the intentional password variable

The fix preserves the security annotation while resolving the conflict." 2>&1 | tee -a "$LOG_FILE"; then
        log "${GREEN}✓ Successfully fixed and committed${NC}"
        ((SUCCESS_COUNT++))
    else
        log "${RED}✗ Commit failed${NC}"
        ((FAILED_COUNT++))
        return 1
    fi
}

# Main execution
log "======================================"
log "Merge Conflict Fix Script"
log "Issue: #1778"
log "Date: $(date)"
log "======================================"

# Store original branch
ORIGINAL_BRANCH=$(git branch --show-current)
log "\nOriginal branch: $ORIGINAL_BRANCH"

# Process each branch
for branch in "${BRANCHES[@]}"; do
    fix_branch "$branch" || true  # Continue on error
done

# Return to original branch
log "\n=== Returning to original branch ==="
git checkout "$ORIGINAL_BRANCH"

# Summary
log "\n======================================"
log "SUMMARY"
log "======================================"
log "Total branches: ${#BRANCHES[@]}"
log "${GREEN}✓ Success: $SUCCESS_COUNT${NC}"
log "${RED}✗ Failed: $FAILED_COUNT${NC}"
log "${YELLOW}⊘ Skipped: $SKIPPED_COUNT${NC}"
log "\nLog file: $LOG_FILE"
log "======================================"

# Exit with error if any failures
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi
