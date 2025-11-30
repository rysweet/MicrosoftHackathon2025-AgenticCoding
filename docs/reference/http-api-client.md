# API Client Reference

Complete reference for the simple HTTP API client.

## Installation

```python
from api_client import APIClient, ClientConfig, APIError, HTTPError
```

## APIClient Class

Simple HTTP client with authentication and retry logic.

```python
from api_client import APIClient

# Simple usage
client = APIClient("https://api.example.com")

# With authentication
client = APIClient("https://api.example.com", api_key="secret")
# OR
client = APIClient("https://api.example.com", bearer_token="token")

# With config object
config = ClientConfig(
    base_url="https://api.example.com",
    api_key="secret",
    timeout=60,
    max_retries=5
)
client = APIClient(config=config)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| base_url | str | None | Base URL for all requests |
| api_key | str | None | API key for x-api-key header |
| bearer_token | str | None | Bearer token for Authorization header |
| config | ClientConfig | None | Full configuration (overrides other params) |

### Methods

#### get(path, **kwargs)

Make GET request.

```python
response = client.get("/users/123", params={"include": "profile"})
data = response.json()
```

**Parameters:**
- `path` (str): URL path to append to base_url
- `params` (dict): Query parameters
- `headers` (dict): Additional headers

**Returns:** APIResponse object

#### post(path, json_data=None, **kwargs)

Make POST request.

```python
response = client.post("/users", json_data={"name": "Alice"})
```

**Parameters:**
- `path` (str): URL path
- `json_data` (dict): JSON body

**Returns:** APIResponse object

#### put(path, json_data=None, **kwargs)

Make PUT request.

```python
response = client.put("/users/123", json_data={"name": "Bob"})
```

**Parameters:** Same as `post()`

**Returns:** APIResponse object

#### delete(path, **kwargs)

Make DELETE request.

```python
response = client.delete("/users/123")
```

**Parameters:** Same as `get()`

**Returns:** APIResponse object

## ClientConfig Class

Configuration container for the API client.

```python
from api_client import ClientConfig

config = ClientConfig(
    base_url="https://api.example.com",
    api_key="secret-key",  # OR bearer_token, not both
    timeout=30,
    max_retries=3
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| base_url | str | Required | Base URL (must start with http:// or https://) |
| api_key | str | None | API key for authentication |
| bearer_token | str | None | Bearer token for authentication |
| timeout | int | 30 | Request timeout in seconds |
| max_retries | int | 3 | Maximum retry attempts for 5xx errors |

**Note:** You cannot set both `api_key` and `bearer_token`. Choose one authentication method.

## APIResponse Class

Response object from API requests.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| status_code | int | HTTP status code |
| headers | dict | Response headers |
| content | bytes | Raw response body |
| text | str | Response as UTF-8 text |
| url | str | Request URL |
| ok | bool | True if status is 2xx |

### Methods

#### json()

Parse response as JSON.

```python
response = client.get("/data")
data = response.json()  # Parses JSON and caches result
```

## Exceptions

### APIError

Base exception for all API client errors.

```python
class APIError(Exception):
    """Base exception for API client."""
```

### HTTPError

HTTP error responses (4xx, 5xx).

```python
class HTTPError(APIError):
    def __init__(self, status_code: int, message: str, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
```

**Properties:**
- `status_code` (int): HTTP status code
- `response_body` (str): Response body text

## Error Handling

```python
from api_client import APIClient, HTTPError, APIError

client = APIClient("https://api.example.com", api_key="secret")

try:
    response = client.get("/protected")
    data = response.json()
except HTTPError as e:
    if e.status_code == 401:
        print("Authentication failed")
    elif e.status_code == 404:
        print("Not found")
    else:
        print(f"HTTP {e.status_code}")
except APIError as e:
    print(f"Request failed: {e}")
```

## Retry Behavior

The client automatically retries requests that fail with 5xx errors.

### Retry Logic

- **What gets retried:** Only 5xx server errors
- **How many times:** Up to `max_retries` times (default 3)
- **Backoff strategy:** Exponential backoff (0.5s, 1s, 2s, 4s, etc.)
- **Maximum delay:** No cap on backoff time

### Example Delays

| Attempt | Delay |
|---------|-------|
| 1 | 0.5 seconds |
| 2 | 1 second |
| 3 | 2 seconds |
| 4 | 4 seconds |

## Thread Safety

The APIClient is thread-safe and can be shared across threads:

```python
from concurrent.futures import ThreadPoolExecutor

client = APIClient("https://api.example.com", api_key="key")

def fetch(path):
    return client.get(path).json()

with ThreadPoolExecutor(max_workers=10) as executor:
    paths = [f"/data/{i}" for i in range(100)]
    results = list(executor.map(fetch, paths))
```

## Complete Examples

### Basic API Integration

```python
from api_client import APIClient, HTTPError

# Initialize client
client = APIClient("https://jsonplaceholder.typicode.com")

# GET request
response = client.get("/users/1")
if response.ok:
    user = response.json()
    print(f"User: {user['name']}")

# POST request
response = client.post("/posts", json_data={
    "title": "Hello World",
    "body": "This is my post",
    "userId": 1
})
post = response.json()
print(f"Created post {post['id']}")
```

### With Authentication

```python
from api_client import APIClient, ClientConfig

# Using config for more control
config = ClientConfig(
    base_url="https://api.github.com",
    bearer_token="ghp_your_token_here",
    timeout=60,
    max_retries=5
)

client = APIClient(config=config)

try:
    # Get authenticated user
    response = client.get("/user")
    user = response.json()
    print(f"Authenticated as {user['login']}")

    # Create a gist
    response = client.post("/gists", json_data={
        "description": "My gist",
        "public": True,
        "files": {
            "test.py": {"content": "print('Hello')"}
        }
    })
    gist = response.json()
    print(f"Created gist: {gist['html_url']}")

except HTTPError as e:
    print(f"API error {e.status_code}: {e.response_body}")
```

## Limitations

This is a simple client. It does NOT support:

- Async/await (use aiohttp for that)
- OAuth flows (use requests-oauthlib)
- Automatic pagination
- Request signing (AWS, etc.)
- Multipart uploads
- Cookie handling
- Session management
- Proxy configuration
- Custom SSL certificates
- Streaming responses

If you need these features, consider using `requests` or `httpx` instead.

## See Also

- [How-To Guide](../howto/http-api-client.md) - Common usage patterns
- [Tutorial](../tutorials/http-api-client.md) - Step-by-step learning guide