# Rate Limiter Module

A production-ready rate limiting protection system for API calls with exponential backoff, token budget management, and thread-safe operation.

## Purpose

This module provides comprehensive rate limiting protection to prevent API overload while maximizing throughput and ensuring zero work loss through intelligent retry mechanisms.

## Key Features

### 1. Exponential Backoff

- Initial delay: 1 second
- Exponential growth: 2x per retry
- Maximum delay: 60 seconds
- Jitter: ±10% randomization to prevent thundering herd
- Automatic reset after success

### 2. Token Budget System

- Initial capacity: 1000 tokens
- Refill rate: 100 tokens/minute
- Thread-safe token management
- Automatic budget tracking

### 3. Thread Safety

- All operations are thread-safe
- Concurrent request handling
- Lock-free token bucket implementation where possible

### 4. User Feedback

- Progress indicators during delays
- Estimated wait time display
- Retry attempt counter
- Clear error messages

### 5. State Preservation

- All retries preserve original state
- No work loss on failure
- Automatic state recovery

## Public Interface

```python
from amplihack.rate_limiter import RateLimiter, RateLimitConfig

# Create rate limiter with custom config
config = RateLimitConfig(
    initial_tokens=1000,
    refill_rate=100,  # tokens per minute
    max_retries=5,
    initial_delay=1.0,
    max_delay=60.0,
    jitter_factor=0.1
)
limiter = RateLimiter(config)

# Execute API call with protection
async def api_call():
    # Your API call here
    pass

result = await limiter.execute(api_call)
```

## Architecture

```
rate_limiter/
├── __init__.py       # Public exports
├── README.md         # This file
├── core.py           # Main RateLimiter class
├── models.py         # Configuration and state models
├── backoff.py        # Exponential backoff implementation
└── token_budget.py   # Token bucket algorithm
```

## Components

### Core (core.py)

Main `RateLimiter` class that orchestrates rate limiting strategies.

### Models (models.py)

- `RateLimitConfig`: Configuration for rate limiting behavior
- `RateLimitState`: Current state tracking
- `RetryResult`: Result of retry operations

### Backoff (backoff.py)

Exponential backoff with jitter implementation:

- Calculate next delay
- Add randomized jitter
- Reset on success

### Token Budget (token_budget.py)

Token bucket implementation:

- Thread-safe token management
- Automatic refill calculation
- Capacity enforcement

## Usage Examples

### Basic Usage

```python
from amplihack.rate_limiter import RateLimiter

limiter = RateLimiter()

# Protect an API call
async def fetch_data():
    response = await http_client.get("/api/data")
    return response.json()

data = await limiter.execute(fetch_data)
```

### Custom Configuration

```python
from amplihack.rate_limiter import RateLimiter, RateLimitConfig

config = RateLimitConfig(
    initial_tokens=500,     # Start with 500 tokens
    refill_rate=50,        # 50 tokens per minute
    max_retries=3,         # Maximum 3 retries
    initial_delay=2.0,     # Start with 2 second delay
    max_delay=30.0,        # Cap at 30 seconds
    jitter_factor=0.2      # 20% jitter
)

limiter = RateLimiter(config)
```

### With Progress Callback

```python
def on_progress(attempt: int, delay: float, tokens: int):
    print(f"Retry {attempt}: waiting {delay:.1f}s, {tokens} tokens remaining")

result = await limiter.execute(
    api_call,
    progress_callback=on_progress
)
```

### Batch Operations

```python
# Process multiple items with rate limiting
async def process_batch(items):
    results = []
    for item in items:
        result = await limiter.execute(
            lambda: process_item(item)
        )
        results.append(result)
    return results
```

## Error Handling

The module handles several error scenarios:

1. **Rate Limit Exceeded**: Automatic retry with backoff
2. **Token Exhaustion**: Wait for refill and retry
3. **Max Retries Exceeded**: Raise `RateLimitExhausted` exception
4. **API Errors**: Distinguish between rate limits and other errors

## Thread Safety

All components are designed for concurrent use:

- Token bucket uses thread-safe operations
- Backoff calculations are stateless
- State tracking uses proper locking

## Testing

Comprehensive test coverage including:

- Unit tests for each component
- Integration tests for complete flows
- Concurrency tests for thread safety
- Performance tests for throughput

## Module Contract

### Inputs

- Async function to execute
- Optional configuration
- Optional progress callback

### Outputs

- Function result on success
- `RateLimitExhausted` exception after max retries
- Progress updates via callback

### Side Effects

- Delays execution when rate limited
- Consumes tokens from budget
- Logs retry attempts

### Guarantees

- Zero work loss on retries
- Thread-safe operation
- Predictable backoff behavior
- Token budget enforcement
