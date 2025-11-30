# Implementation Specification

## Module Structure

```
api_client/
├── __init__.py         # Public API exports via __all__
├── core.py            # Main implementation using urllib
├── contracts.py       # Import from api_client_design/contracts.py
├── retry.py           # Retry logic implementation
├── middleware.py      # Middleware processing
├── utils.py           # URL encoding, JSON handling
└── tests/
    ├── test_client.py
    ├── test_retry.py
    └── test_thread_safety.py
```

## Implementation Requirements

### 1. Core Implementation (`core.py`)

Must implement the `RESTClient.request()` method with:

- **urllib only** - No external dependencies
- **Thread-safe** - No shared mutable state
- **Middleware pipeline** - Process in correct order
- **Retry handling** - With configurable strategy
- **Timeout support** - Using urllib timeout parameter

### 2. URL Building

```python
def build_url(base: str, path: str, params: Optional[Dict[str, str]]) -> str:
    """Build complete URL with query parameters."""
    # Handle base_url + path joining
    # Encode query parameters properly
    # Return complete URL
```

### 3. Request Execution Flow

```
1. Merge configuration with request
2. Apply request middleware (in order)
3. Build URL with parameters
4. Serialize JSON body if provided
5. Make HTTP request with urllib
6. Handle retries on failure
7. Apply response middleware (reverse order)
8. Return Response object
```

### 4. Error Handling

Map urllib exceptions to our exception hierarchy:

- `urllib.error.URLError` → `ConnectionError`
- `socket.timeout` → `TimeoutError`
- `urllib.error.HTTPError` → `HTTPError`

### 5. Thread Safety Requirements

- No instance variables that change after `__init__`
- Use local variables in methods
- Configuration is immutable (dataclass frozen or copying)
- Middleware lists are copied before iteration

## Critical Implementation Details

### JSON Handling

```python
# Request
if request.json_body is not None:
    data = json.dumps(request.json_body).encode('utf-8')
    headers['Content-Type'] = 'application/json'

# Response
def json(self) -> Any:
    return json.loads(self.body.decode('utf-8'))
```

### Retry Logic

```python
def execute_with_retry(self, request: Request) -> Response:
    last_error = None

    for attempt in range(self.config.max_retries):
        try:
            response = self._execute_request(request)

            if self._retry_strategy:
                if not self._retry_strategy.should_retry(attempt, None, response):
                    return response
            elif response.status_code not in self.config.retry_on:
                return response

            delay = self._get_retry_delay(attempt)
            time.sleep(delay)

        except Exception as e:
            last_error = e
            if self._retry_strategy:
                if not self._retry_strategy.should_retry(attempt, e, None):
                    raise
            elif attempt == self.config.max_retries - 1:
                raise RetryExhausted(f"All {self.config.max_retries} attempts failed", last_error)

            delay = self._get_retry_delay(attempt)
            time.sleep(delay)

    raise RetryExhausted(f"All {self.config.max_retries} attempts failed", last_error)
```

### Middleware Processing

```python
def apply_request_middleware(self, request: Request) -> Request:
    """Apply all request middleware in order."""
    for middleware in self._request_middleware:
        request = middleware.process_request(request)
    return request

def apply_response_middleware(self, response: Response) -> Response:
    """Apply all response middleware in reverse order."""
    for middleware in reversed(self._response_middleware):
        response = middleware.process_response(response)
    return response
```

## Testing Requirements

### Unit Tests (60%)

- Test each method in isolation
- Mock urllib.request.urlopen
- Verify middleware ordering
- Check exception mapping

### Integration Tests (30%)

- Test against httpbin.org
- Verify retry behavior
- Test timeout handling
- Check concurrent requests

### E2E Tests (10%)

- Complete workflow tests
- Real API interactions
- Thread safety verification

## Performance Considerations

- Connection pooling not required (urllib handles it)
- Keep middleware lightweight
- Avoid unnecessary object creation
- Use lazy imports where sensible

## Security Notes

- Never log sensitive headers (Authorization, Cookie)
- Validate URLs before making requests
- Handle SSL verification properly
- Sanitize error messages

## Checklist for Implementation

- [ ] Import contracts from api_client_design
- [ ] Implement request() method with urllib
- [ ] Handle all HTTP methods
- [ ] Process middleware correctly
- [ ] Implement retry logic
- [ ] Map exceptions properly
- [ ] Ensure thread safety
- [ ] Add comprehensive tests
- [ ] Document public API
- [ ] Verify no external dependencies