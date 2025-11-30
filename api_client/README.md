# REST API Client Library

A ruthlessly simple REST API client library with clear contracts and thread-safe operation.

## Design Philosophy

This module follows the brick philosophy:

- **Single Responsibility**: HTTP client operations only
- **Clear Public API**: All public interfaces defined via `__all__`
- **Regeneratable**: Can be rebuilt from OpenAPI specification
- **Thread-Safe**: Immutable data models and synchronized operations
- **Zero-BS**: No stubs, placeholders, or unimplemented functions

## Module Structure

```
api_client/
├── __init__.py         # Public interface via __all__
├── openapi.yaml        # Complete contract specification
├── models.py           # Request/Response immutable data models
├── exceptions.py       # Exception hierarchy with clear semantics
├── config.py           # Configuration interfaces
├── client.py           # Main implementation
├── README.md           # This file
└── tests/              # Contract tests (not shown)
```

## Public API (The "Studs")

### Main Client

```python
from api_client import APIClient

# Initialize with config object
from api_client import APIClientConfig, RetryConfig, RateLimitConfig

config = APIClientConfig(
    base_url="https://api.example.com",
    timeout=30.0,
    retry_config=RetryConfig(
        max_retries=3,
        backoff_factor=2.0,
        retry_on_status=[429, 500, 502, 503, 504]
    ),
    rate_limit_config=RateLimitConfig(
        requests_per_second=10.0,
        burst_size=10
    ),
    headers={"User-Agent": "MyApp/1.0"}
)

client = APIClient(config)

# Or simple initialization with just URL
client = APIClient("https://api.example.com")
```

### Making Requests

```python
from api_client import Request, Response

# Using Request object (full control)
request = Request(
    method="GET",
    path="/users/123",
    params={"include": "profile"},
    headers={"Accept": "application/json"},
    timeout=10.0
)
response = client.request(request)

# Using convenience methods
response = client.get("/users/123", params={"include": "profile"})
response = client.post("/users", json_data={"name": "John"})
response = client.put("/users/123", json_data={"name": "Jane"})
response = client.patch("/users/123", json_data={"status": "active"})
response = client.delete("/users/123")
```

### Response Handling

```python
# Response properties
assert response.status_code == 200
assert response.is_success
assert not response.is_error

# Access data
json_data = response.json_data  # Parsed JSON
text = response.text             # Raw text
headers = response.headers       # Response headers
elapsed = response.elapsed       # Request duration

# Check status
response.raise_for_status()  # Raises exception for 4xx/5xx
```

### Exception Hierarchy

```python
from api_client import (
    APIException,           # Base exception
    RateLimitException,     # Rate limit exceeded
    TimeoutException,       # Request timeout
    NetworkException,       # Network connectivity issues
    ValidationException,    # Client errors (4xx)
    ServerException         # Server errors (5xx)
)

try:
    response = client.get("/resource")
except RateLimitException as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except TimeoutException as e:
    print(f"Request timed out after {e.timeout} seconds")
except NetworkException as e:
    print(f"Network error: {e.message}")
except ValidationException as e:
    print(f"Client error {e.status_code}: {e.message}")
except ServerException as e:
    print(f"Server error {e.status_code}: {e.message}")
except APIException as e:
    print(f"API error: {e.message}")
```

## Configuration

### Retry Configuration

```python
from api_client import RetryConfig

retry_config = RetryConfig(
    max_retries=3,                                   # Maximum retry attempts
    backoff_factor=2.0,                              # Exponential backoff multiplier
    retry_on_status=[429, 500, 502, 503, 504]       # Status codes to retry
)

# Calculate backoff time
wait_time = retry_config.calculate_backoff(attempt=2)  # Returns 2.0 seconds

# Check if should retry
should_retry = retry_config.should_retry(503)  # Returns True
```

### Rate Limiting Configuration

```python
from api_client import RateLimitConfig

rate_limit_config = RateLimitConfig(
    requests_per_second=10.0,  # Maximum sustained rate
    burst_size=10               # Maximum burst size
)

# Token bucket algorithm with burst support
# Can make 10 requests immediately, then 10/second sustained
```

## Thread Safety

All components are thread-safe:

1. **Immutable Data Models**: Request and Response objects are frozen dataclasses
2. **Synchronized Rate Limiting**: Token bucket with locks
3. **Configuration Immutability**: All config objects are frozen
4. **Client Thread Safety**: All client methods are thread-safe

```python
import threading

client = APIClient("https://api.example.com")

def worker(thread_id):
    response = client.get(f"/data/{thread_id}")
    print(f"Thread {thread_id}: {response.status_code}")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Logging

The library uses Python's standard logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Library uses logger named 'api_client'
logger = logging.getLogger('api_client')
logger.setLevel(logging.INFO)
```

## Error Response Format

The library expects standard error response format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": {
      "resource_type": "user",
      "resource_id": "123"
    }
  }
}
```

## Design Decisions

### Why urllib instead of requests/httpx?

- Standard library = zero dependencies
- Sufficient for REST API needs
- Thread-safe out of the box
- Simpler deployment

### Why immutable models?

- Thread safety without locks
- Clear modification patterns (create new instances)
- Prevents accidental mutation
- Easier to reason about

### Why explicit exception hierarchy?

- Clear error handling patterns
- Specific recovery strategies per error type
- Better debugging with context
- Follows fail-fast principle

### Why token bucket for rate limiting?

- Supports burst traffic
- Simple and proven algorithm
- Efficient implementation
- Fair resource allocation

## Testing

The module includes comprehensive contract tests:

```python
# Test public interface contract
def test_public_api():
    """Verify all public exports are available."""
    from api_client import (
        APIClient, Request, Response,
        APIException, RateLimitException, TimeoutException,
        NetworkException, ValidationException, ServerException,
        RetryConfig, RateLimitConfig
    )
    assert all([APIClient, Request, Response])

# Test thread safety
def test_thread_safety():
    """Verify concurrent access is safe."""
    # ... concurrent testing code ...

# Test retry behavior
def test_retry_with_backoff():
    """Verify exponential backoff works correctly."""
    # ... retry testing code ...
```

## Summary

This REST API client library provides:

- ✅ Clean, intuitive public API
- ✅ Immutable request/response models with validation
- ✅ Clear configuration contracts
- ✅ Comprehensive exception hierarchy
- ✅ Structured logging interfaces
- ✅ Thread-safety guarantees
- ✅ Zero external dependencies (standard library only)
- ✅ Regeneratable from OpenAPI specification

The design follows amplihack philosophy with ruthless simplicity, clear contracts (studs), and regeneratable modules (bricks).