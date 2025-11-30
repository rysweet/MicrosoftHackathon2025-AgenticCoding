"""Usage Examples for REST API Client

Shows how to use the API client contracts in practice.
"""

from contracts import (
    RESTClient,
    ClientConfig,
    Request,
    HTTPMethod,
    HTTPError,
    RetryStrategy,
    RequestMiddleware,
)
import time


def basic_usage():
    """Simple GET request example."""
    client = RESTClient()

    # Simple GET
    response = client.get("https://api.github.com/user")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text()}")

    # With parameters
    response = client.get(
        "https://api.github.com/search/repositories",
        params={"q": "python", "sort": "stars"}
    )
    data = response.json()
    print(f"Found {data['total_count']} repositories")


def configured_client():
    """Client with base configuration."""
    config = ClientConfig(
        base_url="https://api.github.com",
        default_headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MyApp/1.0"
        },
        timeout=10.0,
        max_retries=5
    )

    client = RESTClient(config)

    # URL is relative to base_url
    response = client.get("/user")
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx

    # Create variant with different timeout
    fast_client = client.with_config(timeout=2.0)
    response = fast_client.get("/user")


def post_json_example():
    """POST request with JSON body."""
    client = RESTClient()

    response = client.post(
        "https://httpbin.org/post",
        json_body={"name": "test", "value": 123},
        headers={"Content-Type": "application/json"}
    )

    result = response.json()
    print(f"Echoed data: {result['json']}")


def error_handling():
    """Handle various error scenarios."""
    client = RESTClient()

    try:
        response = client.get("https://httpbin.org/status/404")
        response.raise_for_status()
    except HTTPError as e:
        print(f"HTTP Error: {e}")
        if e.response:
            print(f"Status: {e.response.status_code}")
            print(f"Body: {e.response.text()}")


def custom_retry_strategy():
    """Implement custom retry logic."""

    class ExponentialBackoffRetry:
        """Exponential backoff with jitter."""

        def should_retry(self, attempt, error, response):
            if attempt >= 3:
                return False
            if response and response.status_code in [429, 502, 503, 504]:
                return True
            return isinstance(error, ConnectionError)

        def get_delay(self, attempt):
            # 1s, 2s, 4s with jitter
            base_delay = 2 ** attempt
            jitter = 0.1 * base_delay
            return base_delay + jitter

    client = RESTClient()
    client.set_retry_strategy(ExponentialBackoffRetry())

    response = client.get("https://httpbin.org/delay/1")


def request_middleware_example():
    """Add authentication middleware."""

    class BearerAuthMiddleware:
        """Add bearer token to requests."""

        def __init__(self, token):
            self.token = token

        def process_request(self, request):
            request.headers["Authorization"] = f"Bearer {self.token}"
            return request

    client = RESTClient()
    client.add_request_middleware(BearerAuthMiddleware("secret-token"))

    # All requests will have Authorization header
    response = client.get("https://api.example.com/protected")


def batch_requests():
    """Make multiple requests efficiently."""
    import concurrent.futures

    client = RESTClient(ClientConfig(timeout=5.0))

    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/2",
        "https://httpbin.org/delay/3",
    ]

    # Thread-safe client allows parallel requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(client.get, url) for url in urls]
        responses = [f.result() for f in futures]

    for response in responses:
        print(f"URL: {response.url}, Status: {response.status_code}")


def direct_request_object():
    """Use Request object directly for complex requests."""
    client = RESTClient()

    request = Request(
        method=HTTPMethod.POST,
        url="https://httpbin.org/post",
        headers={
            "X-Custom-Header": "value",
            "Accept": "application/json"
        },
        json_body={"complex": {"nested": "data"}},
        timeout=15.0
    )

    response = client.request(request)
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    # Run examples
    print("=== Basic Usage ===")
    basic_usage()

    print("\n=== Configured Client ===")
    configured_client()

    print("\n=== POST JSON ===")
    post_json_example()

    print("\n=== Error Handling ===")
    error_handling()