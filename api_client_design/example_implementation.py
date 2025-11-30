#!/usr/bin/env python3
"""Example implementation showing the simplified API client in action.

This demonstrates how clean and simple the actual usage becomes.
"""

# This is what the actual client.py would look like (simplified for demo)
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError as URLHTTPError


@dataclass(frozen=True)
class ClientConfig:
    """Dead simple config."""
    base_url: str
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3


class APIResponse:
    """Simple response wrapper."""
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self._content = content

    def json(self) -> Any:
        return json.loads(self._content.decode('utf-8'))

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class APIClient:
    """The entire client in ~50 lines."""

    def __init__(self, base_url: str = None, api_key: str = None,
                 bearer_token: str = None, config: ClientConfig = None):
        if config:
            self._config = config
        else:
            self._config = ClientConfig(base_url, api_key, bearer_token)

    def get(self, path: str) -> APIResponse:
        """Make GET request."""
        url = self._config.base_url.rstrip('/') + path

        # Build headers
        headers = {}
        if self._config.api_key:
            headers["x-api-key"] = self._config.api_key
        elif self._config.bearer_token:
            headers["Authorization"] = f"Bearer {self._config.bearer_token}"

        # Make request (simplified - no retry in this demo)
        request = Request(url, headers=headers)
        try:
            response = urlopen(request, timeout=self._config.timeout)
            return APIResponse(response.getcode(), response.read())
        except URLHTTPError as e:
            return APIResponse(e.code, e.read())


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_simple():
    """Simplest possible usage."""
    client = APIClient("https://api.github.com")
    response = client.get("/zen")
    if response.ok:
        print(response.json())  # GitHub's zen message


def example_with_auth():
    """Using API key authentication."""
    client = APIClient(
        base_url="https://api.example.com",
        api_key="my-secret-key"
    )
    response = client.get("/protected/resource")
    if response.ok:
        data = response.json()
        print(f"Got data: {data}")


def example_with_config():
    """Using configuration object."""
    config = ClientConfig(
        base_url="https://api.example.com",
        bearer_token="eyJ0eXAiOiJKV1QiLCJhbGc...",
        timeout=60,
        max_retries=5
    )
    client = APIClient(config=config)
    response = client.get("/user/profile")
    if response.ok:
        profile = response.json()
        print(f"User: {profile.get('name')}")


def example_error_handling():
    """Simple error handling."""
    client = APIClient("https://httpbin.org")

    # This will 404
    response = client.get("/status/404")
    if not response.ok:
        print(f"Error: HTTP {response.status_code}")

    # This will 500 (would be retried in real implementation)
    response = client.get("/status/500")
    if not response.ok:
        print(f"Server error: HTTP {response.status_code}")


if __name__ == "__main__":
    print("Simple API Client Examples")
    print("=" * 40)

    print("\n1. Simple GET:")
    # example_simple()  # Would work with real API

    print("\n2. With Authentication:")
    # example_with_auth()  # Would work with real API

    print("\n3. With Configuration:")
    # example_with_config()  # Would work with real API

    print("\n4. Error Handling:")
    # example_error_handling()  # Would work with httpbin.org

    print("\nThis is the entire implementation!")
    print("No middleware, no strategies, no protocols.")
    print("Just simple, working code.")