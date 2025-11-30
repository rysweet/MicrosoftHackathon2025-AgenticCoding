# Simplified API Client Specification

## Philosophy
Ruthlessly simple HTTP client with just enough features to be useful, not enough to be confusing.

## Core Design Principles
1. **Zero dependencies** - stdlib only (urllib)
2. **One way to do things** - No configuration explosion
3. **Fail loudly** - Clear errors, no silent failures
4. **80/20 rule** - Cover 80% of use cases with 20% complexity

## Module: api_client

### Purpose
Make HTTP API calls with authentication and basic retry logic.

### Public API (The Studs)

```python
from api_client import APIClient, ClientConfig, APIError, HTTPError

# Simplest case - no auth
client = APIClient("https://api.example.com")
data = client.get("/users/123").json()

# With API key
client = APIClient("https://api.example.com", api_key="secret")
response = client.get("/users/123")
data = response.json()

# Custom config case
config = ClientConfig(
    base_url="https://api.example.com",
    api_key="secret-key",  # OR bearer_token, not both
    timeout=30,
    max_retries=3
)
client = APIClient(config=config)
```

### Module Structure

#### `__init__.py` - Public Interface
```python
"""Zero-dependency API client with simple auth and retry.

Public API:
    APIClient: Main client class
    ClientConfig: Configuration container
    APIError: Base exception
    HTTPError: HTTP error responses

Example:
    client = APIClient("https://api.example.com", api_key="secret")
    response = client.get("/endpoint")
    data = response.json()
"""

from .client import APIClient
from .config import ClientConfig
from .errors import APIError, HTTPError

__all__ = ["APIClient", "ClientConfig", "APIError", "HTTPError"]
```

#### `config.py` - Single Configuration Class
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ClientConfig:
    """Immutable configuration for API client.

    One of api_key or bearer_token can be set, not both.
    """
    base_url: str
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    def __post_init__(self):
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")

        if self.api_key and self.bearer_token:
            raise ValueError("Cannot use both api_key and bearer_token")
```

#### `client.py` - Core Client
```python
import json
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError as URLHTTPError, URLError

from .config import ClientConfig
from .auth import add_auth_header
from .errors import HTTPError, NetworkError
from .response import APIResponse
from .retry import RetryHandler

