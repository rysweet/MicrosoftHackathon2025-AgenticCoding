#!/usr/bin/env bash
#
# Push all fixed branches to remote
#

set -euo pipefail

# Read branches from file (single source of truth)
BRANCHES=()
while IFS= read -r branch; do
    BRANCHES+=("$branch")
done < branches.txt

echo "==================================="
echo "Pushing Fixed Branches to Remote"
echo "==================================="

for branch in "${BRANCHES[@]}"; do
    echo ""
    echo "Pushing: $branch"
    if git push origin "$branch"; then
        echo "✓ $branch pushed successfully"
    else
        echo "✗ Failed to push $branch"
    fi
done

echo ""
echo "==================================="
echo "Push operation complete!"
echo "==================================="
