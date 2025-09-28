"""Comprehensive test suite for amplihack error handling system."""

import threading
import time
from unittest.mock import patch

import pytest

from amplihack.errors import (
    AmplihackError,
    ConfigurationError,
    ErrorLogger,
    NetworkError,
    ProcessError,
    SecurityError,
    TimeoutError,
    ValidationError,
    clear_correlation_id,
    format_error_message,
    get_correlation_id,
    sanitize_error_message,
    sanitize_path,
    set_correlation_id,
)


class TestAmplihackErrorBase:
    """Test base error functionality."""

    def test_basic_error_creation(self):
        """Test basic error creation with all parameters."""
        correlation_id = "test-corr-123"
        context = {"key": "value", "number": 42}
        cause = ValueError("original error")

        error = AmplihackError(
            message="Test error",
            error_code="TEST_001",
            correlation_id=correlation_id,
            context=context,
            cause=cause,
        )

        assert str(error) == "Test error"
        assert error.error_code == "TEST_001"
        assert error.correlation_id == correlation_id
        assert error.context == context
        assert error.cause is cause

    def test_error_to_dict(self):
        """Test error dictionary conversion."""
        error = AmplihackError(
            message="Test error",
            error_code="TEST_001",
            correlation_id="corr-123",
            context={"test": True},
            cause=ValueError("cause"),
        )

        error_dict = error.to_dict()

        assert error_dict["type"] == "AmplihackError"
        assert error_dict["message"] == "Test error"
        assert error_dict["error_code"] == "TEST_001"
        assert error_dict["correlation_id"] == "corr-123"
        assert error_dict["context"] == {"test": True}
        assert error_dict["cause"] == "cause"

    def test_error_without_optional_params(self):
        """Test error creation with minimal parameters."""
        error = AmplihackError("Simple error")

        assert str(error) == "Simple error"
        assert error.error_code is None
        assert error.correlation_id is None
        assert error.context == {}
        assert error.cause is None


class TestSpecificErrorTypes:
    """Test specific error type functionality."""

    def test_validation_error(self):
        """Test ValidationError specific functionality."""
        error = ValidationError(
            message="Field validation failed",
            field="username",
            value="test@user",
            correlation_id="val-123",
        )

        assert error.field == "username"
        assert error.value == "test@user"
        assert error.context["field"] == "username"
        assert error.context["value_type"] == "str"

    def test_configuration_error(self):
        """Test ConfigurationError specific functionality."""
        error = ConfigurationError(
            message="Config missing",
            config_key="api_key",
            config_file="/path/to/config.yml",
            correlation_id="conf-123",
        )

        assert error.config_key == "api_key"
        assert error.config_file == "/path/to/config.yml"
        assert error.context["config_key"] == "api_key"
        # File path should be sanitized
        assert "config_file" in error.context

    def test_process_error(self):
        """Test ProcessError specific functionality."""
        error = ProcessError(
            message="Command failed",
            command="ls -la",
            return_code=1,
            stdout="some output",
            stderr="error output",
            correlation_id="proc-123",
        )

        assert error.command == "ls -la"
        assert error.return_code == 1
        assert error.stdout == "some output"
        assert error.stderr == "error output"
        assert "command" in error.context
        assert error.context["return_code"] == 1

    def test_network_error(self):
        """Test NetworkError specific functionality."""
        error = NetworkError(
            message="Request failed",
            url="https://api.example.com/data",
            status_code=404,
            timeout=30.0,
            correlation_id="net-123",
        )

        assert error.url == "https://api.example.com/data"
        assert error.status_code == 404
        assert error.timeout == 30.0
        assert error.context["status_code"] == 404
        assert error.context["timeout"] == 30.0

    def test_security_error(self):
        """Test SecurityError specific functionality."""
        error = SecurityError(
            message="Path traversal detected",
            violation_type="path_traversal",
            resource="/etc/passwd",
            correlation_id="sec-123",
        )

        assert error.violation_type == "path_traversal"
        assert error.resource == "/etc/passwd"
        assert error.context["violation_type"] == "path_traversal"

    def test_timeout_error(self):
        """Test TimeoutError specific functionality."""
        error = TimeoutError(
            message="Operation timed out",
            timeout_duration=30.0,
            operation="database_query",
            correlation_id="timeout-123",
        )

        assert error.timeout_duration == 30.0
        assert error.operation == "database_query"
        assert error.context["timeout_duration"] == 30.0
        assert error.context["operation"] == "database_query"


