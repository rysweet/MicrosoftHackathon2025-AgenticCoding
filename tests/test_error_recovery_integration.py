"""Integration tests for error recovery and end-to-end error handling."""

import asyncio
import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from amplihack.errors import (
    ConfigurationError,
    ErrorLogger,
    NetworkError,
    ProcessError,
    RetryConfig,
    SecurityError,
    TimeoutError,
    clear_correlation_id,
    get_correlation_id,
    retry_on_error,
    set_correlation_id,
)
from amplihack.proxy.manager import ProxyManager
from amplihack.utils.claude_trace import get_claude_command
from amplihack.utils.process import ProcessManager
from amplihack.uvx.manager import UVXManager


class TestProcessManagerIntegration:
    """Test ProcessManager with enhanced error handling."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_process_manager_command_exists(self):
        """Test ProcessManager command existence checking."""
        # Test with existing command
        assert ProcessManager.check_command_exists("echo") is True
        assert ProcessManager.check_command_exists("ls") is True

        # Test with non-existing command
        assert ProcessManager.check_command_exists("nonexistent_command_12345") is False

    def test_process_manager_run_command_success(self):
        """Test successful command execution."""
        result = ProcessManager.run_command(["echo", "hello world"])

        assert result.returncode == 0
        assert "hello world" in result.stdout
        assert result.stderr == ""

    def test_process_manager_run_command_failure(self):
        """Test command execution failure handling."""
        with pytest.raises(ProcessError) as exc_info:
            ProcessManager.run_command(["ls", "/nonexistent/directory/12345"])

        error = exc_info.value
        assert error.return_code != 0
        assert error.command is not None
        assert error.correlation_id is not None

    def test_process_manager_run_command_timeout(self):
        """Test command timeout handling."""
        with pytest.raises(TimeoutError) as exc_info:
            ProcessManager.run_command(["sleep", "10"], timeout=0.1)

        error = exc_info.value
        assert error.timeout_duration == 0.1
        assert "run_command" in error.operation
        assert error.correlation_id is not None

    def test_process_manager_run_command_nonexistent(self):
        """Test running non-existent command."""
        with pytest.raises(ProcessError) as exc_info:
            ProcessManager.run_command(["nonexistent_command_67890"])

        error = exc_info.value
        assert error.return_code == 127  # Command not found
        assert "nonexistent_command_67890" in error.command

    def test_process_manager_run_command_safe(self):
        """Test safe command execution."""
        # Successful command
        result = ProcessManager.run_command_safe(["echo", "test"])
        assert result is not None
        assert result.returncode == 0

        # Failed command
        result = ProcessManager.run_command_safe(["ls", "/nonexistent"])
        assert result is None

    def test_process_manager_correlation_id_tracking(self):
        """Test that ProcessManager maintains correlation IDs."""
        correlation_id = set_correlation_id("process-test-123")

        with pytest.raises(ProcessError) as exc_info:
            ProcessManager.run_command(["ls", "/nonexistent"])

        # Should use existing correlation ID
        assert exc_info.value.correlation_id == correlation_id

    def test_process_manager_retry_on_transient_failure(self):
        """Test retry behavior on transient failures."""
        call_count = 0

        # Mock run_command to fail twice then succeed
        original_run = subprocess.run

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # Simulate transient failure
                result = Mock()
                result.returncode = 1
                result.stdout = ""
                result.stderr = "Transient error"
                return result
            return original_run(*args, **kwargs)

        with patch("subprocess.run", side_effect=mock_run):
            with patch.object(ProcessManager, "check_command_exists", return_value=True):
                try:
                    ProcessManager.run_command(["echo", "success"])
                except ProcessError:
                    pass  # Expected on mock failures

        assert call_count >= 2  # Should have retried


class TestProxyManagerIntegration:
    """Test ProxyManager with enhanced error handling."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_proxy_manager_initialization(self):
        """Test ProxyManager initialization."""
        manager = ProxyManager()

        assert manager.proxy_config is None
        assert manager.proxy_process is None
        assert manager.proxy_port in [8080]  # Default port
        assert manager.proxy_dir.name == "proxy"

    def test_proxy_manager_ensure_installed_git_failure(self):
        """Test proxy installation with git failure."""
        manager = ProxyManager()

        with patch("subprocess.run") as mock_run:
            # Mock git clone failure
            mock_run.side_effect = subprocess.CalledProcessError(
                128, ["git", "clone"], stderr="Permission denied"
            )

            with pytest.raises(ProcessError) as exc_info:
                manager.ensure_proxy_installed()

            error = exc_info.value
            assert "git clone" in error.command
            assert error.return_code == 128
            assert error.correlation_id is not None

    def test_proxy_manager_ensure_installed_timeout(self):
        """Test proxy installation timeout."""
        manager = ProxyManager()

        with patch("subprocess.run") as mock_run:
            # Mock git clone timeout
            mock_run.side_effect = subprocess.TimeoutExpired(["git", "clone"], 120)

            with pytest.raises(NetworkError) as exc_info:
                manager.ensure_proxy_installed()

            error = exc_info.value
            assert error.timeout == 120.0
            assert "github.com" in error.url
            assert error.correlation_id is not None

    def test_proxy_manager_correlation_id_propagation(self):
        """Test correlation ID propagation in proxy operations."""
        correlation_id = set_correlation_id("proxy-test-456")
        manager = ProxyManager()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["git"])

            try:
                manager.ensure_proxy_installed()
            except ProcessError as e:
                # Should use the existing correlation ID
                assert e.correlation_id == correlation_id

    def test_proxy_manager_dependency_installation_failure(self):
        """Test dependency installation failure handling."""
        manager = ProxyManager()
        test_repo = Path("/tmp/test_proxy_repo")

        # Create mock repo structure
        test_repo.mkdir(exist_ok=True)
        requirements_file = test_repo / "requirements.txt"
        requirements_file.write_text("fake-package==1.0.0\n")

        try:
            with patch.object(manager, "proxy_dir", test_repo.parent):
                with patch("subprocess.run") as mock_run:
                    # Mock pip install failure
                    mock_run.return_value = Mock(returncode=1, stderr="Package not found")

                    with pytest.raises(ProcessError) as exc_info:
                        manager._install_proxy_dependencies(test_repo, "test-corr")

                    error = exc_info.value
                    assert "pip install" in error.command or "uv" in error.command
                    assert error.correlation_id == "test-corr"

        finally:
            # Cleanup
            if requirements_file.exists():
                requirements_file.unlink()
            if test_repo.exists():
                test_repo.rmdir()