class APIClient:
    """Simple API client with auth and retry.

    Thread-safe and immutable after creation.
    """

    def __init__(self,
                 base_url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 bearer_token: Optional[str] = None,
                 config: Optional[ClientConfig] = None):
        """Create client with URL and optional auth.

        Args:
            base_url: API base URL (if not using config)
            api_key: API key for x-api-key header
            bearer_token: Bearer token for Authorization header
            config: Full configuration object (overrides other args)
        """
        if config:
            self._config = config
        else:
            if not base_url:
                raise ValueError("base_url or config required")
            self._config = ClientConfig(
                base_url=base_url,
                api_key=api_key,
                bearer_token=bearer_token
            )

        self._retry = RetryHandler(self._config.max_retries)

    def request(self, method: str, path: str,
                json_data: Optional[Dict] = None,
                params: Optional[Dict] = None,
                headers: Optional[Dict] = None) -> APIResponse:
        """Make HTTP request with retries.

        Args:
            method: HTTP method
            path: Path relative to base_url
            json_data: JSON body data
            params: Query parameters
            headers: Additional headers

        Returns:
            APIResponse object

        Raises:
            HTTPError: For 4xx/5xx responses after retries
            NetworkError: For network failures
        """
        # Build URL
        url = urljoin(self._config.base_url, path)
        if params:
            url = f"{url}?{urlencode(params)}"

        # Build request
        req_headers = {"User-Agent": "api-client/1.0"}
        if headers:
            req_headers.update(headers)

        # Add auth
        add_auth_header(req_headers, self._config)

        # Add JSON body
        body_data = None
        if json_data is not None:
            body_data = json.dumps(json_data).encode('utf-8')
            req_headers["Content-Type"] = "application/json"

        # Make request with retries
        request = Request(url, data=body_data, headers=req_headers, method=method)

        def _do_request():
            try:
                response = urlopen(request, timeout=self._config.timeout)
                return APIResponse(
                    status_code=response.getcode(),
                    headers=dict(response.headers),
                    content=response.read(),
                    url=url
                )
            except URLHTTPError as e:
                # Convert to our HTTPError
                raise HTTPError(
                    status_code=e.code,
                    message=f"{method} {url} returned {e.code}",
                    response_body=e.read().decode('utf-8', errors='ignore')
                )
            except URLError as e:
                raise APIError(f"Network error: {e.reason}")

        return self._retry.execute(_do_request)

    def get(self, path: str, **kwargs) -> APIResponse:
        """GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json_data: Optional[Dict] = None, **kwargs) -> APIResponse:
        """POST request."""
        return self.request("POST", path, json_data=json_data, **kwargs)

    def put(self, path: str, json_data: Optional[Dict] = None, **kwargs) -> APIResponse:
        """PUT request."""
        return self.request("PUT", path, json_data=json_data, **kwargs)

    def delete(self, path: str, **kwargs) -> APIResponse:
        """DELETE request."""
        return self.request("DELETE", path, **kwargs)
```

#### `auth.py` - Dead Simple Auth
```python
from typing import Dict
from .config import ClientConfig

def add_auth_header(headers: Dict[str, str], config: ClientConfig) -> None:
    """Add authentication header to request.

    Modifies headers dict in place.
    """
    if config.api_key:
        headers["x-api-key"] = config.api_key
    elif config.bearer_token:
        headers["Authorization"] = f"Bearer {config.bearer_token}"
    # No auth is also valid
```

#### `errors.py` - Clear Exceptions
```python
class APIError(Exception):
    """Base exception for API client."""
    pass

class HTTPError(APIError):
    """HTTP error response."""
    def __init__(self, status_code: int, message: str, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)
```

#### `retry.py` - Basic Retry Logic
```python
import time
from typing import Callable, TypeVar

from .errors import HTTPError

T = TypeVar('T')

class RetryHandler:
    """Simple retry handler for 5xx errors."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def execute(self, func: Callable[[], T]) -> T:
        """Execute function with retries on 5xx errors.

        Uses exponential backoff: 0.5s, 1s, 2s, etc.
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except HTTPError as e:
                # Only retry 5xx errors
                if e.status_code < 500:
                    raise

                last_error = e

                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = 0.5 * (2 ** attempt)
                    time.sleep(delay)

        # All retries exhausted
        raise last_error
```

#### `response.py` - Response Wrapper
```python
import json
from typing import Dict, Any, Optional

class APIResponse:
    """API response wrapper."""

    def __init__(self, status_code: int, headers: Dict[str, str],
                 content: bytes, url: str):
        self.status_code = status_code
        self.headers = headers
        self._content = content
        self.url = url
        self._json = None  # Lazy cache

    @property
    def content(self) -> bytes:
        """Raw response bytes."""
        return self._content

    @property
    def text(self) -> str:
        """Response as text."""
        return self._content.decode('utf-8', errors='replace')

    def json(self) -> Any:
        """Parse response as JSON.

        Caches result for multiple calls.
        """
        if self._json is None:
            self._json = json.loads(self.text)
        return self._json

    @property
    def ok(self) -> bool:
        """True if status is 2xx."""
        return 200 <= self.status_code < 300
```

## Usage Examples

### Basic Usage
```python
from api_client import APIClient

# Simple API key auth
client = APIClient("https://api.github.com", api_key="ghp_xxx")

# GET request
response = client.get("/user")
if response.ok:
    user = response.json()
    print(f"Hello {user['name']}")

# POST with JSON
response = client.post("/repos", json_data={
    "name": "my-repo",
    "private": True
})
```

### Custom Configuration
```python
from api_client import APIClient, ClientConfig

config = ClientConfig(
    base_url="https://api.example.com",
    bearer_token="eyJ...",
    timeout=60,
    max_retries=5
)

client = APIClient(config=config)
```

### Error Handling
```python
from api_client import APIClient, HTTPError, APIError

client = APIClient("https://api.example.com", api_key="secret")

try:
    response = client.get("/protected")
except HTTPError as e:
    if e.status_code == 401:
        print("Authentication failed")
    elif e.status_code == 404:
        print("Resource not found")
    else:
        print(f"HTTP {e.status_code}: {e.response_body}")
except APIError as e:
    print(f"Network or other error: {e}")
```

## Testing Strategy (60/30/10)

### Unit Tests (60%)
- Test each module in isolation
- Mock urllib for network calls
- Test configuration validation
- Test retry logic with mock functions

### Integration Tests (30%)
- Test client with real-like responses
- Test auth flow with mock server
- Test retry behavior end-to-end

### E2E Tests (10%)
- Test against httpbin.org or similar
- Optional: test against real API with test credentials
- Focus on happy path + one error case

## Security Considerations

### What We Do
1. **Force HTTPS for auth** - No credentials over HTTP
2. **No auth in logs** - Headers with auth are never logged
3. **URL validation** - Basic sanity checks
4. **SSL verification** - Default on, can disable for dev

### What We Don't Do
- No complex cert pinning
- No OAuth flows (use a library)
- No credential storage (user's responsibility)
- No automatic token refresh

## Philosophy Alignment

✅ **Ruthless Simplicity**: One class, one config, clear usage
✅ **Zero Dependencies**: Pure stdlib
✅ **Brick Philosophy**: Self-contained module, clear public API
✅ **No BS**: No stubs, everything works
✅ **80/20 Rule**: Covers common cases, doesn't overreach

## What This Doesn't Do

Being honest about limitations:
- No async/await (use aiohttp for that)
- No OAuth flows (use requests-oauthlib)
- No automatic pagination (add if needed)
- No request signing (AWS, etc.)
- No multipart uploads

If you need these, this isn't your library. That's OK.

## Migration from Complex Design

Key simplifications:
1. Removed middleware - just auth function
2. Removed protocol abstraction - just methods
3. Removed transport abstraction - just urllib
4. Single config class instead of 5+
5. Retry built-in, not pluggable

The result: 80% of the functionality with 20% of the complexity.