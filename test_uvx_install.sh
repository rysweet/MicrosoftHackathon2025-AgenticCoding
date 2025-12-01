#!/usr/bin/env bash
#
# Test uvx installation from fixed branches
# Requirement: USER_PREFERENCES.md "Mandatory End-to-End Testing"
#

set -euo pipefail

# Read branches from file (portable)
BRANCHES=()
while IFS= read -r branch; do
    BRANCHES+=("$branch")
done < branches.txt

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0;m'

# Counters
SUCCESS_COUNT=0
FAILED_COUNT=0

LOG_FILE=".claude/runtime/logs/uvx-test-$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log "========================================"
log "UVX Installation Testing"
log "Testing $(wc -l < branches.txt) fixed branches"
log "Date: $(date)"
log "========================================\n"

for branch in "${BRANCHES[@]}"; do
    log "Testing branch: $branch"

    # Test uvx installation
    if uvx --from "git+https://github.com/rysweet/MicrosoftHackathon2025-AgenticCoding@${branch}" amplihack --help >/dev/null 2>&1; then
        log "${GREEN}✓${NC} $branch: uvx install works"
        ((SUCCESS_COUNT++))
    else
        log "${RED}✗${NC} $branch: uvx install FAILED"
        ((FAILED_COUNT++))
    fi
done

log "\n========================================"
log "TEST SUMMARY"
log "========================================"
log "Total branches: ${#BRANCHES[@]}"
log "${GREEN}✓ Success: $SUCCESS_COUNT${NC}"
log "${RED}✗ Failed: $FAILED_COUNT${NC}"
log "\nLog file: $LOG_FILE"
log "========================================"

# Exit with error if any failures
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi
