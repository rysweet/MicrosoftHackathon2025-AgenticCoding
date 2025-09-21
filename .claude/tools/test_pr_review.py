#!/usr/bin/env python3
"""Test module for PR review posting functionality."""

import subprocess
import unittest
from unittest.mock import patch


class TestPRReviewPosting(unittest.TestCase):
    """Test cases for PR review comment posting."""

    def test_pr_review_uses_comment_not_edit(self):
        """Test that PR reviews are posted as comments, not edits."""
        # Mock review content
        review_content = """## Review Summary

**Overall Assessment**: Good

### Strengths
- Clean module boundaries
- Good error handling

### Issues Found
1. **Complexity**: Helper function could be simplified
   - Location: src/utils.py:45
   - Impact: Low
   - Suggestion: Inline the single-use function

### Recommendations
- Consider adding more unit tests
- Update documentation

### Philosophy Compliance
- Simplicity: 8/10
- Modularity: 9/10
- Clarity: 8/10"""

        pr_number = 123

        # Test that the correct command would be used
        # In actual implementation, this would be called by the reviewer
        with patch("subprocess.run") as mock_run:
            # Simulate posting a review
            post_pr_review(pr_number, review_content)

            # Verify the correct command was called
            mock_run.assert_called_once()
            called_args = mock_run.call_args[0][0]

            # Check that gh pr comment was used
            self.assertEqual(called_args[0:3], ["gh", "pr", "comment"])
            self.assertIn(str(pr_number), called_args)

            # Ensure gh pr edit was NOT used
            self.assertNotIn("edit", called_args)

    def test_pr_review_preserves_description(self):
        """Test that PR description remains unchanged after review."""
        pr_number = 123
        original_description = "Original PR description"
        review_content = "Review content"

        with patch("subprocess.run") as mock_run:
            # Mock getting the original description
            mock_run.return_value.stdout = original_description

            # Post review
            post_pr_review(pr_number, review_content)

            # Verify no edit command was called
            for call in mock_run.call_args_list:
                args = call[0][0] if call[0] else []
                if "gh" in args and "pr" in args:
                    self.assertNotIn("edit", args, "PR edit should not be called")


def post_pr_review(pr_number: int, review_content: str) -> bool:
    """
    Post a review as a PR comment.

    This function should ONLY use 'gh pr comment', never 'gh pr edit'.

    Args:
        pr_number: The PR number to comment on
        review_content: The review content to post

    Returns:
        True if successful, False otherwise
    """
    try:
        # CORRECT: Use gh pr comment
        cmd = ["gh", "pr", "comment", str(pr_number), "--body", review_content]

        # INCORRECT (for reference - this is what NOT to do):
        # cmd = ["gh", "pr", "edit", str(pr_number), "--body", review_content]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


if __name__ == "__main__":
    unittest.main()
