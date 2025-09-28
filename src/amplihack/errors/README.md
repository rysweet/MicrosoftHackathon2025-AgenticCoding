# Amplihack Error Handling System

This document describes the comprehensive error handling system implemented for amplihack (Issue #179). The system provides structured error handling with retry mechanisms, security features, and comprehensive logging with correlation IDs.

## Overview

The error handling system is designed around several core principles:

- **Structured Errors**: All errors inherit from a base `AmplihackError` class with consistent structure
- **Correlation IDs**: Every error can be tracked across system components using secure correlation IDs
- **Retry Mechanisms**: Automatic retry with exponential backoff and security constraints
- **Security First**: Credential sanitization and DoS protection built-in
- **Comprehensive Logging**: Structured logging with correlation tracking

## Core Components

### Error Classes

All error classes inherit from `AmplihackError` and provide structured information:

```python
from amplihack.errors import ProcessError, NetworkError, SecurityError

# Create structured errors with context
error = ProcessError(
    message="Command failed",
    command="git clone repo.git",
    return_code=128,
    correlation_id="abc123",
    context={"operation": "setup"}
)
```

Available error types:

- `AmplihackError` - Base class for all errors
- `ProcessError` - Process execution failures
- `NetworkError` - Network operation failures
- `ConfigurationError` - Configuration issues
- `ValidationError` - Input validation failures
- `SecurityError` - Security violations
- `TimeoutError` - Operation timeouts

### Correlation IDs

Track errors across system components with secure correlation IDs:

```python
from amplihack.errors import set_correlation_id, get_correlation_id

# Set correlation ID for current thread
correlation_id = set_correlation_id("operation-123")

# Auto-generate secure correlation ID
correlation_id = set_correlation_id()

# Get current correlation ID
current_id = get_correlation_id()
```

Correlation IDs are thread-local and automatically included in all error logging.

### Retry Mechanisms

Automatic retry with exponential backoff and security constraints:

```python
from amplihack.errors import retry_on_error, RetryConfig

# Simple retry with defaults
@retry_on_error()
def risky_operation():
    # Operation that might fail
    pass

# Custom retry configuration
config = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

@retry_on_error(config)
def custom_retry_operation():
    pass

# Async retry support
@retry_async(config)
async def async_operation():
    pass
```

#### Security Features

The retry system includes built-in security protections:

- **Maximum 5 retry attempts** - Prevents infinite retry loops
- **Maximum 30-second delays** - Prevents excessive waiting
- **Retry budgets** - Limits total retry time to prevent DoS
- **Non-retryable errors** - Security and validation errors never retry

#### Error Classification

Errors are automatically classified as retryable or non-retryable:

**Retryable (by default):**

- `ConnectionError`
- `TimeoutError`
- `OSError`
- `ProcessError`
- `NetworkError`

**Non-retryable (by default):**

- `ValueError`
- `TypeError`
- `SecurityError`
- `ValidationError`

You can customize error classification:

```python
config = RetryConfig(
    retryable_errors=(ValueError, OSError),
    non_retryable_errors=(SecurityError,)
)
```

### Structured Logging

Comprehensive logging with correlation ID tracking:

```python
from amplihack.errors import ErrorLogger, log_error

# Create logger
logger = ErrorLogger("my.component")

# Log errors with correlation tracking
correlation_id = logger.log_error(
    error,
    level=logging.ERROR,
    context={"operation": "startup"}
)

# Global convenience function
log_error(error, context={"user": "admin"})
```

### Security Features

#### Credential Sanitization

All error messages are automatically sanitized to remove sensitive information:

```python
from amplihack.errors import sanitize_error_message

message = "API call failed: api_key=sk-1234567890abcdef"
safe_message = sanitize_error_message(message)
# Result: "API call failed: api_key=***"
```

Sanitized patterns include:

- API keys and tokens
- Bearer tokens
- SSH private keys
- URLs with credentials
- File paths in home directories
- Email addresses
- Environment variables

#### Path Security

File paths are validated for security:

```python
from amplihack.errors import sanitize_path

# Safe path sanitization
safe_path = sanitize_path("/Users/john/secret.txt")
# Result: "/Users/***/secret.txt"
```

### Error Templates

Consistent error message formatting:

```python
from amplihack.errors import format_error_message

# Use predefined templates
message = format_error_message(
    'PROCESS_FAILED',
    command='git clone',
    return_code=128
)
# Result: "Process 'git clone' failed with exit code 128"

# Available templates
ERROR_TEMPLATES = {
    'PROCESS_FAILED': "Process '{command}' failed with exit code {return_code}",
    'NETWORK_TIMEOUT': "Network request to '{url}' timed out after {timeout} seconds",
    'CONFIG_MISSING': "Required configuration '{key}' is missing",
    # ... and many more
}
```

## Integration Examples

### ProcessManager Integration

Enhanced process execution with retry and error handling:

```python
from amplihack.utils.process import ProcessManager

# Automatic retry on transient failures
result = ProcessManager.run_command(["git", "clone", "repo.git"])

# Safe execution (returns None on failure)
result = ProcessManager.run_command_safe(["risky", "command"])
```

### ProxyManager Integration

Robust proxy management with fallbacks:

```python
from amplihack.proxy.manager import ProxyManager

manager = ProxyManager()

# Automatic retry on installation/startup failures
success = manager.start_proxy()

# Comprehensive error handling for all failure modes
if not success:
    # Detailed error information available in logs
    pass
```

### UVXManager Integration

Secure path validation and error recovery:

```python
from amplihack.uvx.manager import UVXManager

manager = UVXManager()

# Path security validation built-in
framework_path = manager.get_framework_path()
if framework_path and manager.validate_path_security(framework_path):
    # Safe to use path
    pass
```

## Best Practices

### 1. Always Use Correlation IDs

```python
# Good: Set correlation ID for operation tracking
correlation_id = set_correlation_id("user-action-123")
try:
    risky_operation()
except AmplihackError as e:
    # Error automatically includes correlation ID
    log_error(e)
```

### 2. Create Structured Errors

```python
# Good: Provide context and structure
raise ProcessError(
    "Git clone failed",
    command="git clone repo.git",
    return_code=128,
    correlation_id=get_correlation_id(),
    context={"repository": "user/repo"}
)

# Avoid: Generic error messages
raise Exception("Something went wrong")
```

### 3. Use Appropriate Retry Configurations

```python
# Good: Reasonable retry limits
@retry_on_error(RetryConfig(max_attempts=3, max_delay=10.0))
def network_operation():
    pass

# Avoid: Excessive retries
@retry_on_error(RetryConfig(max_attempts=100, max_delay=300.0))  # Too much!
```

### 4. Leverage Error Templates

```python
# Good: Consistent formatting
message = format_error_message(
    'NETWORK_TIMEOUT',
    url=url,
    timeout=timeout
)

# Avoid: Manual string formatting
message = f"Network request to {url} timed out after {timeout} seconds"
```

### 5. Security Considerations

```python
# Good: Errors are automatically sanitized
try:
    api_call(api_key="sk-secret123")  # pragma: allowlist secret
except Exception as e:
    log_error(ProcessError(str(e)))  # Credentials automatically removed

# Good: Validate paths before use
if manager.validate_path_security(user_path):
    process_file(user_path)
else:
    raise SecurityError("Invalid path detected")
```

## Testing

The error handling system includes comprehensive tests:

```bash
# Run all error handling tests
pytest tests/test_error_handling_comprehensive.py -v

# Run retry mechanism tests
pytest tests/test_retry_mechanisms.py -v

# Run logging and correlation tests
pytest tests/test_error_logging_correlation.py -v

# Run integration tests
pytest tests/test_error_recovery_integration.py -v
```

## Migration Guide

### From Basic Exception Handling

**Before:**

```python
try:
    subprocess.run(["command"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e}")
```

**After:**

```python
from amplihack.errors import ProcessError, retry_on_error, set_correlation_id

correlation_id = set_correlation_id("operation-123")

@retry_on_error()
def run_command():
    result = subprocess.run(["command"], check=True)
    return result

try:
    result = run_command()
except ProcessError as e:
    # Structured error with correlation ID and retry logic
    log_error(e)
```

### From Manual Retry Logic

**Before:**

```python
for attempt in range(3):
    try:
        return risky_operation()
    except Exception as e:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)
```

**After:**

```python
@retry_on_error(RetryConfig(max_attempts=3, base_delay=1.0))
def risky_operation():
    # Automatic retry with exponential backoff
    pass
```

## Performance Impact

The error handling system is designed for minimal performance overhead:

- **<5% performance impact** on normal operations
- **Thread-local correlation IDs** - no global state
- **Lazy initialization** - components only created when needed
- **Efficient sanitization** - regex patterns optimized for speed
- **Configurable logging** - can be disabled in production if needed

## Configuration

Error handling behavior can be configured via environment variables:

```bash
# Disable retry on specific error types (comma-separated)
export AMPLIHACK_NO_RETRY_ERRORS="SecurityError,ValidationError"

# Set default retry budget (seconds)
export AMPLIHACK_DEFAULT_RETRY_BUDGET="300"

# Configure logging level for error system
export AMPLIHACK_ERROR_LOG_LEVEL="INFO"
```

## Troubleshooting

### Common Issues

1. **Correlation IDs not appearing in logs**
   - Ensure `set_correlation_id()` is called before operations
   - Check that logger has `CorrelationFilter` applied

2. **Retries not working as expected**
   - Verify error type is in `retryable_errors`
   - Check retry budget isn't exhausted
   - Ensure max_attempts > 1

3. **Sensitive data in logs**
   - Verify `sanitize_error_message()` is being called
   - Check sanitization patterns cover your data format
   - Consider custom sanitization rules

### Debug Mode

Enable detailed error handling logs:

```python
import logging
logging.getLogger('amplihack.errors').setLevel(logging.DEBUG)
```

This provides detailed information about:

- Retry attempts and decisions
- Correlation ID propagation
- Error classification
- Sanitization operations

## Future Enhancements

Planned improvements for the error handling system:

1. **Metrics Integration** - Export retry/error metrics to monitoring systems
2. **Circuit Breakers** - Automatic service degradation on repeated failures
3. **Error Aggregation** - Group similar errors for better analysis
4. **Custom Retry Strategies** - Beyond exponential backoff
5. **Error Recovery Suggestions** - AI-powered error resolution hints

## Contributing

When contributing to the error handling system:

1. **Add tests** for new error types or retry scenarios
2. **Update templates** when adding new error message patterns
3. **Consider security** implications of any new error information
4. **Maintain backwards compatibility** with existing error interfaces
5. **Document new features** in this README

## References

- [Issue #179: Comprehensive Error Handling](https://github.com/example/repo/issues/179)
- [Architecture Specifications](../../../Specs/error_handling_architecture.md)
- [Security Requirements](../../../Specs/error_handling_security.md)
- [Test Requirements](../../../tests/test_error_handling_comprehensive.py)
