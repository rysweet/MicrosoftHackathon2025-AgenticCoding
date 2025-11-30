# REST API Client Reference

[PLANNED - Implementation Pending]

Simple REST client using only Python standard library (urllib).

## Quick Reference

```python
# [PLANNED] - Simple client with basic rate limiting
from amplihack.rest import RESTClient

# Create client
client = RESTClient(
    base_url="https://api.example.com",
    rate_limit=10  # Max 10 requests per second
)

# Make requests
response = client.get("/users/123")
response = client.post("/users", data={"name": "Alice"})
response = client.put("/users/123", data={"name": "Bob"})
response = client.delete("/users/123")
```

## Overview

The REST API Client provides a simple interface for making HTTP requests with built-in rate limiting and retry logic using only Python's standard library.

## Core Components

### RESTClient Class

The main client for making REST API calls.

```python
# [PLANNED]
class RESTClient:
    """Simple REST client with rate limiting."""

    def __init__(self, base_url: str, rate_limit: int = 10):
        """
        Initialize client.

        Args:
            base_url: API base URL (e.g., "https://api.example.com")
            rate_limit: Max requests per second (default: 10)
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limit = rate_limit
        self.last_request = 0
```

### Response Object

Simple dataclass for API responses.

```python
# [PLANNED]
@dataclass
class Response:
    """API response container."""
    status_code: int
    data: dict
    headers: dict
```

## Methods

### GET Request

```python
# [PLANNED]
response = client.get("/users/123")
if response.status_code == 200:
    print(response.data["name"])
```

### POST Request

```python
# [PLANNED]
response = client.post(
    "/users",
    data={"name": "Alice", "email": "alice@example.com"}
)
if response.status_code == 201:
    print(f"Created user: {response.data['id']}")
```

### PUT Request

```python
# [PLANNED]
response = client.put(
    "/users/123",
    data={"name": "Bob"}
)
```

### DELETE Request

```python
# [PLANNED]
response = client.delete("/users/123")
if response.status_code == 204:
    print("User deleted")
```

## Rate Limiting

Simple time-based rate limiting enforces a maximum requests per second.

```python
# [PLANNED] - Automatic rate limiting
client = RESTClient(
    base_url="https://api.example.com",
    rate_limit=5  # Max 5 requests per second
)

# Client automatically sleeps between requests to maintain rate
for user_id in range(1, 100):
    response = client.get(f"/users/{user_id}")  # Auto-throttled
```

## Error Handling

### Retry Logic

Simple exponential backoff for transient errors.

```python
# [PLANNED] - Automatic retry with exponential backoff
# Retries on: 429 (rate limit), 502 (bad gateway), 503 (unavailable)
# Backoff: 1s, 2s, 4s (max 3 retries)

response = client.get("/users/123")
# Automatically retries if server is temporarily unavailable
```

### Error Responses

All errors return Response objects with appropriate status codes.

```python
# [PLANNED]
response = client.get("/invalid/path")
if response.status_code == 404:
    print("Resource not found")
elif response.status_code >= 500:
    print(f"Server error: {response.status_code}")
```

## Complete Example

```python
# [PLANNED] - Full working example
from amplihack.rest import RESTClient

# Initialize client
client = RESTClient(
    base_url="https://jsonplaceholder.typicode.com",
    rate_limit=10
)

# Get user
response = client.get("/users/1")
if response.status_code == 200:
    user = response.data
    print(f"User: {user['name']} ({user['email']})")

# Create post
new_post = {
    "userId": 1,
    "title": "Hello World",
    "body": "This is my first post"
}
response = client.post("/posts", data=new_post)
if response.status_code == 201:
    print(f"Created post ID: {response.data['id']}")

# Update post
updates = {"title": "Updated Title"}
response = client.put("/posts/1", data=updates)

# Delete post
response = client.delete("/posts/1")
if response.status_code in [200, 204]:
    print("Post deleted")
```

## Implementation Details

### Dependencies

- **urllib**: Standard library for HTTP requests
- **time**: Standard library for rate limiting
- **json**: Standard library for JSON parsing
- **dataclasses**: Standard library for Response object

### Rate Limiting Algorithm

Simple time-based sleep between requests:

```python
# [PLANNED]
def _rate_limit(self):
    """Sleep if needed to maintain rate limit."""
    elapsed = time.time() - self.last_request
    min_interval = 1.0 / self.rate_limit
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    self.last_request = time.time()
```

### Retry Algorithm

Simple exponential backoff:

```python
# [PLANNED]
def _retry_request(self, method, path, **kwargs):
    """Retry with exponential backoff."""
    for attempt in range(3):
        response = self._make_request(method, path, **kwargs)
        if response.status_code not in [429, 502, 503]:
            return response
        if attempt < 2:
            time.sleep(2 ** attempt)  # 1s, 2s
    return response
```

## Limitations

This simple client intentionally omits:

- Authentication mechanisms (add as needed)
- Connection pooling (urllib handles basics)
- Async operations (use asyncio separately if needed)
- Complex retry strategies (simple exponential only)
- Request/response interceptors (not needed)

## See Also

- [HTTP module documentation](./http-utilities.md) - Lower-level HTTP utilities
- [Error handling guide](../howto/handle-api-errors.md) - Best practices for error handling