class TestUVXManagerIntegration:
    """Test UVXManager with enhanced error handling."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_uvx_manager_initialization(self):
        """Test UVXManager initialization."""
        manager = UVXManager()

        assert manager.force_staging is False
        assert manager._config is not None
        assert manager._detection_state is None
        assert manager._path_resolution is None

    def test_uvx_manager_detection_failure_handling(self):
        """Test UVX detection failure handling."""
        manager = UVXManager()

        with patch("amplihack.utils.uvx_detection.detect_uvx_deployment") as mock_detect:
            mock_detect.side_effect = Exception("Detection failed")

            with pytest.raises(ConfigurationError) as exc_info:
                manager._ensure_detection()

            error = exc_info.value
            assert "UVX detection failed" in str(error)
            assert error.correlation_id is not None

    def test_uvx_manager_path_security_validation(self):
        """Test path security validation."""
        manager = UVXManager()

        # Test dangerous paths
        dangerous_paths = [
            Path("../../../etc/passwd"),
            Path("/etc/passwd"),
            Path("/root/.ssh/id_rsa"),
            Path("/System/Library/Security"),
        ]

        for path in dangerous_paths:
            # Should not raise but return False
            assert manager.validate_path_security(path) is False

    def test_uvx_manager_path_traversal_detection(self):
        """Test path traversal detection."""
        manager = UVXManager()
        set_correlation_id("uvx-security-test")

        # Path with traversal should return False and log security error
        with patch("amplihack.errors.log_error") as mock_log:
            result = manager.validate_path_security(Path("../../../etc/passwd"))

            assert result is False
            # Should have logged a security error
            mock_log.assert_called()
            logged_error = mock_log.call_args[1]["error"]
            assert isinstance(logged_error, SecurityError)
            assert logged_error.violation_type == "path_traversal"

    def test_uvx_manager_correlation_id_in_operations(self):
        """Test correlation ID usage in UVX operations."""
        correlation_id = set_correlation_id("uvx-correlation-test")
        manager = UVXManager()

        with patch("amplihack.utils.uvx_detection.detect_uvx_deployment") as mock_detect:
            mock_detect.side_effect = Exception("Test error")

            try:
                manager._ensure_detection()
            except ConfigurationError as e:
                # Should use the existing correlation ID
                assert e.correlation_id == correlation_id


class TestClaudeTraceIntegration:
    """Test claude-trace integration with error handling."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_get_claude_command_no_trace_available(self):
        """Test claude command resolution when trace is not available."""
        with patch("shutil.which") as mock_which:
            # Mock claude-trace not available, claude available
            def which_side_effect(cmd):
                if cmd == "claude-trace":
                    return None
                elif cmd == "claude":
                    return "/usr/local/bin/claude"
                elif cmd == "npm":
                    return None
                return None

            mock_which.side_effect = which_side_effect

            command = get_claude_command()
            assert command == "claude"

    def test_get_claude_command_installation_failure(self):
        """Test claude command resolution when installation fails."""
        with patch("shutil.which") as mock_which:
            with patch("subprocess.run") as mock_run:
                # Mock claude-trace not available, npm available but install fails
                def which_side_effect(cmd):
                    if cmd == "claude-trace":
                        return None
                    elif cmd == "claude":
                        return "/usr/local/bin/claude"
                    elif cmd == "npm":
                        return "/usr/local/bin/npm"
                    return None

                mock_which.side_effect = which_side_effect
                mock_run.return_value = Mock(returncode=1, stderr="Install failed")

                command = get_claude_command()
                assert command == "claude"

    def test_get_claude_command_no_claude_available(self):
        """Test claude command resolution when neither command is available."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(ProcessError) as exc_info:
                get_claude_command()

            error = exc_info.value
            assert "claude command found" in str(error)
            assert error.correlation_id is not None

    def test_claude_trace_installation_timeout(self):
        """Test claude-trace installation timeout handling."""
        with patch("shutil.which") as mock_which:
            with patch("subprocess.run") as mock_run:
                mock_which.side_effect = lambda cmd: "/usr/bin/npm" if cmd == "npm" else None
                mock_run.side_effect = subprocess.TimeoutExpired(["npm", "install"], 120)

                # Import the private function for testing
                from amplihack.utils.claude_trace import _install_claude_trace

                with pytest.raises(NetworkError) as exc_info:
                    _install_claude_trace()

                error = exc_info.value
                assert error.timeout == 120.0
                assert error.correlation_id is not None


class TestEndToEndErrorRecovery:
    """Test end-to-end error recovery scenarios."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_cascading_error_recovery(self):
        """Test recovery from cascading errors across components."""
        correlation_id = set_correlation_id("e2e-cascade-test")

        # Simulate a scenario where multiple components fail and recover
        results = {}

        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        def simulate_process_operation():
            if not hasattr(simulate_process_operation, "attempts"):
                simulate_process_operation.attempts = 0
            simulate_process_operation.attempts += 1

            if simulate_process_operation.attempts < 2:
                raise ProcessError(
                    "Process temporarily unavailable",
                    command="test_process",
                    return_code=1,
                    correlation_id=correlation_id,
                )
            results["process"] = "success"
            return "process_success"

        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        def simulate_network_operation():
            if not hasattr(simulate_network_operation, "attempts"):
                simulate_network_operation.attempts = 0
            simulate_network_operation.attempts += 1

            if simulate_network_operation.attempts < 3:
                raise NetworkError(
                    "Network temporarily unavailable",
                    url="https://api.test.com",
                    status_code=503,
                    correlation_id=correlation_id,
                )
            results["network"] = "success"
            return "network_success"

        # Execute operations
        process_result = simulate_process_operation()
        network_result = simulate_network_operation()

        assert process_result == "process_success"
        assert network_result == "network_success"
        assert results["process"] == "success"
        assert results["network"] == "success"

        # Verify correlation ID was maintained
        assert get_correlation_id() == correlation_id

    def test_concurrent_error_recovery(self):
        """Test concurrent error recovery scenarios."""
        correlation_ids = {}
        results = {}

        def worker_operation(worker_id):
            correlation_id = set_correlation_id(f"worker-{worker_id}")
            correlation_ids[worker_id] = correlation_id

            @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
            def worker_task():
                # First attempt fails, second succeeds
                if not hasattr(worker_task, f"attempts_{worker_id}"):
                    setattr(worker_task, f"attempts_{worker_id}", 0)

                attempts = getattr(worker_task, f"attempts_{worker_id}")
                setattr(worker_task, f"attempts_{worker_id}", attempts + 1)

                if attempts == 0:
                    raise ProcessError(
                        f"Worker {worker_id} temporary failure", correlation_id=correlation_id
                    )

                results[worker_id] = f"worker_{worker_id}_success"
                return results[worker_id]

            return worker_task()

        # Run concurrent workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_operation, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all workers succeeded with their own correlation IDs
        for i in range(5):
            assert results[i] == f"worker_{i}_success"
            assert correlation_ids[i] == f"worker-{i}"

    @pytest.mark.asyncio
    async def test_async_error_recovery(self):
        """Test async error recovery scenarios."""
        correlation_id = set_correlation_id("async-e2e-test")

        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        async def async_operation_with_recovery():
            if not hasattr(async_operation_with_recovery, "attempts"):
                async_operation_with_recovery.attempts = 0
            async_operation_with_recovery.attempts += 1

            await asyncio.sleep(0.001)  # Simulate async work

            if async_operation_with_recovery.attempts < 3:
                raise NetworkError(
                    "Async network error",
                    url="https://async.api.com",
                    correlation_id=correlation_id,
                )

            return "async_success"

        result = await async_operation_with_recovery()

        assert result == "async_success"
        assert get_correlation_id() == correlation_id

    def test_error_context_preservation(self):
        """Test that error context is preserved across recovery attempts."""
        correlation_id = set_correlation_id("context-preservation-test")
        error_contexts = []

        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        def context_preserving_operation():
            if not hasattr(context_preserving_operation, "attempts"):
                context_preserving_operation.attempts = 0
            context_preserving_operation.attempts += 1

            context = {
                "attempt": context_preserving_operation.attempts,
                "operation": "context_test",
                "timestamp": time.time(),
            }

            if context_preserving_operation.attempts < 3:
                error = ProcessError(
                    f"Attempt {context_preserving_operation.attempts} failed",
                    correlation_id=correlation_id,
                    context=context,
                )
                error_contexts.append(error.context)
                raise error

            return "context_success"

        result = context_preserving_operation()

        assert result == "context_success"
        assert len(error_contexts) == 2  # Two failed attempts

        # Verify context was preserved and unique for each attempt
        for i, context in enumerate(error_contexts):
            assert context["attempt"] == i + 1
            assert context["operation"] == "context_test"
            assert "timestamp" in context

    def test_security_error_no_retry(self):
        """Test that security errors are not retried."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=5, base_delay=0.01))
        def security_violation_operation():
            nonlocal call_count
            call_count += 1
            raise SecurityError(
                "Access denied", violation_type="unauthorized_access", resource="/secure/resource"
            )

        with pytest.raises(SecurityError):
            security_violation_operation()

        # Should not have retried
        assert call_count == 1

    def test_budget_exhaustion_recovery(self):
        """Test recovery behavior when retry budget is exhausted."""
        call_count = 0

        # Limited retry configuration
        budget_config = RetryConfig(
            max_attempts=3,  # Limited attempts
            base_delay=1.0,  # Base delays
            max_delay=2.0,  # Small max delay acts as budget constraint
        )

        @retry_on_error(budget_config)
        def budget_limited_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        start_time = time.time()

        with pytest.raises(ConnectionError):
            budget_limited_operation()

        elapsed = time.time() - start_time

        # Should have stopped due to budget, not max attempts
        assert call_count < 10
        assert elapsed < 10.0  # Much less than max attempts would take


class TestErrorMetricsAndMonitoring:
    """Test error metrics and monitoring capabilities."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_error_logging_with_metrics(self):
        """Test error logging includes useful metrics."""
        logger = ErrorLogger("metrics.test")
        correlation_id = set_correlation_id("metrics-test-123")

        start_time = time.time()
        error = ProcessError(
            "Test process error",
            command="test_command",
            return_code=1,
            correlation_id=correlation_id,
        )

        with patch.object(logger.logger, "log") as mock_log:
            logged_id = logger.log_error(
                error,
                context={
                    "operation_start_time": start_time,
                    "component": "test_component",
                    "user_action": "test_action",
                },
            )

            assert logged_id == correlation_id
            args, kwargs = mock_log.call_args
            error_data = kwargs["extra"]["error_data"]

            # Verify metrics are included
            assert error_data["correlation_id"] == correlation_id
            assert "operation_start_time" in error_data["context"]
            assert "component" in error_data["context"]
            assert "user_action" in error_data["context"]

    def test_retry_metrics_logging(self):
        """Test that retry metrics are properly logged."""
        logger = ErrorLogger("retry.metrics")

        with patch.object(logger, "log_retry_attempt") as mock_retry_log:

            @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
            def metrics_retry_operation():
                if not hasattr(metrics_retry_operation, "attempts"):
                    metrics_retry_operation.attempts = 0
                metrics_retry_operation.attempts += 1

                if metrics_retry_operation.attempts < 3:
                    raise ConnectionError("Metrics test error")
                return "success"

            result = metrics_retry_operation()

            assert result == "success"
            # Should have logged retry attempts
            assert mock_retry_log.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
