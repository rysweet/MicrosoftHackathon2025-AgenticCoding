# Error Handling Comprehensive Test Suite (Issue #179)

This test suite provides comprehensive failing tests for error handling improvements using Test-Driven Development (TDD) approach.

## Overview

The error handling improvements require implementation of:

- Retry logic with exponential backoff (3 attempts, 1s, 2s, 4s delays)
- Error recovery for subprocess, file I/O, and network operations
- Fallback strategies for common failure scenarios
- Structured error logging with correlation IDs
- User-friendly error message transformation
- Graceful degradation paths

## Test Structure

### Core Test Files

1. **`test_error_handling_comprehensive.py`** - Main comprehensive test suite
   - Error simulation utilities (`ErrorSimulator`, `RetryErrorCounter`)
   - Retry logic tests with exponential backoff
   - Fallback strategy tests (npm→pip, uv→pip, claude-trace→claude)
   - Error message transformation tests
   - Structured logging tests
   - Performance overhead tests
   - Integration tests for existing managers

2. **`test_retry_mechanisms.py`** - Specialized retry mechanism tests
   - `RetryStrategy` interface tests
   - `CircuitBreaker` pattern tests
   - `RetryableOperation` wrapper tests
   - Timing validation and precision tests
   - Async retry mechanism tests
   - Performance benchmarks

3. **`test_error_logging_correlation.py`** - Logging infrastructure tests
   - `CorrelationIDManager` tests
   - `StructuredErrorLogger` tests
   - `LogAggregator` tests
   - Security and privacy tests
   - Performance tests for logging

4. **`test_error_recovery_integration.py`** - Integration tests
   - Cross-manager error recovery
   - Real-world scenario simulations
   - Performance impact assessment
   - Configuration and customization tests

## Test Requirements

### Coverage Requirements

- **>85% test coverage** for error handling code paths
- Error simulation utilities for testing
- Fallback strategy validation
- Performance testing for **<5% overhead** requirement
- Integration tests for end-to-end error scenarios

### Specific Test Scenarios

#### 1. Retry Logic Tests

```python
# Exponential backoff timing: 1s, 2s, 4s delays
def test_retry_exponential_backoff_timing()

# Retry on transient failures
def test_retry_succeeds_on_third_attempt()

# Give up after max attempts
def test_retry_exhausts_all_attempts()

# Correlation ID tracking
def test_retry_with_correlation_id()
```

#### 2. Fallback Strategy Tests

```python
# npm → pip fallback
def test_npm_to_pip_fallback()

# uv → pip fallback
def test_uv_to_pip_fallback()

# claude-trace → claude fallback
def test_claude_trace_to_claude_fallback()

# All strategies fail
def test_all_fallbacks_fail()
```

#### 3. Error Message Tests

```python
# Technical → user-friendly transformation
def test_subprocess_error_transformation()
def test_permission_error_transformation()
def test_network_error_transformation()

# Technical details preservation
def test_technical_error_preservation()
```

#### 4. Logging Tests

```python
# Correlation ID management
def test_correlation_id_generation()
def test_correlation_id_context_management()

# Structured logging
def test_error_logging_structure()
def test_retry_attempt_logging()
def test_fallback_strategy_logging()

# Security and privacy
def test_sensitive_data_scrubbing()
def test_file_path_sanitization()
```

#### 5. Performance Tests

```python
# Retry overhead <5%
def test_retry_overhead_successful_operation()

# Logging performance
def test_structured_logging_performance()

# Memory usage limits
def test_error_recovery_memory_usage()
```

## Implementation Interfaces

### Required Classes (Currently Don't Exist - Tests Will Fail)