class TestCorrelationIds:
    """Test correlation ID functionality."""

    def setup_method(self):
        """Clear correlation ID before each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Clear correlation ID after each test."""
        clear_correlation_id()

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        correlation_id = set_correlation_id("test-123")

        assert correlation_id == "test-123"
        assert get_correlation_id() == "test-123"

    def test_auto_generate_correlation_id(self):
        """Test auto-generation of correlation ID."""
        correlation_id = set_correlation_id()

        assert correlation_id is not None
        assert len(correlation_id) == 16  # 8 bytes hex = 16 chars
        assert get_correlation_id() == correlation_id

    def test_correlation_id_thread_isolation(self):
        """Test that correlation IDs are isolated per thread."""
        set_correlation_id("main-thread")
        thread_corr_id = None

        def thread_function():
            nonlocal thread_corr_id
            thread_corr_id = set_correlation_id("thread-123")
            assert get_correlation_id() == "thread-123"

        thread = threading.Thread(target=thread_function)
        thread.start()
        thread.join()

        # Main thread should still have its correlation ID
        assert get_correlation_id() == "main-thread"
        assert thread_corr_id == "thread-123"

    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

        clear_correlation_id()
        assert get_correlation_id() is None


class TestErrorLogger:
    """Test error logging functionality."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()
        self.logger = ErrorLogger("test.logger")

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_log_error_basic(self):
        """Test basic error logging."""
        error = AmplihackError("Test error")

        with patch.object(self.logger.logger, "log") as mock_log:
            correlation_id = self.logger.log_error(error)

            assert correlation_id is not None
            assert len(correlation_id) == 16
            mock_log.assert_called_once()

    def test_log_error_with_correlation_id(self):
        """Test logging with specific correlation ID."""
        error = AmplihackError("Test error")
        test_corr_id = "test-correlation-123"

        with patch.object(self.logger.logger, "log") as mock_log:
            returned_id = self.logger.log_error(error, correlation_id=test_corr_id)

            assert returned_id == test_corr_id
            mock_log.assert_called_once()

    def test_log_retry_attempt(self):
        """Test retry attempt logging."""
        error = ProcessError("Command failed")

        with patch.object(self.logger.logger, "warning") as mock_warning:
            self.logger.log_retry_attempt(2, 3, error, 2.5, "test-corr")

            mock_warning.assert_called_once()
            args, kwargs = mock_warning.call_args
            assert "Retry attempt 2/3" in args[0]

    def test_log_retry_exhausted(self):
        """Test retry exhausted logging."""
        error = NetworkError("Connection failed")

        with patch.object(self.logger.logger, "error") as mock_error:
            self.logger.log_retry_exhausted(3, error, "test-corr")

            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            assert "Retry exhausted after 3 attempts" in args[0]


class TestSecurityFunctions:
    """Test security sanitization functions."""

    def test_sanitize_api_keys(self):
        """Test API key sanitization."""
        message = "Error: api_key=sk-1234567890abcdef failed to authenticate"
        sanitized = sanitize_error_message(message)

        assert "sk-1234567890abcdef" not in sanitized
        assert "api_key=***" in sanitized

    def test_sanitize_bearer_tokens(self):
        """Test Bearer token sanitization."""
        message = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = sanitize_error_message(message)

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "Bearer ***" in sanitized

    def test_sanitize_file_paths(self):
        """Test file path sanitization."""
        message = "Error reading /Users/john/secret/config.yml"
        sanitized = sanitize_error_message(message)

        assert "/Users/john" not in sanitized
        assert "/Users/***" in sanitized

    def test_sanitize_urls_with_credentials(self):
        """Test URL credential sanitization."""
        message = "Failed to connect to https://user:pass@api.example.com/endpoint"  # pragma: allowlist secret
        sanitized = sanitize_error_message(message)

        assert "user:pass" not in sanitized
        assert "***:***@api.example.com" in sanitized

    def test_sanitize_email_addresses(self):
        """Test email address sanitization."""
        message = "User john.doe@company.com not found"
        sanitized = sanitize_error_message(message)

        assert "john.doe@company.com" not in sanitized
        assert "***@***.***" in sanitized

    def test_sanitize_path_function(self):
        """Test path sanitization function."""
        path = "/Users/john/Documents/secret.txt"
        sanitized = sanitize_path(path)

        assert "/Users/john" not in sanitized
        assert "/Users/***" in sanitized or "~/Documents/secret.txt" in sanitized

    def test_sanitize_preserves_structure(self):
        """Test that sanitization preserves message structure."""
        message = "Error: api_key=sk-test123 failed at https://user:pass@api.com for john@example.com"  # pragma: allowlist secret
        sanitized = sanitize_error_message(message)

        # Should still be readable
        assert "Error:" in sanitized
        assert "failed at" in sanitized
        assert "for" in sanitized
        # But sensitive data should be gone
        assert "sk-test123" not in sanitized
        assert "user:pass" not in sanitized
        assert "john@example.com" not in sanitized


class TestErrorTemplates:
    """Test error message templates."""

    def test_process_failed_template(self):
        """Test process failure template."""
        message = format_error_message("PROCESS_FAILED", command="git clone", return_code=128)

        assert "git clone" in message
        assert "128" in message
        assert "failed with exit code" in message

    def test_network_timeout_template(self):
        """Test network timeout template."""
        message = format_error_message("NETWORK_TIMEOUT", url="https://api.example.com", timeout=30)

        assert "https://api.example.com" in message
        assert "30" in message
        assert "timed out" in message

    def test_config_missing_template(self):
        """Test missing configuration template."""
        message = format_error_message("CONFIG_MISSING", key="database_url")

        assert "database_url" in message
        assert "missing" in message

    def test_validation_error_template(self):
        """Test validation error template."""
        message = format_error_message("VALIDATION_REQUIRED", field="username")

        assert "username" in message
        assert "required" in message

    def test_template_sanitization(self):
        """Test that templates sanitize sensitive data."""
        message = format_error_message(
            "PROCESS_FAILED",
            command="git clone https://token:secret@github.com/repo.git",  # pragma: allowlist secret
            return_code=1,
            sanitize=True,
        )

        assert "token:secret" not in message
        assert "***:***@github.com" in message

    def test_unknown_template_raises_error(self):
        """Test that unknown template raises KeyError."""
        with pytest.raises(KeyError):
            format_error_message("UNKNOWN_TEMPLATE")

    def test_missing_template_variables_raises_error(self):
        """Test that missing variables raise ValueError."""
        with pytest.raises(ValueError):
            format_error_message("PROCESS_FAILED", command="test")  # Missing return_code


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_end_to_end_error_flow(self):
        """Test complete error handling flow."""
        # Set correlation ID
        correlation_id = set_correlation_id("integration-test")

        # Create error with full context
        error = ProcessError(
            message="Git clone failed",
            command="git clone https://github.com/repo.git",
            return_code=128,
            stderr="Permission denied",
            correlation_id=correlation_id,
        )

        # Convert to dict and verify structure
        error_dict = error.to_dict()
        assert error_dict["correlation_id"] == correlation_id
        assert error_dict["type"] == "ProcessError"
        assert "return_code" in error_dict["context"]

        # Log the error
        logger = ErrorLogger("integration.test")
        with patch.object(logger.logger, "log") as mock_log:
            logged_corr_id = logger.log_error(error)
            assert logged_corr_id == correlation_id
            mock_log.assert_called_once()

    def test_error_chaining(self):
        """Test error chaining with causes."""
        original_error = ValueError("Invalid input")

        wrapped_error = ProcessError(
            message="Command failed due to invalid input",
            command="process_data",
            return_code=1,
            cause=original_error,
        )

        # Should maintain cause chain
        assert wrapped_error.cause is original_error
        error_dict = wrapped_error.to_dict()
        assert error_dict["cause"] == "Invalid input"

    def test_concurrent_correlation_ids(self):
        """Test correlation IDs in concurrent scenarios."""
        results = {}

        def worker(worker_id: int):
            set_correlation_id(f"worker-{worker_id}")
            time.sleep(0.1)  # Simulate work
            results[worker_id] = get_correlation_id()

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Each worker should have its own correlation ID
        for i in range(5):
            assert results[i] == f"worker-{i}"

    def test_security_error_handling(self):
        """Test security-focused error handling."""
        # Create error with sensitive data
        error = SecurityError(
            message="Path traversal attempt detected",
            violation_type="path_traversal",
            resource="../../../etc/passwd",
            correlation_id="sec-test",
        )

        # Resource should be sanitized in context
        assert error.context["resource"] is not None
        # Original resource should still be available for internal use
        assert error.resource == "../../../etc/passwd"

        # Error message should be safe to log
        error.to_dict()
        sanitized_message = sanitize_error_message(str(error))
        assert "passwd" not in sanitized_message or "***" in sanitized_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
