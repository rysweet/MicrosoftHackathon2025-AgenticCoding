"""Configuration management for claude-trace analysis system.

Provides centralized configuration with:
- Environment variable support
- Default settings
- Validation
- GitHub integration configuration
- Security settings
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SecurityConfig:
    """Security configuration."""

    max_file_size_mb: int = 100
    max_entries_per_file: int = 10000
    enable_content_sanitization: bool = True


@dataclass
class GitHubConfig:
    """GitHub integration configuration."""

    token: Optional[str] = None
    repo_owner: str = ""
    repo_name: str = ""
    daily_issue_limit: int = 50
    hourly_issue_limit: int = 10

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.repo_owner and self.repo_name)


@dataclass
class AnalysisConfig:
    """Analysis configuration."""

    enable_code_improvement_analysis: bool = True
    enable_prompt_improvement_analysis: bool = True
    enable_system_fix_analysis: bool = True
    similarity_threshold: float = 0.8
    temporal_window_minutes: int = 60


class TraceConfig:
    """Main configuration class for claude-trace analysis system.

    Provides centralized configuration management with environment variable
    support and validation.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration.

        Args:
            config_dict: Optional configuration dictionary to override defaults
        """
        # Load from environment variables first
        self._load_from_environment()

        # Override with provided config
        if config_dict:
            self._load_from_dict(config_dict)

        # Validate configuration
        self._validate_config()

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        self.security = SecurityConfig(
            max_file_size_mb=int(os.getenv("TRACE_MAX_FILE_SIZE_MB", "100")),
            max_entries_per_file=int(os.getenv("TRACE_MAX_ENTRIES", "10000")),
            enable_content_sanitization=os.getenv("TRACE_ENABLE_SANITIZATION", "true").lower()
            == "true",
        )

        self.github = GitHubConfig(
            token=os.getenv("GITHUB_TOKEN"),
            repo_owner=os.getenv("GITHUB_REPO_OWNER", ""),
            repo_name=os.getenv("GITHUB_REPO_NAME", ""),
            daily_issue_limit=int(os.getenv("GITHUB_DAILY_LIMIT", "50")),
            hourly_issue_limit=int(os.getenv("GITHUB_HOURLY_LIMIT", "10")),
        )

        self.analysis = AnalysisConfig(
            enable_code_improvement_analysis=os.getenv("ANALYSIS_ENABLE_CODE", "true").lower()
            == "true",
            enable_prompt_improvement_analysis=os.getenv("ANALYSIS_ENABLE_PROMPT", "true").lower()
            == "true",
            enable_system_fix_analysis=os.getenv("ANALYSIS_ENABLE_SYSTEM", "true").lower()
            == "true",
            similarity_threshold=float(os.getenv("ANALYSIS_SIMILARITY_THRESHOLD", "0.8")),
            temporal_window_minutes=int(os.getenv("ANALYSIS_TEMPORAL_WINDOW", "60")),
        )

    def _load_from_dict(self, config_dict: Dict[str, Any]):
        """Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary
        """
        # Security overrides
        if "security" in config_dict:
            security_config = config_dict["security"]
            for key, value in security_config.items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)

        # GitHub overrides
        if "github" in config_dict:
            github_config = config_dict["github"]
            for key, value in github_config.items():
                if hasattr(self.github, key):
                    setattr(self.github, key, value)

        # Analysis overrides
        if "analysis" in config_dict:
            analysis_config = config_dict["analysis"]
            for key, value in analysis_config.items():
                if hasattr(self.analysis, key):
                    setattr(self.analysis, key, value)

    def _validate_config(self):
        """Validate configuration settings."""
        if self.security.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if self.security.max_entries_per_file <= 0:
            raise ValueError("max_entries_per_file must be positive")
        if self.github.daily_issue_limit <= 0:
            raise ValueError("daily_issue_limit must be positive")
        if self.github.hourly_issue_limit <= 0:
            raise ValueError("hourly_issue_limit must be positive")
        if not (0.0 <= self.analysis.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        if self.analysis.temporal_window_minutes <= 0:
            raise ValueError("temporal_window_minutes must be positive")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path.

        Args:
            key: Configuration key (e.g., 'github.token', 'security.max_file_size_mb')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            parts = key.split(".")
            value = self

            for part in parts:
                value = getattr(value, part)

            return value
        except AttributeError:
            return default
