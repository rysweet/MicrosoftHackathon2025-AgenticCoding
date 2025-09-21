#!/usr/bin/env python3
"""
Example: How to post PR reviews correctly

This example demonstrates the correct way to post PR reviews as comments,
not as PR description edits.
"""

from pr_review import format_review_for_github, validate_review_format


def example_correct_review():
    """Example of posting a review the RIGHT way."""
    print("=" * 60)
    print("CORRECT WAY: Posting PR Review as Comment")
    print("=" * 60)

    pr_number = 123  # Replace with actual PR number

    # Format the review using the standard template
    review_content = """## Review Summary

**Overall Assessment**: Good

### Strengths
- Follows single responsibility principle
- Clean module boundaries with clear contracts
- Good error handling throughout
- Comprehensive test coverage

### Issues Found

1. **Complexity**: The `process_data` function is doing too much
   - Location: src/processor.py:156-210
   - Impact: Medium
   - Suggestion: Split into separate validation and transformation functions

2. **Philosophy Violation**: Found a stub function that's not implemented
   - Location: src/utils.py:45
   - Impact: High
   - Suggestion: Either implement or remove per Zero-BS principle

### Recommendations
- Add integration tests for the new API endpoints
- Update the module specification in Specs/ directory
- Consider caching the expensive computation in line 180

### Philosophy Compliance
- Simplicity: 7/10 (some unnecessary abstractions found)
- Modularity: 9/10 (excellent module boundaries)
- Clarity: 8/10 (mostly clear, but some complex logic needs comments)"""

    # Validate the format
    validation_error = validate_review_format(review_content)
    if validation_error:
        print(f"✗ Review format invalid: {validation_error}")
        return

    # Format for GitHub
    formatted_review = format_review_for_github(review_content)

    print("\nReview content to be posted:")
    print("-" * 60)
    print(formatted_review)
    print("-" * 60)

    print(f"\n✓ This will be posted as a COMMENT on PR #{pr_number}")
    print("✓ The PR description will remain UNCHANGED")
    print("\nCommand that will be executed:")
    print(f"  gh pr comment {pr_number} --body '<review_content>'")

    # Uncomment to actually post the review:
    # success = post_pr_review(pr_number, formatted_review)
    # if success:
    #     print(f"\n✓ Review successfully posted to PR #{pr_number}")


def example_wrong_way():
    """Example of what NOT to do."""
    print("\n" + "=" * 60)
    print("WRONG WAY: What NOT to Do")
    print("=" * 60)

    print("\n❌ NEVER use these commands for posting reviews:")
    print("  gh pr edit 123 --body 'review content'")
    print("  gh pr edit 123 --description 'review content'")

    print("\n❌ These commands MODIFY the PR description")
    print("❌ This overwrites the author's original PR description")
    print("❌ Reviews should be in the discussion thread, not the description")

    print("\n✓ ALWAYS use this instead:")
    print("  gh pr comment 123 --body 'review content'")


def example_enforcement():
    """Example of how the tool enforces correct behavior."""
    print("\n" + "=" * 60)
    print("ENFORCEMENT: How the Tool Protects Against Mistakes")
    print("=" * 60)

    print("\nThe pr_review.py tool enforces correct behavior:")
    print("1. It ONLY uses 'gh pr comment' internally")
    print("2. It NEVER uses 'gh pr edit'")
    print("3. It validates review format before posting")
    print("4. It adds proper formatting for GitHub markdown")

    print("\nEven if someone tries to misuse it, the tool ensures:")
    print("- Reviews go to comments")
    print("- PR descriptions are preserved")
    print("- Review format is consistent")


if __name__ == "__main__":
    print("PR Review Posting Examples")
    print("=" * 60)
    print("This script demonstrates correct PR review posting.\n")

    # Show the correct way
    example_correct_review()

    # Show what not to do
    example_wrong_way()

    # Show enforcement
    example_enforcement()

    print("\n" + "=" * 60)
    print("Remember: Reviews are COMMENTS, not DESCRIPTION EDITS!")
    print("=" * 60)
