"""Unit tests for Issue Generator module.

Tests GitHub integration with templates and rate limiting.
Follows TDD approach - tests written before implementation.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from ...core.issue_generator import (
    GitHubIssueCreator,
    IssueCreationResult,
    IssueGenerator,
    IssueTemplate,
    RateLimiter,
)
from ...core.pattern_extractor import ImprovementPattern


class TestIssueGenerator(unittest.TestCase):
    """Test cases for IssueGenerator main orchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = IssueGenerator()

    def test_create_issue_basic_pattern(self):
        """Should create GitHub issue from improvement pattern."""
        pattern = self._create_test_pattern(
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed authentication bug in login system",
            evidence=["before/after code", "test results"],
        )

        with patch.object(self.generator.github_creator, "create_issue") as mock_create:
            mock_create.return_value = IssueCreationResult(
                success=True,
                issue_number=123,
                issue_url="https://github.com/test/repo/issues/123",
                title="Code Improvement: Fixed authentication bug in login system",
            )

            result = self.generator.create_issue(pattern)

            self.assertTrue(result.success)
            self.assertEqual(result.issue_number, 123)
            self.assertIn("authentication", result.title or "")
            mock_create.assert_called_once()

    def test_create_issue_with_template(self):
        """Should use appropriate template based on pattern type."""
        pattern = self._create_test_pattern(
            type="prompt_improvement",
            subtype="clarity",
            description="Improved prompt clarity for API requests",
        )

        with patch.object(self.generator.github_creator, "create_issue") as mock_create:
            mock_create.return_value = IssueCreationResult(
                success=True,
                issue_number=124,
                issue_url="https://github.com/test/repo/issues/124",
                title="Prompt Improvement: Improved prompt clarity for API requests",
            )

            self.generator.create_issue(pattern)

            # Verify template selection
            call_args = mock_create.call_args[1]
            self.assertIn("## Prompt Improvement", call_args["body"])
            self.assertIn("clarity", call_args["body"])

    def test_create_issue_rate_limiting(self):
        """Should respect rate limiting when creating issues."""
        pattern = self._create_test_pattern()

        with patch.object(self.generator.rate_limiter, "can_make_request") as mock_rate_check:
            mock_rate_check.return_value = False

            result = self.generator.create_issue(pattern)

            self.assertFalse(result.success)
            self.assertIn("rate limit", (result.error_message or "").lower())

    def test_create_issue_github_error(self):
        """Should handle GitHub API errors gracefully."""
        pattern = self._create_test_pattern()

        with patch.object(self.generator.github_creator, "create_issue") as mock_create:
            mock_create.side_effect = Exception("GitHub API Error")

            result = self.generator.create_issue(pattern)

            self.assertFalse(result.success)
            self.assertIn("GitHub API Error", result.error_message or "")

    def test_create_issue_with_sanitization(self):
        """Should sanitize sensitive content before creating issues."""
        pattern = self._create_test_pattern(
            description="Fixed API key leak: removed password='secret123' from logs",  # pragma: allowlist secret
            evidence=["token abc123def456", "api_key=xyz789"],
        )

        with patch.object(self.generator.github_creator, "create_issue") as mock_create:
            mock_create.return_value = IssueCreationResult(
                success=True,
                issue_number=125,
                issue_url="https://github.com/test/repo/issues/125",
                title="Code Improvement: Fixed API key leak",
            )

            self.generator.create_issue(pattern)

            # Verify sanitization occurred
            call_args = mock_create.call_args[1]
            body = call_args["body"]
            self.assertNotIn("secret123", body)
            self.assertNotIn("abc123def456", body)  # pragma: allowlist secret
            self.assertNotIn("xyz789", body)
            self.assertIn("[REDACTED]", body)

    def test_get_generation_statistics(self):
        """Should provide comprehensive statistics."""
        # Create multiple issues to generate stats
        pattern1 = self._create_test_pattern(type="code_improvement")
        pattern2 = self._create_test_pattern(type="system_fix")

        with patch.object(self.generator.github_creator, "create_issue") as mock_create:
            mock_create.return_value = IssueCreationResult(success=True, issue_number=123)

            self.generator.create_issue(pattern1)
            self.generator.create_issue(pattern2)

        stats = self.generator.get_generation_statistics()
        self.assertEqual(stats["total_issues_attempted"], 2)
        self.assertEqual(stats["successful_creations"], 2)
        self.assertIn("by_type", stats)

    def _create_test_pattern(
        self,
        type="code_improvement",
        subtype="bug_fix",
        description="Test improvement",
        evidence=None,
    ) -> ImprovementPattern:
        """Helper to create test patterns."""
        return ImprovementPattern(
            id=f"test-{hash(description)}",
            type=type,
            subtype=subtype,
            description=description,
            confidence=0.8,
            evidence=evidence or ["test evidence"],
            suggested_action="Test action",
        )


