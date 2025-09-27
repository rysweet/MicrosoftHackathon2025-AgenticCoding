"""Security utilities for claude-trace analysis system.

This module provides:
- GitHub token validation and permission checking
- Enhanced secret detection patterns
- Security event logging for critical operations
- Authentication hardening
- Content sanitization with security focus
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

# Optional imports for GitHub integration
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    requests = None  # type: ignore
    HAS_REQUESTS = False


@dataclass
class SecurityEvent:
    """Represents a security event for logging."""

    event_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert security event to dictionary."""
        return {
            "event_type": self.event_type,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GitHubTokenValidationResult:
    """Result of GitHub token validation."""

    is_valid: bool
    has_required_permissions: bool
    token_type: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    rate_limit_info: Dict[str, Any] = field(default_factory=dict)


class SecurityLogger:
    """Handles security event logging for critical operations."""

    def __init__(self, logger_name: str = "claude_trace_security"):
        """Initialize security logger.

        Args:
            logger_name: Name for the security logger
        """
        self.logger = logging.getLogger(logger_name)
        self.events: List[SecurityEvent] = []

        # Configure logger if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - SECURITY: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.WARNING)

    def log_event(self, event: SecurityEvent):
        """Log a security event.

        Args:
            event: Security event to log
        """
        self.events.append(event)

        # Log to standard logger based on severity
        log_level = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL,
        }.get(event.severity, logging.WARNING)

        self.logger.log(
            log_level, f"{event.event_type}: {event.message} (metadata: {event.metadata})"
        )

    def log_authentication_event(self, success: bool, details: str):
        """Log authentication-related events.

        Args:
            success: Whether authentication was successful
            details: Additional details about the event
        """
        severity = "medium" if success else "high"
        event_type = "authentication_success" if success else "authentication_failure"

        self.log_event(
            SecurityEvent(
                event_type=event_type,
                severity=severity,
                message=f"GitHub authentication {('succeeded' if success else 'failed')}: {details}",
                metadata={"success": success},
            )
        )

    def log_sensitive_data_detection(self, pattern_type: str, redacted_count: int):
        """Log sensitive data detection and redaction.

        Args:
            pattern_type: Type of sensitive pattern detected
            redacted_count: Number of instances redacted
        """
        self.log_event(
            SecurityEvent(
                event_type="sensitive_data_detected",
                severity="medium",
                message=f"Detected and redacted {redacted_count} instances of {pattern_type}",
                metadata={"pattern_type": pattern_type, "redacted_count": redacted_count},
            )
        )

    def log_api_call(self, endpoint: str, success: bool, status_code: Optional[int] = None):
        """Log API calls for monitoring.

        Args:
            endpoint: API endpoint called
            success: Whether the call was successful
            status_code: HTTP status code if available
        """
        severity = "low" if success else "medium"
        event_type = "api_call_success" if success else "api_call_failure"

        self.log_event(
            SecurityEvent(
                event_type=event_type,
                severity=severity,
                message=f"API call to {endpoint}: {'success' if success else 'failure'}",
                metadata={"endpoint": endpoint, "success": success, "status_code": status_code},
            )
        )

    def get_events_summary(self) -> Dict[str, Any]:
        """Get summary of security events.

        Returns:
            Dictionary with event summary statistics
        """
        if not self.events:
            return {"total_events": 0, "by_severity": {}, "by_type": {}}

        by_severity = {}
        by_type = {}

        for event in self.events:
            by_severity[event.severity] = by_severity.get(event.severity, 0) + 1
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1

        return {
            "total_events": len(self.events),
            "by_severity": by_severity,
            "by_type": by_type,
            "latest_event": self.events[-1].to_dict() if self.events else None,
        }