```python
class ErrorRecovery:
    """Retry logic with exponential backoff."""
    @staticmethod
    def with_retry(func, max_attempts=3, base_delay=1.0, correlation_id=None)

    @staticmethod
    def fallback_chain(strategies, correlation_id=None)

    @staticmethod
    def transform_error_message(error, user_friendly=True)

class StructuredLogger:
    """Structured logging with correlation IDs."""
    def __init__(self, correlation_id=None)
    def log_retry_attempt(self, attempt, error, delay, context=None)
    def log_fallback_attempt(self, strategy, success, error=None)
    def log_error_recovery(self, original_error, recovery_action)

class RetryStrategy:
    """Configurable retry strategies."""
    def __init__(self, max_attempts=3, base_delay=1.0, backoff_factor=2.0)
    def should_retry(self, attempt, error)
    def get_delay(self, attempt)

class CircuitBreaker:
    """Circuit breaker pattern for error recovery."""
    def __init__(self, failure_threshold=5, recovery_timeout=60.0)
    def call(self, func, *args, **kwargs)
    @property
    def state(self)  # CLOSED, OPEN, HALF_OPEN

class CorrelationIDManager:
    """Thread-safe correlation ID management."""
    @staticmethod
    def generate()
    @staticmethod
    def set_current(correlation_id)
    @staticmethod
    def get_current()
    @contextmanager
    def context(correlation_id)
```

### Enhanced Manager Classes (Also Don't Exist)

```python
class EnhancedProxyManager:
    """ProxyManager with comprehensive error handling."""
    def start_proxy_with_recovery(self)
    def install_dependencies_with_fallback(self)

class EnhancedUVXManager:
    """UVXManager with retry logic and fallbacks."""
    def detect_environment_with_retry(self)
    def resolve_paths_with_fallback(self)

class ErrorRecoveryOrchestrator:
    """Cross-manager error recovery coordination."""
    def execute_with_recovery(self, primary_operation, fallback_chain)
    def handle_cascading_failures(self, operations, dependencies)
```

## Running the Tests

### Prerequisites

```bash
pip install pytest pytest-asyncio psutil
```

### Run All Error Handling Tests

```bash
# All tests (will fail until implementation)
pytest tests/test_error_handling_comprehensive.py -v

# Specific test categories
pytest tests/test_retry_mechanisms.py -v
pytest tests/test_error_logging_correlation.py -v
pytest tests/test_error_recovery_integration.py -v
```

### Run with Coverage

```bash
pip install pytest-cov
pytest tests/test_error_handling_comprehensive.py --cov=amplihack --cov-report=html
```

### Run Performance Tests

```bash
pytest tests/ -m performance -v
```

### Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Component integration tests
- `@pytest.mark.performance` - Performance benchmark tests
- `@pytest.mark.error_case` - Error handling specific tests
- `@pytest.mark.slow` - Tests that may take several seconds

## Expected Test Results (Before Implementation)

**ALL TESTS SHOULD FAIL** with `NotImplementedError` until the error handling modules are implemented.

Example expected output:

```
tests/test_error_handling_comprehensive.py::TestRetryLogicWithExponentialBackoff::test_retry_succeeds_on_first_attempt FAILED
...
NotImplementedError: ErrorRecovery.with_retry not implemented
```

## Implementation Guidance

### 1. Start with Core Infrastructure

Implement in this order:

1. `CorrelationIDManager` - Thread-safe correlation ID management
2. `StructuredLogger` - JSON logging with correlation IDs
3. `RetryStrategy` - Exponential backoff calculations
4. `ErrorRecovery` - Core retry and fallback logic

### 2. Add Circuit Breaker Pattern

5. `CircuitBreaker` - Failure threshold and recovery logic

### 3. Enhance Existing Managers

6. Modify `ProxyManager` to use error recovery
7. Modify `UVXManager` to use retry logic
8. Modify `ProcessManager` for better error handling

### 4. Add Integration Layer

9. `ErrorRecoveryOrchestrator` - Cross-manager coordination

### Timing Requirements

- **Exponential backoff**: 1s, 2s, 4s delays exactly
- **Performance overhead**: <5% for successful operations
- **Circuit breaker recovery**: Configurable timeout (default 60s)
- **Max total retry time**: Configurable (default 300s)

### Fallback Strategy Examples

