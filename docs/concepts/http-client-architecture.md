# [PLANNED - Implementation Pending]

# HTTP Client Architecture

Understanding the design decisions behind the HTTP API Client.

## Design Philosophy

The HTTP API Client follows amplihack's core philosophy of ruthless simplicity. Every feature serves a clear purpose without unnecessary complexity.

### Simplicity First

We chose simplicity over flexibility:
- One way to make requests (async/await)
- Simple exponential backoff instead of complex retry strategies
- Basic rate limiting instead of circuit breakers
- Clear exception hierarchy instead of generic errors

### Why Async-Only?

The client is async-only because:
1. **Modern Python is async** - Most web frameworks (FastAPI, Starlette) are async
2. **Better performance** - Non-blocking I/O for concurrent requests
3. **Simpler implementation** - No need to maintain sync and async versions
4. **Future-proof** - Async is the direction Python is moving

## Core Components

### APIClient

The main client class is a simple wrapper around HTTP operations:

```
APIClient
├── Configuration (base_url, timeout, retries)
├── HTTP Methods (get, post, put, patch, delete)
├── Retry Logic (exponential backoff)
└── Error Handling (exception hierarchy)
```

### Request/Response Flow

```
User Code → APIClient → HTTP Request → Response/Error
                ↓                          ↓
            Retry Logic              Exception Mapping
                ↓                          ↓
            Backoff Wait              Specific Exception
                ↓                          ↓
            Retry Request             Raise to User
```

## Retry Strategy

### Simple Exponential Backoff

We use a simple exponential backoff formula:

```python
delay = min(1.0 * (2 ** attempt), 60)
```

This gives us:
- Attempt 1: 2 second wait
- Attempt 2: 4 second wait
- Attempt 3: 8 second wait
- Maximum: 60 second wait

### Why Not Circuit Breakers?

Circuit breakers add complexity for minimal benefit in most cases:
- They require state management
- They need configuration tuning
- Simple retries handle most failures well
- Users can implement their own if needed

## Exception Design

### Clear Hierarchy

```
APIError (base)
├── NetworkError (connection issues)
├── TimeoutError (request timeout)
├── ValidationError (bad parameters)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
├── RateLimitError (429)
└── ServerError (5xx)
```

### Why Specific Exceptions?

Specific exceptions allow users to:
- Handle different errors differently
- Write cleaner error handling code
- Understand what went wrong immediately
- Avoid parsing error messages

## Rate Limiting

### Respect Retry-After

When servers return 429 with `Retry-After` header:
1. Parse the header value
2. Wait exactly that long
3. Retry the request

When no header is present:
- Use exponential backoff
- Same as other retryable errors

### Why Not Token Buckets?

Token bucket algorithms are over-engineering for most APIs:
- APIs handle their own rate limiting
- Client-side limiting often guesses wrong
- Simple retry-after respect works better
- Less configuration needed

## Thread Safety

### Shared Client Pattern

```python
# One client, many threads
client = APIClient(base_url="https://api.example.com")

# Safe to share
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(client.get, path) for path in paths]
```

The client is thread-safe because:
- No mutable shared state
- Each request is independent
- Connection pooling handled by underlying library

## Logging Philosophy

### Structured Levels

- **DEBUG**: Full details for debugging
- **INFO**: Normal operation confirmation
- **WARNING**: Recoverable issues (retries)
- **ERROR**: Unrecoverable failures

### Why Comprehensive Logging?

Good logging helps users:
- Debug integration issues quickly
- Understand retry behavior
- Monitor API performance
- Troubleshoot production issues

## Migration Path

### From Popular Libraries

We provide migration guides because:
- Many projects use requests or aiohttp
- Migration should be straightforward
- Similar patterns reduce learning curve
- Clear mapping of concepts helps adoption

## What We Don't Include

### Features We Intentionally Omit

- **Middleware/Interceptors**: Add complexity, rarely needed
- **Request/Response Hooks**: Can be done in user code
- **Caching**: Better handled by dedicated libraries
- **Cookie Management**: Most APIs use tokens
- **Proxy Rotation**: Specialized use case
- **Custom Transports**: Over-engineering

### Why Less Is More

Each feature we don't add:
- Reduces maintenance burden
- Simplifies the mental model
- Makes the code easier to understand
- Allows users to add their own if needed

## Future Considerations

### Potential Additions

Features we might add if commonly requested:
- Streaming responses for large downloads
- WebSocket support for real-time APIs
- HTTP/2 support for better performance
- Request signing for AWS-style APIs

### Staying Simple

Any future additions must:
- Solve real user problems
- Not complicate basic usage
- Follow the same design philosophy
- Be optional and backward-compatible

## Summary

The HTTP API Client architecture prioritizes:
1. **Simplicity** - Easy to understand and use
2. **Reliability** - Automatic retries and clear errors
3. **Performance** - Async-first design
4. **Clarity** - Explicit over implicit

By keeping the design simple, we make it easier for users to:
- Get started quickly
- Debug issues effectively
- Extend functionality if needed
- Trust the client to do the right thing