class EnhancedSecretDetector:
    """Enhanced secret detection with comprehensive patterns."""

    def __init__(self):
        """Initialize with comprehensive secret detection patterns."""
        self.patterns = self._build_detection_patterns()
        self.security_logger = SecurityLogger("secret_detector")

    def _build_detection_patterns(self) -> Dict[str, re.Pattern]:
        """Build comprehensive secret detection patterns.

        Returns:
            Dictionary mapping pattern names to compiled regex patterns
        """
        return {
            # GitHub tokens
            "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b"),
            "github_classic_token": re.compile(r"\b[0-9a-f]{40}\b"),
            # API keys and tokens
            "api_key": re.compile(
                r"\b(?:api[_-]?key|token|secret)[_-]?(?:=|:|\s+)['\"]?([A-Za-z0-9+/=]{20,})['\"]?",
                re.IGNORECASE,
            ),
            "bearer_token": re.compile(r"\bBearer\s+([A-Za-z0-9+/=]{20,})", re.IGNORECASE),
            # AWS credentials
            "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            "aws_secret_key": re.compile(r"\b[A-Za-z0-9+/]{40}\b"),
            # Database connections
            "db_connection": re.compile(
                r"\b(?:postgres|mysql|mongodb)://[^@\s]+:[^@\s]+@[^/\s]+", re.IGNORECASE
            ),
            # Email addresses
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            # Private IP addresses
            "private_ip": re.compile(
                r"\b(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9]{1,3}\.[0-9]{1,3}\b"
            ),
            # SSH keys
            "ssh_key": re.compile(
                r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE
            ),
            # JWT tokens
            "jwt_token": re.compile(r"\bey[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]*\b"),
            # Generic secrets
            "generic_secret": re.compile(
                r"\b(?:password|passwd|pwd|secret|key)\s*[=:]\s*['\"]?([A-Za-z0-9+/=@#$%^&*!]{8,})['\"]?",
                re.IGNORECASE,
            ),
            # Long hex strings (likely secrets)
            "hex_string": re.compile(r"\b[a-fA-F0-9]{32,}\b"),
            # Base64 encoded data (likely secrets)
            "base64_secret": re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b"),
        }

    def detect_and_redact(self, content: str) -> Tuple[str, Dict[str, int]]:
        """Detect and redact secrets from content.

        Args:
            content: Content to scan and redact

        Returns:
            Tuple of (sanitized_content, detection_counts)
        """
        if not content:
            return content, {}

        sanitized = content
        detection_counts = {}

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(sanitized)
            if matches:
                count = len(matches)
                detection_counts[pattern_name] = count
                sanitized = pattern.sub("[REDACTED]", sanitized)

                # Log the detection
                self.security_logger.log_sensitive_data_detection(pattern_name, count)

        return sanitized, detection_counts

    def scan_for_secrets(self, content: str) -> Dict[str, List[str]]:
        """Scan content for secrets without redacting.

        Args:
            content: Content to scan

        Returns:
            Dictionary mapping pattern names to lists of matches
        """
        if not content:
            return {}

        detected_secrets = {}

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(content)
            if matches:
                detected_secrets[pattern_name] = matches

        return detected_secrets


