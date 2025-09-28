"""Test suite for error logging and correlation ID functionality."""

import logging
import threading
import time
from unittest.mock import patch

import pytest

from amplihack.errors import (
    AmplihackError,
    CorrelationFilter,
    ErrorLogger,
    NetworkError,
    ProcessError,
    clear_correlation_id,
    generate_correlation_id,
    get_correlation_id,
    log_error,
    set_correlation_id,
)


class TestCorrelationIdGeneration:
    """Test correlation ID generation and management."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_generate_correlation_id_format(self):
        """Test correlation ID generation format."""
        corr_id = generate_correlation_id()

        assert isinstance(corr_id, str)
        assert len(corr_id) == 16  # 8 bytes hex = 16 characters
        # Should be hexadecimal
        assert all(c in "0123456789abcdef" for c in corr_id)

    def test_generate_correlation_id_uniqueness(self):
        """Test that generated correlation IDs are unique."""
        ids = [generate_correlation_id() for _ in range(100)]

        # All IDs should be unique
        assert len(set(ids)) == 100

    def test_correlation_id_thread_safety(self):
        """Test correlation ID generation thread safety."""
        ids = {}
        threads = []

        def generate_ids(thread_id):
            ids[thread_id] = [generate_correlation_id() for _ in range(10)]

        for i in range(10):
            thread = threading.Thread(target=generate_ids, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Collect all generated IDs
        all_ids = []
        for thread_ids in ids.values():
            all_ids.extend(thread_ids)

        # All IDs should be unique
        assert len(set(all_ids)) == 100


class TestCorrelationIdManagement:
    """Test correlation ID management in thread-local storage."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_set_specific_correlation_id(self):
        """Test setting a specific correlation ID."""
        test_id = "test-correlation-123"
        result_id = set_correlation_id(test_id)

        assert result_id == test_id
        assert get_correlation_id() == test_id

    def test_set_auto_generate_correlation_id(self):
        """Test auto-generating correlation ID."""
        result_id = set_correlation_id()

        assert result_id is not None
        assert len(result_id) == 16
        assert get_correlation_id() == result_id

    def test_get_correlation_id_when_none_set(self):
        """Test getting correlation ID when none is set."""
        assert get_correlation_id() is None

    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

        clear_correlation_id()
        assert get_correlation_id() is None

    def test_correlation_id_thread_isolation(self):
        """Test that correlation IDs are isolated between threads."""
        set_correlation_id("main-thread")
        thread_results = {}

        def thread_worker(thread_id):
            # Each thread sets its own correlation ID
            corr_id = set_correlation_id(f"thread-{thread_id}")
            time.sleep(0.1)  # Simulate work
            thread_results[thread_id] = {"set_id": corr_id, "get_id": get_correlation_id()}

        threads = []
        for i in range(5):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Main thread should retain its ID
        assert get_correlation_id() == "main-thread"

        # Each thread should have its own ID
        for i in range(5):
            expected_id = f"thread-{i}"
            assert thread_results[i]["set_id"] == expected_id
            assert thread_results[i]["get_id"] == expected_id

    def test_correlation_id_inheritance_in_new_threads(self):
        """Test that new threads start with no correlation ID."""
        set_correlation_id("parent-thread")
        child_correlation_id = None

        def child_thread():
            nonlocal child_correlation_id
            child_correlation_id = get_correlation_id()

        thread = threading.Thread(target=child_thread)
        thread.start()
        thread.join()

        # Parent should have its ID
        assert get_correlation_id() == "parent-thread"
        # Child should start with None
        assert child_correlation_id is None


