#!/usr/bin/env bash
#
# Push all fixed branches to remote
#

set -euo pipefail

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
