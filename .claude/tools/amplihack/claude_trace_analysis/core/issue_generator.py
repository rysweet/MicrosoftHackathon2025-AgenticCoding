"""Issue generator for creating GitHub issues from improvement patterns.

This module creates GitHub issues with:
- Template-based issue generation
- Content sanitization for security
- Rate limiting to prevent API abuse
- Comprehensive error handling
- GitHub API integration with proper authentication
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Optional imports for GitHub integration
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    requests = None  # type: ignore
    HAS_REQUESTS = False

from .pattern_extractor import ImprovementPattern
from .security import EnhancedSecretDetector, GitHubTokenValidator, SecurityEvent, security_logger


@dataclass
class IssueCreationResult:
    """Result of GitHub issue creation.

    Attributes:
        success: Whether issue creation succeeded
        issue_number: GitHub issue number (if successful)
        issue_url: GitHub issue URL (if successful)
        title: Issue title that was created
        error_message: Error description (if failed)
        metadata: Additional creation metadata
    """

    success: bool
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    title: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary representation of the result
        """
        return {
            "success": self.success,
            "issue_number": self.issue_number,
            "issue_url": self.issue_url,
            "title": self.title,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class ContentSanitizer:
    """Sanitizes content to prevent sensitive information disclosure."""

    def __init__(self):
        # Use enhanced secret detector for comprehensive security
        self.secret_detector = EnhancedSecretDetector()

    def sanitize(self, content: str) -> str:
        """Sanitize content by redacting sensitive information.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content with sensitive information redacted
        """
        if not content:
            return content

        sanitized, detection_counts = self.secret_detector.detect_and_redact(content)

        # Log summary if secrets were detected
        if detection_counts:
            total_redacted = sum(detection_counts.values())
            security_logger.log_event(
                SecurityEvent(
                    event_type="content_sanitization",
                    severity="medium",
                    message=f"Sanitized content: {total_redacted} secrets redacted",
                    metadata={"detection_counts": detection_counts},
                )
            )

        return sanitized


class IssueTemplate:
    """Template system for generating GitHub issues from improvement patterns."""

    def __init__(self, template_type: str, title_template: str, body_template: str):
        """Initialize issue template.

        Args:
            template_type: Type of template (code_improvement, prompt_improvement, etc.)
            title_template: Template for issue title
            body_template: Template for issue body
        """
        self.template_type = template_type
        self.title_template = title_template
        self.body_template = body_template
        self.sanitizer = ContentSanitizer()

    def render(self, pattern: ImprovementPattern) -> Tuple[str, str]:
        """Render template with pattern data.

        Args:
            pattern: Improvement pattern to render

        Returns:
            Tuple of (title, body) for the GitHub issue
        """
        # Sanitize pattern data
        sanitized_description = self.sanitizer.sanitize(pattern.description)
        sanitized_evidence = [self.sanitizer.sanitize(evidence) for evidence in pattern.evidence]
        sanitized_action = self.sanitizer.sanitize(pattern.suggested_action)

        # Render title
        title = self.title_template.format(
            type=pattern.type.replace("_", " ").title(),
            subtype=pattern.subtype,
            description=sanitized_description[:100],  # Limit title length
        )

        # Render body
        evidence_list = "\n".join(f"- {evidence}" for evidence in sanitized_evidence)

        body = self.body_template.format(
            type=pattern.type.replace("_", " ").title(),
            subtype=pattern.subtype,
            description=sanitized_description,
            confidence=pattern.confidence,
            evidence=evidence_list,
            suggested_action=sanitized_action,
            pattern_id=pattern.id,
            timestamp=datetime.now().isoformat(),
            entry_count=len(pattern.source_entries),
        )

        return title, body

    @classmethod
    def get_template(cls, pattern_type: str) -> "IssueTemplate":
        """Get appropriate template for pattern type.

        Args:
            pattern_type: Type of improvement pattern

        Returns:
            IssueTemplate instance for the pattern type
        """
        # Simplified unified template
        template = """## {type}

**Subtype**: {subtype} | **Confidence**: {confidence:.2f}

{description}

## Evidence
{evidence}

## Suggested Action
{suggested_action}

**Pattern ID**: `{pattern_id}` | **Detected**: {timestamp} | **Entries**: {entry_count}

---
*Auto-generated from claude-trace analysis*
"""

        templates = {
            "code_improvement": cls("code_improvement", "{type}: {description}", template),
            "prompt_improvement": cls("prompt_improvement", "{type}: {description}", template),
            "system_fix": cls("system_fix", "{type}: {description}", template),
        }

        return templates.get(pattern_type, templates["code_improvement"])  # Default fallback


class RateLimiter:
    """Rate limiting for GitHub API requests."""

    def __init__(self, daily_limit: int = 50, hourly_limit: int = 10):
        """Initialize rate limiter.

        Args:
            daily_limit: Maximum requests per day
            hourly_limit: Maximum requests per hour
        """
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit

        # Request tracking
        self.daily_requests = []
        self.hourly_requests = []

    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits.

        Returns:
            True if request is allowed
        """
        now = datetime.now()

        # Clean old requests
        self._cleanup_old_requests(now)

        # Check limits
        return (
            len(self.daily_requests) < self.daily_limit
            and len(self.hourly_requests) < self.hourly_limit
        )

    def record_request(self):
        """Record a request for rate limiting."""
        now = datetime.now()
        self.daily_requests.append(now)
        self.hourly_requests.append(now)

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        now = datetime.now()
        self._cleanup_old_requests(now)

        return {
            "daily_remaining": self.daily_limit - len(self.daily_requests),
            "hourly_remaining": self.hourly_limit - len(self.hourly_requests),
            "can_make_request": self.can_make_request(),
            "daily_reset_time": (now + timedelta(days=1)).replace(hour=0, minute=0, second=0),
            "hourly_reset_time": (now + timedelta(hours=1)).replace(minute=0, second=0),
        }

    def reset_limits(self):
        """Reset rate limits (for testing purposes)."""
        self.daily_requests.clear()
        self.hourly_requests.clear()

    def _cleanup_old_requests(self, now: datetime):
        """Remove old requests outside the time windows."""
        # Remove requests older than 24 hours
        day_ago = now - timedelta(days=1)
        self.daily_requests = [req for req in self.daily_requests if req > day_ago]

        # Remove requests older than 1 hour
        hour_ago = now - timedelta(hours=1)
        self.hourly_requests = [req for req in self.hourly_requests if req > hour_ago]


class GitHubIssueCreator:
    """Creates GitHub issues via API."""

    def __init__(
        self, github_token: Optional[str] = None, repo_owner: str = "", repo_name: str = ""
    ):
        """Initialize GitHub issue creator.

        Args:
            github_token: GitHub API token
            repo_owner: Repository owner
            repo_name: Repository name
        """
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = "https://api.github.com"

        # Initialize security components
        self.token_validator = GitHubTokenValidator()
        self._token_validated = False
        self._validation_result = None

    def create_issue(
        self, title: str, body: str, labels: Optional[List[str]] = None
    ) -> IssueCreationResult:
        """Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body content
            labels: Optional list of labels

        Returns:
            IssueCreationResult with creation status
        """
        if not HAS_REQUESTS:
            return IssueCreationResult(
                success=False,
                error_message="GitHub integration unavailable (requests module not installed)",
            )

        if not self.github_token or not self.repo_owner or not self.repo_name:
            return IssueCreationResult(
                success=False,
                error_message="GitHub credentials or repository information not configured",
            )

        # Validate GitHub token if not already validated
        if not self._token_validated:
            self._validation_result = self.token_validator.validate_token(
                self.github_token, {"issues", "repo"}
            )
            self._token_validated = True

        # Check token validation result
        if not self._validation_result or not self._validation_result.is_valid:
            error_msg = (
                self._validation_result.error_message
                if self._validation_result
                else "Token validation failed"
            )
            security_logger.log_authentication_event(False, f"Token validation failed: {error_msg}")
            return IssueCreationResult(
                success=False,
                error_message=f"GitHub token validation failed: {error_msg}",
            )

        if not self._validation_result.has_required_permissions:
            security_logger.log_authentication_event(
                False, f"Token lacks required permissions: {self._validation_result.scopes}"
            )
            return IssueCreationResult(
                success=False,
                error_message=f"GitHub token lacks required permissions. Available scopes: {self._validation_result.scopes}",
            )

        try:
            # Prepare request
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            data: Dict[str, Any] = {"title": title, "body": body}

            if labels:
                data["labels"] = labels

            # Make request
            if not HAS_REQUESTS or requests is None:
                raise RuntimeError("requests module is required for GitHub integration")

            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)

            # Log the API call
            security_logger.log_api_call(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues",
                response.status_code < 400,
                response.status_code,
            )

            response.raise_for_status()

            # Parse response
            issue_data = response.json()

            result = IssueCreationResult(
                success=True,
                issue_number=issue_data["number"],
                issue_url=issue_data["html_url"],
                title=issue_data["title"],
                metadata={
                    "created_at": issue_data.get("created_at"),
                    "state": issue_data.get("state", "open"),
                },
            )

            # Log successful issue creation
            security_logger.log_event(
                SecurityEvent(
                    event_type="github_issue_created",
                    severity="low",
                    message=f"Successfully created GitHub issue #{issue_data['number']}",
                    metadata={
                        "issue_number": issue_data["number"],
                        "issue_url": issue_data["html_url"],
                        "repo": f"{self.repo_owner}/{self.repo_name}",
                    },
                )
            )

            return result

        except Exception as e:
            # Log the error
            security_logger.log_event(
                SecurityEvent(
                    event_type="github_issue_creation_failed",
                    severity="medium",
                    message=f"Failed to create GitHub issue: {str(e)}",
                    metadata={
                        "exception_type": type(e).__name__,
                        "repo": f"{self.repo_owner}/{self.repo_name}",
                    },
                )
            )

            return IssueCreationResult(
                success=False,
                error_message=f"GitHub API error: {str(e)}",
                metadata={"exception_type": type(e).__name__},
            )


class IssueGenerator:
    """Main orchestrator for GitHub issue generation from improvement patterns.

    Coordinates template rendering, content sanitization, rate limiting,
    and GitHub API integration to create well-formatted issues.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        repo_owner: str = "",
        repo_name: str = "",
        daily_limit: int = 50,
        hourly_limit: int = 10,
    ):
        """Initialize issue generator.

        Args:
            github_token: GitHub API token
            repo_owner: Repository owner
            repo_name: Repository name
            daily_limit: Maximum issues per day
            hourly_limit: Maximum issues per hour
        """
        self.github_creator = GitHubIssueCreator(github_token, repo_owner, repo_name)
        self.rate_limiter = RateLimiter(daily_limit, hourly_limit)

        # Statistics tracking
        self.generation_stats = {
            "total_attempted": 0,
            "successful_creations": 0,
            "failed_creations": 0,
            "rate_limited": 0,
            "by_type": defaultdict(int),
            "by_error": defaultdict(int),
        }

    def create_issue(self, pattern: ImprovementPattern) -> IssueCreationResult:
        """Create GitHub issue from improvement pattern.

        Args:
            pattern: Improvement pattern to create issue from

        Returns:
            IssueCreationResult with creation status
        """
        self.generation_stats["total_attempted"] += 1
        self.generation_stats["by_type"][pattern.type] += 1

        try:
            # Check rate limits
            if not self.rate_limiter.can_make_request():
                self.generation_stats["rate_limited"] += 1
                return IssueCreationResult(
                    success=False,
                    error_message="Rate limit exceeded - please try again later",
                    metadata={"rate_limit_status": self.rate_limiter.get_rate_limit_status()},
                )

            # Get appropriate template
            template = IssueTemplate.get_template(pattern.type)

            # Render issue content
            title, body = template.render(pattern)

            # Generate labels
            labels = self._generate_labels(pattern)

            # Create issue
            result = self.github_creator.create_issue(title, body, labels)

            # Record request and update stats
            if result.success:
                self.rate_limiter.record_request()
                self.generation_stats["successful_creations"] += 1
            else:
                self.generation_stats["failed_creations"] += 1
                error_type = result.metadata.get("exception_type", "unknown")
                self.generation_stats["by_error"][error_type] += 1

            return result

        except Exception as e:
            self.generation_stats["failed_creations"] += 1
            self.generation_stats["by_error"]["unexpected_error"] += 1

            return IssueCreationResult(
                success=False,
                error_message=f"Unexpected error during issue creation: {str(e)}",
                metadata={"exception_type": type(e).__name__},
            )

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive issue generation statistics.

        Returns:
            Dictionary with generation statistics
        """
        return {
            "total_issues_attempted": self.generation_stats["total_attempted"],
            "successful_creations": self.generation_stats["successful_creations"],
            "failed_creations": self.generation_stats["failed_creations"],
            "rate_limited_requests": self.generation_stats["rate_limited"],
            "success_rate": (
                self.generation_stats["successful_creations"]
                / max(self.generation_stats["total_attempted"], 1)
            ),
            "by_type": dict(self.generation_stats["by_type"]),
            "by_error": dict(self.generation_stats["by_error"]),
            "rate_limit_status": self.rate_limiter.get_rate_limit_status(),
        }

    def _generate_labels(self, pattern: ImprovementPattern) -> List[str]:
        """Generate appropriate labels for the pattern.

        Args:
            pattern: Improvement pattern

        Returns:
            List of GitHub labels
        """
        labels = ["auto-generated"]

        # Type-based labels
        if pattern.type == "code_improvement":
            labels.extend(["enhancement", "code-improvement"])
            if pattern.subtype == "bug_fix":
                labels.append("bug")
            elif pattern.subtype == "security":
                labels.append("security")
            elif pattern.subtype == "performance":
                labels.append("performance")

        elif pattern.type == "prompt_improvement":
            labels.extend(["documentation", "prompt-improvement", "user-experience"])

        elif pattern.type == "system_fix":
            labels.extend(["bug", "system-fix", "reliability"])

        # Confidence-based labels
        if pattern.confidence >= 0.9:
            labels.append("high-confidence")
        elif pattern.confidence >= 0.7:
            labels.append("medium-confidence")
        else:
            labels.append("low-confidence")

        return labels