class TestCorrelationFilter:
    """Test correlation filter for logging."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_correlation_filter_adds_correlation_id(self):
        """Test that correlation filter adds correlation ID to log records."""
        set_correlation_id("test-filter-123")
        filter_instance = CorrelationFilter()

        # Create a mock log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result is True  # Filter should not block records
        assert hasattr(record, "correlation_id")
        assert record.correlation_id == "test-filter-123"

    def test_correlation_filter_with_no_correlation_id(self):
        """Test correlation filter when no correlation ID is set."""
        filter_instance = CorrelationFilter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result is True
        assert hasattr(record, "correlation_id")
        assert record.correlation_id == "none"

    def test_correlation_filter_thread_specific(self):
        """Test that correlation filter uses thread-specific correlation ID."""
        set_correlation_id("main-filter")
        filter_instance = CorrelationFilter()
        thread_record_correlation = None

        def thread_worker():
            nonlocal thread_record_correlation
            set_correlation_id("thread-filter")

            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Thread message",
                args=(),
                exc_info=None,
            )

            filter_instance.filter(record)
            thread_record_correlation = record.correlation_id

        thread = threading.Thread(target=thread_worker)
        thread.start()
        thread.join()

        # Test main thread record
        main_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Main message",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(main_record)

        assert main_record.correlation_id == "main-filter"
        assert thread_record_correlation == "thread-filter"


class TestErrorLogger:
    """Test ErrorLogger functionality."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_error_logger_initialization(self):
        """Test ErrorLogger initialization."""
        logger = ErrorLogger("test.error.logger")

        assert logger.logger.name == "test.error.logger"
        # Should have correlation filter
        correlation_filters = [f for f in logger.logger.filters if isinstance(f, CorrelationFilter)]
        assert len(correlation_filters) == 1

    def test_error_logger_duplicate_filter_prevention(self):
        """Test that ErrorLogger doesn't add duplicate correlation filters."""
        logger = ErrorLogger("test.logger")
        original_filter_count = len(
            [f for f in logger.logger.filters if isinstance(f, CorrelationFilter)]
        )

        # Re-setup should not add another filter
        logger._setup_logger()

        new_filter_count = len(
            [f for f in logger.logger.filters if isinstance(f, CorrelationFilter)]
        )

        assert new_filter_count == original_filter_count

    def test_log_error_basic(self):
        """Test basic error logging."""
        logger = ErrorLogger("test.logger")
        error = AmplihackError("Test error message")

        with patch.object(logger.logger, "log") as mock_log:
            correlation_id = logger.log_error(error)

            assert correlation_id is not None
            assert len(correlation_id) == 16
            mock_log.assert_called_once()

            # Verify log call arguments
            args, kwargs = mock_log.call_args
            assert args[0] == logging.ERROR  # Level
            assert "Test error message" in args[1]  # Message
            assert "error_data" in kwargs["extra"]

    def test_log_error_with_existing_correlation_id(self):
        """Test logging error with existing correlation ID."""
        set_correlation_id("existing-corr-123")
        logger = ErrorLogger("test.logger")
        error = ProcessError("Process failed")

        with patch.object(logger.logger, "log") as mock_log:
            returned_id = logger.log_error(error)

            assert returned_id == "existing-corr-123"
            mock_log.assert_called_once()

    def test_log_error_with_custom_correlation_id(self):
        """Test logging error with custom correlation ID."""
        logger = ErrorLogger("test.logger")
        error = NetworkError("Network failed")
        custom_id = "custom-correlation-456"

        with patch.object(logger.logger, "log") as mock_log:
            returned_id = logger.log_error(error, correlation_id=custom_id)

            assert returned_id == custom_id
            # Should also set thread-local correlation ID
            assert get_correlation_id() == custom_id
            mock_log.assert_called_once()

    def test_log_error_with_context(self):
        """Test logging error with additional context."""
        logger = ErrorLogger("test.logger")
        error = AmplihackError("Test error")
        context = {"operation": "test_operation", "user": "test_user"}

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_error(error, context=context)

            args, kwargs = mock_log.call_args
            error_data = kwargs["extra"]["error_data"]
            assert error_data["context"] == context

    def test_log_error_with_custom_level(self):
        """Test logging error with custom log level."""
        logger = ErrorLogger("test.logger")
        error = AmplihackError("Warning level error")

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_error(error, level=logging.WARNING)

            args, kwargs = mock_log.call_args
            assert args[0] == logging.WARNING

    def test_log_error_sanitization(self):
        """Test that error logging sanitizes sensitive data."""
        logger = ErrorLogger("test.logger")
        error = ProcessError(
            "Command failed: api_key=sk-1234567890abcdef",
            command="curl -H 'Authorization: Bearer token123'",
        )

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_error(error)

            args, kwargs = mock_log.call_args
            error_data = kwargs["extra"]["error_data"]

            # Should not contain sensitive data
            assert "sk-1234567890abcdef" not in str(error_data)
            assert "token123" not in str(error_data)
            # But should contain sanitized versions
            assert "***" in str(error_data)

    def test_log_retry_attempt(self):
        """Test retry attempt logging."""
        logger = ErrorLogger("test.logger")
        error = ConnectionError("Network timeout")

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.log_retry_attempt(2, 5, error, 4.0, "retry-corr-123")

            mock_warning.assert_called_once()
            args, kwargs = mock_warning.call_args

            # Verify message content
            assert "Retry attempt 2/5" in args[0]
            assert "ConnectionError" in args[0]

            # Verify extra data
            assert "retry_data" in kwargs["extra"]
            retry_data = kwargs["extra"]["retry_data"]
            assert retry_data["attempt"] == 2
            assert retry_data["max_attempts"] == 5
            assert retry_data["delay"] == 4.0
            assert retry_data["retry_correlation_id"] == "retry-corr-123"

    def test_log_retry_exhausted(self):
        """Test retry exhausted logging."""
        logger = ErrorLogger("test.logger")
        final_error = ProcessError("Final process error")

        with patch.object(logger.logger, "error") as mock_error:
            logger.log_retry_exhausted(3, final_error, "exhausted-corr-456")

            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args

            # Verify message content
            assert "Retry exhausted after 3 attempts" in args[0]
            assert "ProcessError" in args[0]

            # Verify extra data
            assert "retry_exhausted_data" in kwargs["extra"]
            exhausted_data = kwargs["extra"]["retry_exhausted_data"]
            assert exhausted_data["max_attempts"] == 3
            assert exhausted_data["final_error_type"] == "ProcessError"
            assert exhausted_data["retry_correlation_id"] == "exhausted-corr-456"

    def test_log_error_with_structured_error(self):
        """Test logging with error that has to_dict method."""
        logger = ErrorLogger("test.logger")
        error = ProcessError(
            "Command failed",
            command="test command",
            return_code=1,
            correlation_id="struct-corr-789",
        )

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_error(error)

            args, kwargs = mock_log.call_args
            error_data = kwargs["extra"]["error_data"]

            # Should include data from to_dict method
            assert error_data["error_type"] == "ProcessError"
            assert error_data["correlation_id"] == "struct-corr-789"
            assert error_data["context"]["return_code"] == 1