class TestIssueTemplate(unittest.TestCase):
    """Test cases for IssueTemplate system."""

    def test_render_code_improvement_template(self):
        """Should render code improvement template correctly."""
        template = IssueTemplate.get_template("code_improvement")
        pattern = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed null pointer exception in user validation",
            confidence=0.95,
            evidence=["before/after code", "test results"],
            suggested_action="Apply fix to similar validation patterns",
        )

        title, body = template.render(pattern)

        self.assertIn("Code Improvement", title)
        self.assertIn("null pointer exception", title)
        self.assertIn("## Summary", body)
        self.assertIn("bug_fix", body)
        self.assertIn("before/after code", body)
        self.assertIn("Apply fix", body)

    def test_render_prompt_improvement_template(self):
        """Should render prompt improvement template correctly."""
        template = IssueTemplate.get_template("prompt_improvement")
        pattern = ImprovementPattern(
            id="test-456",
            type="prompt_improvement",
            subtype="clarity",
            description="Improved prompt clarity for API documentation requests",
            confidence=0.85,
            evidence=["user feedback", "improved response quality"],
            suggested_action="Create clearer prompt templates",
        )

        title, body = template.render(pattern)

        self.assertIn("Prompt Improvement", title)
        self.assertIn("clarity", title)
        self.assertIn("## Prompt Analysis", body)
        self.assertIn("clarity", body)
        self.assertIn("user feedback", body)
        self.assertIn("templates", body)

    def test_render_system_fix_template(self):
        """Should render system fix template correctly."""
        template = IssueTemplate.get_template("system_fix")
        pattern = ImprovementPattern(
            id="test-789",
            type="system_fix",
            subtype="memory",
            description="Implemented memory optimization using streaming",
            confidence=0.9,
            evidence=["memory profiling", "75% reduction in usage"],
            suggested_action="Apply streaming pattern to similar operations",
        )

        title, body = template.render(pattern)

        self.assertIn("System Fix", title)
        self.assertIn("memory optimization", title)
        self.assertIn("## System Issue", body)
        self.assertIn("memory", body)
        self.assertIn("75% reduction", body)
        self.assertIn("streaming pattern", body)

    def test_render_with_sanitization(self):
        """Should sanitize sensitive content in templates."""
        template = IssueTemplate.get_template("code_improvement")
        pattern = ImprovementPattern(
            id="test-sanitize",
            type="code_improvement",
            subtype="security",
            description="Fixed password leak: removed password='secret123' from config",  # pragma: allowlist secret
            confidence=0.9,
            evidence=["api_key=abc123def", "token xyz789"],
            suggested_action="Audit similar configurations",
        )

        title, body = template.render(pattern)

        # Title should be sanitized
        self.assertNotIn("secret123", title)
        self.assertIn("password leak", title)

        # Body should be sanitized
        self.assertNotIn("secret123", body)
        self.assertNotIn("abc123def", body)  # pragma: allowlist secret
        self.assertNotIn("xyz789", body)
        self.assertIn("[REDACTED]", body)

    def test_get_unknown_template(self):
        """Should return default template for unknown types."""
        template = IssueTemplate.get_template("unknown_type")
        self.assertIsNotNone(template)
        self.assertEqual(template.template_type, "generic")


