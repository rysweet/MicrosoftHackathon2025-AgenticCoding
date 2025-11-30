#!/usr/bin/env python3
"""
Advanced usage examples for the REST API Client Library

These examples show retry configuration, rate limiting,
and custom extensions.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import (
    APIClient,
    Request,
    Response,
    RetryConfig,
    SimpleRateLimiter,
    RateLimiter,
    HTTPMethod,
    HTTPError,
    RateLimitError
)


def example_retry_configuration():
    """Configure automatic retries with exponential backoff"""
    print("=== Retry Configuration ===")

    # Configure aggressive retry strategy
    retry_config = RetryConfig(
        max_retries=5,
        backoff_factor=2.0,  # 2, 4, 8, 16, 32 seconds
        retry_on_status=(429, 500, 502, 503, 504)
    )

    client = APIClient(
        base_url="https://httpbin.org",
        retry_config=retry_config
    )

    print(f"Max retries: {retry_config.max_retries}")
    print(f"Backoff times: {[retry_config.get_backoff_time(i) for i in range(3)]}")
    print(f"Retry on status codes: {retry_config.retry_on_status}")

    # This would retry automatically on 503 errors
    try:
        response = client.get("/status/503")
    except HTTPError as e:
        print(f"Failed after retries: {e.message}")

    print()


def example_rate_limiting():
    """Rate limiting to respect API quotas"""
    print("=== Rate Limiting ===")

    # Limit to 2 requests per second with burst of 5
    rate_limiter = SimpleRateLimiter(
        requests_per_second=2,
        burst_size=5
    )

    client = APIClient(
        base_url="https://httpbin.org",
        rate_limiter=rate_limiter
    )

    print("Making 8 rapid requests (limited to 2/sec after burst)...")
    start_time = time.time()

    for i in range(8):
        response = client.get(f"/get?request={i}")
        elapsed = time.time() - start_time
        print(f"Request {i+1} completed at {elapsed:.1f}s")

    total_time = time.time() - start_time
    print(f"Total time for 8 requests: {total_time:.1f} seconds")
    print()


def example_custom_rate_limiter():
    """Implement a custom rate limiter"""
    print("=== Custom Rate Limiter ===")

    class LoggingRateLimiter:
        """Rate limiter that logs when limiting occurs"""

        def __init__(self, requests_per_second: float):
            self.requests_per_second = requests_per_second
            self.last_request = 0.0

        def acquire(self) -> None:
            now = time.time()
            if self.last_request > 0:
                elapsed = now - self.last_request
                min_interval = 1.0 / self.requests_per_second
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    print(f"  [Rate Limiter] Waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
            self.last_request = time.time()

        def reset(self) -> None:
            self.last_request = 0.0

    client = APIClient(
        base_url="https://httpbin.org",
        rate_limiter=LoggingRateLimiter(requests_per_second=3)
    )

    print("Making 3 requests with custom rate limiter...")
    for i in range(3):
        print(f"Request {i+1}...")
        client.get("/get")

    print()


def example_request_object():
    """Using Request objects directly"""
    print("=== Direct Request Objects ===")

    client = APIClient("https://httpbin.org")

    # Build request manually
    request = Request(
        method=HTTPMethod.POST,
        path="/post",
        headers={
            "X-Custom-Header": "CustomValue",
            "Content-Type": "application/json"
        },
        json={"key": "value", "number": 42},
        timeout=10.0
    )

    # Execute the request
    response = client.request(request)

    # Access request from response
    print(f"Method: {response.request.method}")
    print(f"Path: {response.request.path}")
    print(f"Headers sent: {response.request.headers}")
    print(f"Response data: {response.json['json']}")
    print()


class CachingAPIClient(APIClient):
    """Example of extending APIClient with response caching"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: Dict[str, Response] = {}

    def _execute(self, request: Request) -> Response:
        """Override to add caching for GET requests"""
        # Only cache GET requests
        if request.method == HTTPMethod.GET:
            cache_key = f"{request.path}?{request.params}"
            if cache_key in self._cache:
                print(f"  [Cache HIT] {cache_key}")
                return self._cache[cache_key]

            print(f"  [Cache MISS] {cache_key}")
            response = super()._execute(request)
            self._cache[cache_key] = response
            return response

        return super()._execute(request)

    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()


def example_caching_client():
    """Example of extending the client with caching"""
    print("=== Caching Client Extension ===")

    client = CachingAPIClient("https://jsonplaceholder.typicode.com")

    print("First request (cache miss):")
    response1 = client.get("/posts/1")
    print(f"Title: {response1.json['title']}")

    print("\nSecond request (cache hit):")
    response2 = client.get("/posts/1")
    print(f"Title: {response2.json['title']}")

    print("\nDifferent request (cache miss):")
    response3 = client.get("/posts/2")
    print(f"Title: {response3.json['title']}")

    print()


class MetricsAPIClient(APIClient):
    """Example of adding metrics collection"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0.0,
            "status_codes": {}
        }

    def _execute(self, request: Request) -> Response:
        """Track metrics for all requests"""
        self.metrics["total_requests"] += 1
        start_time = time.time()

        try:
            response = super()._execute(request)
            self.metrics["successful_requests"] += 1
            status = str(response.status_code)
            self.metrics["status_codes"][status] = \
                self.metrics["status_codes"].get(status, 0) + 1
            return response
        except Exception as e:
            self.metrics["failed_requests"] += 1
            raise
        finally:
            self.metrics["total_time"] += time.time() - start_time

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        metrics = self.metrics.copy()
        if metrics["total_requests"] > 0:
            metrics["avg_time"] = metrics["total_time"] / metrics["total_requests"]
        return metrics


def example_metrics_client():
    """Example of adding metrics collection"""
    print("=== Metrics Collection ===")

    client = MetricsAPIClient("https://jsonplaceholder.typicode.com")

    # Make several requests
    for i in range(1, 4):
        client.get(f"/posts/{i}")

    # Get metrics
    metrics = client.get_metrics()
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']}")
    print(f"Average time: {metrics.get('avg_time', 0):.3f}s")
    print(f"Status codes: {metrics['status_codes']}")
    print()


def example_combined_features():
    """Combine multiple features together"""
    print("=== Combined Features ===")

    # Create a fully configured client
    client = APIClient(
        base_url="https://httpbin.org",
        timeout=30,
        retry_config=RetryConfig(
            max_retries=3,
            backoff_factor=1.5
        ),
        rate_limiter=SimpleRateLimiter(
            requests_per_second=5,
            burst_size=10
        ),
        default_headers={
            "User-Agent": "AdvancedClient/1.0",
            "Accept": "application/json"
        }
    )

    print("Client configured with:")
    print("- Automatic retry (3 attempts)")
    print("- Rate limiting (5 req/sec)")
    print("- Default headers")
    print("- 30 second timeout")
    print()

    # Make a request that demonstrates all features
    response = client.get("/headers")
    headers = response.json["headers"]
    print(f"User-Agent header: {headers.get('User-Agent')}")
    print(f"Request successful: {response.ok}")
    print()


if __name__ == "__main__":
    print("REST API Client - Advanced Usage Examples\n")
    print("=" * 50)

    examples = [
        example_retry_configuration,
        example_rate_limiting,
        example_custom_rate_limiter,
        example_request_object,
        example_caching_client,
        example_metrics_client,
        example_combined_features,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Example failed: {e}\n")

    print("=" * 50)
    print("Advanced examples completed!")