```python
# npm → pip fallback
strategies = [
    lambda: subprocess.run(["npm", "install", "package"]),
    lambda: subprocess.run(["pip", "install", "package"])
]

# uv → pip fallback
strategies = [
    lambda: subprocess.run(["uv", "pip", "install", "package"]),
    lambda: subprocess.run(["pip", "install", "package"])
]

# claude-trace → claude fallback
strategies = [
    lambda: get_command_with_trace(),
    lambda: "claude"
]
```

### Security Considerations

- **Scrub sensitive data** from logs (API keys, passwords, paths)
- **Validate paths** to prevent directory traversal
- **Use cryptographically secure** correlation IDs
- **Limit log retention** and implement rotation

## Integration with Existing Code

### Proxy Manager Integration

```python
# Current: Basic error handling
def start_proxy(self):
    try:
        # ... proxy startup logic
    except Exception as e:
        print(f"Failed to start proxy: {e}")
        return False

# Enhanced: Comprehensive error recovery
def start_proxy_with_recovery(self):
    correlation_id = CorrelationIDManager.generate()

    with CorrelationIDManager.context(correlation_id):
        return ErrorRecovery.with_retry(
            self._start_proxy_internal,
            max_attempts=3,
            correlation_id=correlation_id
        )
```

### UVX Manager Integration

```python
# Current: Simple validation
def validate_path_security(self, path):
    # Basic validation
    return path is not None and ".." not in str(path)

# Enhanced: Comprehensive validation with recovery
def validate_path_security_with_recovery(self, path):
    correlation_id = CorrelationIDManager.get_current()

    try:
        return self._validate_path_internal(path)
    except SecurityError as e:
        logger = StructuredLogger(correlation_id)
        logger.log_error(e, {"path": str(path), "operation": "path_validation"})

        # Try alternative paths
        return ErrorRecovery.fallback_chain([
            lambda: self._get_safe_alternative_path(),
            lambda: self._use_default_safe_path()
        ], correlation_id)
```

## Test Development Guidelines

### Writing New Tests

1. **Always test the failure case** - TDD requires failing tests first
2. **Use descriptive test names** - Explain what should happen when implemented
3. **Include timing assertions** - Verify exponential backoff timing precisely
4. **Test edge cases** - Empty inputs, null values, maximum limits
5. **Mock external dependencies** - Network, filesystem, subprocess calls
6. **Verify correlation IDs** - Ensure they're propagated through all operations

### Test Assertions to Add (After Implementation)

```python
# Timing precision
def test_exponential_backoff_timing():
    delays = counter.get_retry_delays()
    assert len(delays) == 2
    assert 0.9 <= delays[0] <= 1.1  # ~1 second
    assert 1.9 <= delays[1] <= 2.1  # ~2 seconds

# Correlation ID propagation
def test_correlation_id_propagation():
    correlation_id = str(uuid.uuid4())
    with CorrelationIDManager.context(correlation_id):
        # Verify correlation_id appears in all logs
        pass

# Performance overhead
def test_performance_overhead():
    overhead = (wrapped_avg - baseline_avg) / baseline_avg
    assert overhead < 0.05  # Less than 5%

# Fallback success
def test_fallback_chain():
    result = ErrorRecovery.fallback_chain(strategies)
    assert result == "pip install successful"
```

## Success Criteria

Tests will be considered successful when:

1. **All tests pass** - No more `NotImplementedError` exceptions
2. **Coverage >85%** - Error handling code paths covered
3. **Performance <5%** - Overhead within requirements
4. **Timing precision** - Exponential backoff timing accurate
5. **Correlation tracking** - All operations have correlation IDs
6. **Security validation** - Sensitive data properly scrubbed
7. **Integration working** - Cross-manager error recovery functional

## Future Enhancements

Consider adding tests for:

- **Distributed correlation IDs** - Across multiple processes
- **Error rate limiting** - Prevent log spam
- **Custom retry policies** - Per-operation configuration
- **Metrics collection** - Error rates, recovery success rates
- **Alert integration** - Notify on repeated failures
- **Recovery suggestions** - AI-powered error resolution hints