class TestGitHubIssueCreator(unittest.TestCase):
    """Test cases for GitHubIssueCreator."""

    def setUp(self):
        """Set up test fixtures."""
        self.creator = GitHubIssueCreator(
            github_token="test_token", repo_owner="test_owner", repo_name="test_repo"
        )

    @patch("requests.post")
    def test_create_issue_success(self, mock_post):
        """Should create GitHub issue successfully."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test_owner/test_repo/issues/123",
            "title": "Test Issue",
        }
        mock_post.return_value = mock_response

        result = self.creator.create_issue(
            title="Test Issue", body="Test body", labels=["improvement"]
        )

        self.assertTrue(result.success)
        self.assertEqual(result.issue_number, 123)
        self.assertEqual(result.issue_url, "https://github.com/test_owner/test_repo/issues/123")

    @patch("requests.post")
    def test_create_issue_api_error(self, mock_post):
        """Should handle GitHub API errors."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("Forbidden")
        mock_post.return_value = mock_response

        result = self.creator.create_issue(title="Test Issue", body="Test body")

        self.assertFalse(result.success)
        self.assertIn("Forbidden", result.error_message or "")

    def test_create_issue_no_credentials(self):
        """Should handle missing credentials gracefully."""
        creator = GitHubIssueCreator()

        result = creator.create_issue(title="Test Issue", body="Test body")

        self.assertFalse(result.success)
        self.assertIn("credentials", (result.error_message or "").lower())

    @patch("requests.post")
    def test_create_issue_with_labels(self, mock_post):
        """Should include labels in issue creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 123, "html_url": "test_url"}
        mock_post.return_value = mock_response

        self.creator.create_issue(
            title="Test Issue", body="Test body", labels=["bug", "improvement", "auto-generated"]
        )

        # Verify labels were included in request
        call_args = mock_post.call_args[1]
        data = json.loads(call_args["data"])
        self.assertEqual(data["labels"], ["bug", "improvement", "auto-generated"])


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter."""

    def test_daily_limit_enforcement(self):
        """Should enforce daily rate limits."""
        limiter = RateLimiter(daily_limit=2, hourly_limit=10)

        # First two requests should be allowed
        self.assertTrue(limiter.can_make_request())
        limiter.record_request()

        self.assertTrue(limiter.can_make_request())
        limiter.record_request()

        # Third request should be blocked
        self.assertFalse(limiter.can_make_request())

    def test_hourly_limit_enforcement(self):
        """Should enforce hourly rate limits."""
        limiter = RateLimiter(daily_limit=100, hourly_limit=2)

        # First two requests should be allowed
        self.assertTrue(limiter.can_make_request())
        limiter.record_request()

        self.assertTrue(limiter.can_make_request())
        limiter.record_request()

        # Third request should be blocked
        self.assertFalse(limiter.can_make_request())

    def test_rate_limit_reset(self):
        """Should reset rate limits after time window."""
        limiter = RateLimiter(daily_limit=1, hourly_limit=1)

        # Use up the limit
        self.assertTrue(limiter.can_make_request())
        limiter.record_request()
        self.assertFalse(limiter.can_make_request())

        # Manually reset for testing
        limiter.reset_limits()

        # Should be allowed again
        self.assertTrue(limiter.can_make_request())

    def test_get_rate_limit_status(self):
        """Should provide rate limit status information."""
        limiter = RateLimiter(daily_limit=5, hourly_limit=2)

        # Make some requests
        limiter.record_request()
        limiter.record_request()

        status = limiter.get_rate_limit_status()
        self.assertEqual(status["daily_remaining"], 3)
        self.assertEqual(status["hourly_remaining"], 0)
        self.assertFalse(status["can_make_request"])


class TestIssueCreationResult(unittest.TestCase):
    """Test cases for IssueCreationResult data model."""

    def test_success_result_creation(self):
        """Should create successful result."""
        result = IssueCreationResult(
            success=True,
            issue_number=123,
            issue_url="https://github.com/test/repo/issues/123",
            title="Test Issue",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.issue_number, 123)
        self.assertIsNone(result.error_message)

    def test_failure_result_creation(self):
        """Should create failure result."""
        result = IssueCreationResult(success=False, error_message="API Error occurred")

        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "API Error occurred")
        self.assertIsNone(result.issue_number)

    def test_result_to_dict(self):
        """Should convert result to dictionary."""
        result = IssueCreationResult(
            success=True, issue_number=123, issue_url="test_url", title="Test Title"
        )

        result_dict = result.to_dict()
        self.assertEqual(result_dict["success"], True)
        self.assertEqual(result_dict["issue_number"], 123)
        self.assertEqual(result_dict["issue_url"], "test_url")


if __name__ == "__main__":
    unittest.main()
