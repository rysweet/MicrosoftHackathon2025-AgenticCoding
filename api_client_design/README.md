# API Client Design

Ruthlessly simple HTTP API client - just enough features to be useful, not enough to be confusing.

## Core Philosophy

**80/20 Rule**: Cover 80% of use cases with 20% of the complexity.

## What This Is

A simple, zero-dependency HTTP client that:
- Makes HTTP requests (GET, POST, PUT, DELETE)
- Handles authentication (API key or Bearer token)
- Retries 5xx errors automatically
- Returns clear, simple responses
- Has only 2 exceptions to handle

## What This Isn't

This client does NOT have:
- Async/await support
- OAuth flows
- Middleware or hooks
- Rate limiting beyond basic retry
- Complex configuration
- Automatic pagination
- Request signing
- Multipart uploads

## Public API

The entire public API is just 4 exports:

```python
from api_client import APIClient, ClientConfig, APIError, HTTPError
```

## Simple Usage

```python
from api_client import APIClient

# Simplest case
client = APIClient("https://api.example.com")
data = client.get("/users").json()

# With authentication
client = APIClient("https://api.example.com", api_key="secret")
response = client.post("/users", json_data={"name": "Alice"})

# Error handling
try:
    data = client.get("/protected").json()
except HTTPError as e:
    print(f"HTTP {e.status_code}")
except APIError as e:
    print(f"Request failed: {e}")
```

## Files

- `simplified_spec.md` - Complete technical specification
- `implementation_spec.md` - Detailed implementation guide
- `SECURITY_REQUIREMENTS.md` - Security considerations

## Documentation

User-facing documentation in `/docs/`:
- [Tutorial](../docs/tutorials/http-api-client.md) - 15-minute introduction
- [How-To Guide](../docs/howto/http-api-client.md) - Common patterns
- [API Reference](../docs/reference/http-api-client.md) - Complete reference

## Key Design Decisions

1. **Zero dependencies** - stdlib only (urllib)
2. **Simple config** - Just 4 parameters: base_url, timeout, max_retries, api_key
3. **Only 2 exceptions** - APIError (base) and HTTPError (HTTP errors)
4. **Built-in retry** - Automatic retry for 5xx errors only
5. **One auth method** - API key OR bearer token, not both
6. **`.json()` method** - Simple JSON parsing, not `.json_data`

## Implementation Status

**Status**: Design complete, ready for implementation

The design has been simplified per architect feedback to focus on the 80% use case with maximum clarity.