class GitHubTokenValidator:
    """Validates GitHub tokens and checks permissions."""

    def __init__(self):
        """Initialize GitHub token validator."""
        self.security_logger = SecurityLogger("github_validator")

    def validate_token(
        self, token: str, required_permissions: Optional[Set[str]] = None
    ) -> GitHubTokenValidationResult:
        """Validate GitHub token format and permissions.

        Args:
            token: GitHub token to validate
            required_permissions: Set of required permissions (repo, issues, etc.)

        Returns:
            GitHubTokenValidationResult with validation details
        """
        if not token:
            result = GitHubTokenValidationResult(
                is_valid=False,
                has_required_permissions=False,
                error_message="Token is empty or None",
            )
            self.security_logger.log_authentication_event(False, "Empty token provided")
            return result

        # Basic format validation
        if not self._validate_token_format(token):
            result = GitHubTokenValidationResult(
                is_valid=False,
                has_required_permissions=False,
                error_message="Token format is invalid",
            )
            self.security_logger.log_authentication_event(False, "Invalid token format")
            return result

        # API validation if requests available
        if HAS_REQUESTS and requests:
            return self._validate_token_with_api(token, required_permissions)
        else:
            # Basic validation without API
            result = GitHubTokenValidationResult(
                is_valid=True,  # Format is valid
                has_required_permissions=True,  # Can't check without API
                token_type="unknown",
                error_message="Cannot validate permissions without requests module",
            )
            self.security_logger.log_authentication_event(
                True, "Token format valid, cannot check permissions"
            )
            return result

    def _validate_token_format(self, token: str) -> bool:
        """Validate GitHub token format.

        Args:
            token: Token to validate

        Returns:
            True if format is valid
        """
        # GitHub personal access tokens (new format)
        if re.match(r"^ghp_[A-Za-z0-9]{36}$", token):
            return True

        # GitHub app tokens
        if re.match(r"^ghs_[A-Za-z0-9]{36}$", token):
            return True

        # GitHub OAuth tokens
        if re.match(r"^gho_[A-Za-z0-9]{36}$", token):
            return True

        # GitHub user tokens
        if re.match(r"^ghu_[A-Za-z0-9]{36}$", token):
            return True

        # GitHub refresh tokens
        if re.match(r"^ghr_[A-Za-z0-9]{36}$", token):
            return True

        # Classic personal access tokens (40 character hex)
        if re.match(r"^[a-f0-9]{40}$", token):
            return True

        return False

    def _validate_token_with_api(
        self, token: str, required_permissions: Optional[Set[str]] = None
    ) -> GitHubTokenValidationResult:
        """Validate token using GitHub API.

        Args:
            token: Token to validate
            required_permissions: Required permissions to check

        Returns:
            GitHubTokenValidationResult with full validation details
        """
        # Ensure requests is available (this method should only be called when it is)
        if not HAS_REQUESTS or requests is None:
            return GitHubTokenValidationResult(
                is_valid=False,
                has_required_permissions=False,
                error_message="Requests module not available for API validation",
            )

        try:
            # Test token with user endpoint
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get("https://api.github.com/user", headers=headers, timeout=30)

            if response.status_code == 401:
                result = GitHubTokenValidationResult(
                    is_valid=False,
                    has_required_permissions=False,
                    error_message="Token authentication failed",
                )
                self.security_logger.log_authentication_event(False, "API authentication failed")
                return result

            response.raise_for_status()

            # Extract scopes from headers
            scopes_header = response.headers.get("X-OAuth-Scopes", "")
            scopes = [scope.strip() for scope in scopes_header.split(",") if scope.strip()]

            # Extract rate limit info
            rate_limit_info = {
                "limit": response.headers.get("X-RateLimit-Limit"),
                "remaining": response.headers.get("X-RateLimit-Remaining"),
                "reset": response.headers.get("X-RateLimit-Reset"),
            }

            # Check required permissions
            has_required_permissions = True
            if required_permissions:
                has_required_permissions = self._check_permissions(scopes, required_permissions)

            result = GitHubTokenValidationResult(
                is_valid=True,
                has_required_permissions=has_required_permissions,
                token_type="personal_access_token",
                scopes=scopes,
                rate_limit_info=rate_limit_info,
            )

            self.security_logger.log_authentication_event(
                True, f"Token validated successfully with scopes: {scopes}"
            )
            self.security_logger.log_api_call("/user", True, response.status_code)

            return result

        except Exception as e:
            result = GitHubTokenValidationResult(
                is_valid=False,
                has_required_permissions=False,
                error_message=f"API validation failed: {str(e)}",
            )
            self.security_logger.log_authentication_event(False, f"API validation error: {str(e)}")
            return result

    def _check_permissions(self, scopes: List[str], required_permissions: Set[str]) -> bool:
        """Check if token has required permissions.

        Args:
            scopes: Token scopes
            required_permissions: Required permissions

        Returns:
            True if all required permissions are satisfied
        """
        # Map permission names to scope requirements
        permission_mapping = {
            "repo": ["repo"],
            "issues": ["repo", "public_repo"],
            "read": ["repo", "public_repo", "read:repo"],
            "write": ["repo"],
        }

        for permission in required_permissions:
            required_scopes = permission_mapping.get(permission, [permission])
            if not any(scope in scopes for scope in required_scopes):
                return False

        return True


# Global security logger instance
security_logger = SecurityLogger()
