# How to Use the API Client

Quick guide for common API client tasks.

## Quick Start

```python
from api_client import APIClient

# Create client and make request
client = APIClient("https://api.example.com")
data = client.get("/users/123").json()
print(data)
```

## Common Tasks

### Making Different Request Types

```python
# GET request
response = client.get("/users", params={"limit": 10})

# POST with JSON
response = client.post("/users", json_data={"name": "Alice"})

# PUT to update
response = client.put("/users/123", json_data={"name": "Bob"})

# DELETE resource
response = client.delete("/users/123")
```

### Handling Responses

```python
response = client.get("/data")

# Check status
if response.ok:  # True if 2xx
    # Access JSON data
    data = response.json()

    # Or raw text
    text = response.text

    # Check headers
    content_type = response.headers.get("content-type")
```

### Error Handling

```python
from api_client import APIClient, APIError, HTTPError

client = APIClient("https://api.example.com")

try:
    response = client.get("/protected")
    data = response.json()
except HTTPError as e:
    # HTTP errors (4xx, 5xx)
    if e.status_code == 401:
        print("Authentication required")
    elif e.status_code == 404:
        print("Not found")
    else:
        print(f"HTTP {e.status_code}: {e.response_body}")
except APIError as e:
    # Network errors, timeouts, etc.
    print(f"Request failed: {e}")
```

### Configuration

```python
from api_client import APIClient, ClientConfig

# Simple with API key
client = APIClient("https://api.example.com", api_key="secret-key")

# Or with config object
config = ClientConfig(
    base_url="https://api.example.com",
    api_key="secret-key",  # OR bearer_token, not both
    timeout=60,
    max_retries=5
)
client = APIClient(config=config)

# Retries happen automatically for 5xx errors only
```

### Authentication

```python
# API key authentication
client = APIClient("https://api.example.com", api_key="my-api-key")

# Bearer token authentication
client = APIClient("https://api.example.com", bearer_token="jwt-token")

```

## Complete Example

```python
from api_client import APIClient, HTTPError

# Create client with API key
client = APIClient("https://api.github.com", api_key="ghp_xxx")

# Fetch user data
try:
    response = client.get("/user")
    if response.ok:
        user = response.json()
        print(f"Hello {user['name']}")

    # Create a repository
    response = client.post("/user/repos", json_data={
        "name": "my-repo",
        "private": True
    })
    repo = response.json()
    print(f"Created: {repo['html_url']}")

except HTTPError as e:
    print(f"Request failed with {e.status_code}")
```

## Next Steps

- See [API Reference](../reference/http-api-client.md) for complete API details
- Check [Tutorial](../tutorials/http-api-client.md) for step-by-step learning