class TestGlobalErrorLogging:
    """Test global error logging function."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_global_log_error_function(self):
        """Test global log_error function."""
        error = AmplihackError("Global test error")

        with patch("amplihack.errors.logging.error_logger") as mock_logger:
            correlation_id = log_error(error)

            mock_logger.log_error.assert_called_once_with(
                error, logging.ERROR, correlation_id, None
            )

    def test_global_log_error_with_parameters(self):
        """Test global log_error with all parameters."""
        error = NetworkError("Global network error")
        context = {"test": "context"}
        custom_corr_id = "global-test-123"

        with patch("amplihack.errors.logging.error_logger") as mock_logger:
            log_error(error, level=logging.WARNING, correlation_id=custom_corr_id, context=context)

            mock_logger.log_error.assert_called_once_with(
                error, logging.WARNING, custom_corr_id, context
            )


class TestConcurrentLogging:
    """Test concurrent logging scenarios."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_concurrent_error_logging(self):
        """Test concurrent error logging with different correlation IDs."""
        logger = ErrorLogger("concurrent.test")
        results = {}

        def log_worker(worker_id):
            set_correlation_id(f"worker-{worker_id}")
            error = AmplihackError(f"Error from worker {worker_id}")

            with patch.object(logger.logger, "log") as mock_log:
                logged_id = logger.log_error(error)
                results[worker_id] = {
                    "correlation_id": logged_id,
                    "log_called": mock_log.called,
                    "thread_correlation": get_correlation_id(),
                }

        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify each worker had its own correlation ID
        for i in range(5):
            expected_id = f"worker-{i}"
            assert results[i]["correlation_id"] == expected_id
            assert results[i]["thread_correlation"] == expected_id
            assert results[i]["log_called"] is True

    def test_correlation_filter_thread_safety(self):
        """Test correlation filter thread safety."""
        filter_instance = CorrelationFilter()
        results = {}

        def filter_worker(worker_id):
            set_correlation_id(f"filter-worker-{worker_id}")

            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message from worker {worker_id}",
                args=(),
                exc_info=None,
            )

            filter_result = filter_instance.filter(record)
            results[worker_id] = {
                "filter_result": filter_result,
                "record_correlation": record.correlation_id,
                "thread_correlation": get_correlation_id(),
            }

        threads = []
        for i in range(10):
            thread = threading.Thread(target=filter_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify thread safety
        for i in range(10):
            expected_id = f"filter-worker-{i}"
            assert results[i]["filter_result"] is True
            assert results[i]["record_correlation"] == expected_id
            assert results[i]["thread_correlation"] == expected_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
