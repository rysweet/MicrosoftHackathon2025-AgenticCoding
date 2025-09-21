#!/usr/bin/env python3
"""
PR Review Posting Tool

This tool ensures that PR reviews are posted as comments, not as PR description edits.
It provides a safe interface for the reviewer agent to post reviews.
"""

import subprocess
import sys
from typing import Optional


def post_pr_review(pr_number: int, review_content: str) -> bool:
    """
    Post a review as a PR comment using GitHub CLI.

    This function enforces the correct behavior of posting reviews as comments,
    NOT as PR description edits. It uses 'gh pr comment' exclusively.

    Args:
        pr_number: The PR number to comment on
        review_content: The formatted review content to post

    Returns:
        True if the review was posted successfully, False otherwise

    Example:
        >>> review = '''## Review Summary
        ... **Overall Assessment**: Good
        ... ### Strengths
        ... - Clean code structure'''
        >>> post_pr_review(123, review)
        True
    """
    if not pr_number or not review_content:
        print("Error: PR number and review content are required", file=sys.stderr)
        return False

    try:
        # IMPORTANT: Always use 'gh pr comment' for reviews
        # Never use 'gh pr edit' as that modifies the PR description
        cmd = ["gh", "pr", "comment", str(pr_number), "--body", review_content]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode == 0:
            print(f"✓ Review posted as comment on PR #{pr_number}")
            return True
        else:
            print(f"✗ Failed to post review: {result.stderr}", file=sys.stderr)
            return False

    except subprocess.CalledProcessError as e:
        print(f"✗ Error posting review: {e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}", file=sys.stderr)
        return False


def validate_review_format(review_content: str) -> Optional[str]:
    """
    Validate that review content follows the expected format.

    Args:
        review_content: The review content to validate

    Returns:
        Error message if invalid, None if valid
    """
    required_sections = [
        "## Review Summary",
        "**Overall Assessment**:",
        "### Strengths",
        "### Philosophy Compliance",
    ]

    for section in required_sections:
        if section not in review_content:
            return f"Missing required section: {section}"

    return None


def format_review_for_github(review_content: str) -> str:
    """
    Format review content for GitHub markdown rendering.

    Args:
        review_content: Raw review content

    Returns:
        Formatted review content with proper markdown
    """
    # Ensure proper line endings for GitHub
    formatted = review_content.replace("\r\n", "\n").replace("\r", "\n")

    # Add review signature if not present
    if "Generated with" not in formatted:
        formatted += "\n\n---\n🤖 Generated with [Claude Code](https://claude.ai/code)"

    return formatted


def main():
    """Example usage and self-test."""
    print("PR Review Posting Tool")
    print("=" * 50)
    print("\nThis tool ensures reviews are posted as PR comments.")
    print("It enforces the use of 'gh pr comment' instead of 'gh pr edit'.\n")

    # Example review content
    example_review = """## Review Summary

**Overall Assessment**: Good

### Strengths
- Clean module boundaries
- Follows single responsibility principle
- Good error handling

### Issues Found
1. **Complexity**: Helper function could be simplified
   - Location: src/utils.py:45
   - Impact: Low
   - Suggestion: Inline the single-use function

### Recommendations
- Consider adding more unit tests for edge cases
- Update documentation to reflect new changes

### Philosophy Compliance
- Simplicity: 8/10
- Modularity: 9/10
- Clarity: 8/10"""

    print("Example review format:")
    print("-" * 50)
    print(example_review)
    print("-" * 50)

    # Validate format
    validation_error = validate_review_format(example_review)
    if validation_error:
        print(f"\n✗ Validation failed: {validation_error}")
    else:
        print("\n✓ Review format is valid")

    print("\nTo post this review to PR #123, you would use:")
    print("  post_pr_review(123, review_content)")
    print("\nThis will execute: gh pr comment 123 --body '<review_content>'")
    print("\nIMPORTANT: Never use 'gh pr edit' for reviews!")


if __name__ == "__main__":
    main()
